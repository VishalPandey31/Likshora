from flask import jsonify, request, g
from app.api import api_v1
from app.auth.decorators import require_auth
from app.models import Address
from app.extensions import db
from app.errors import APIException


def serialize_address(address: Address) -> dict:
    """Serialize address model to JSON dictionary."""
    return {
        "id": address.id,
        "full_name": address.full_name,
        "phone": address.phone,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "created_at": address.created_at.isoformat() if address.created_at else None,
        "updated_at": address.updated_at.isoformat() if address.updated_at else None,
    }


def validate_address_input(data: dict, is_update: bool = False):
    """Validate address input fields."""
    if not is_update:
        required_fields = ["full_name", "phone", "address_line1", "city", "state", "postal_code", "country"]
        missing = [field for field in required_fields if not (data.get(field) or "").strip()]
        if missing:
            raise APIException(
                f"Missing required address fields: {', '.join(missing)}",
                status_code=400,
                code="VALIDATION_ERROR",
            )

    if "full_name" in data and not (data["full_name"] or "").strip():
        raise APIException("full_name cannot be empty", status_code=400, code="VALIDATION_ERROR")

    if "phone" in data and not (data["phone"] or "").strip():
        raise APIException("phone cannot be empty", status_code=400, code="VALIDATION_ERROR")

    if "address_line1" in data and not (data["address_line1"] or "").strip():
        raise APIException("address_line1 cannot be empty", status_code=400, code="VALIDATION_ERROR")

    if "city" in data and not (data["city"] or "").strip():
        raise APIException("city cannot be empty", status_code=400, code="VALIDATION_ERROR")

    if "state" in data and not (data["state"] or "").strip():
        raise APIException("state cannot be empty", status_code=400, code="VALIDATION_ERROR")

    if "postal_code" in data and not (data["postal_code"] or "").strip():
        raise APIException("postal_code cannot be empty", status_code=400, code="VALIDATION_ERROR")

    if "country" in data and not (data["country"] or "").strip():
        raise APIException("country cannot be empty", status_code=400, code="VALIDATION_ERROR")


@api_v1.route("/addresses", methods=["GET"])
@require_auth
def get_addresses():
    """Retrieve all addresses for the authenticated user."""
    addresses = (
        Address.query.filter_by(user_id=g.current_user.id)
        .order_by(Address.is_default.desc(), Address.updated_at.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "data": [serialize_address(addr) for addr in addresses],
        "count": len(addresses),
    }), 200


@api_v1.route("/addresses/<int:address_id>", methods=["GET"])
@require_auth
def get_address_detail(address_id):
    """Retrieve a single address (IDOR protected)."""
    address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
    if not address:
        raise APIException("Address not found", status_code=404, code="ADDRESS_NOT_FOUND")

    return jsonify({
        "success": True,
        "data": serialize_address(address)
    }), 200


@api_v1.route("/addresses", methods=["POST"])
@require_auth
def create_address():
    """Create new address for authenticated user."""
    data = request.get_json() or {}
    validate_address_input(data, is_update=False)

    existing_count = Address.query.filter_by(user_id=g.current_user.id).count()

    # Automatically set as default if it's the user's first address or requested explicitly
    is_default = bool(data.get("is_default", False)) or (existing_count == 0)

    if is_default:
        # Transactionally unset existing defaults for user
        Address.query.filter_by(user_id=g.current_user.id).update({"is_default": False})

    address = Address(
        user_id=g.current_user.id,
        full_name=data["full_name"].strip(),
        phone=data["phone"].strip(),
        address_line1=data["address_line1"].strip(),
        address_line2=(data.get("address_line2") or "").strip() or None,
        city=data["city"].strip(),
        state=data["state"].strip(),
        postal_code=data["postal_code"].strip(),
        country=data.get("country", "India").strip(),
        is_default=is_default,
    )
    db.session.add(address)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Address created successfully",
        "data": serialize_address(address)
    }), 201


@api_v1.route("/addresses/<int:address_id>", methods=["PUT", "PATCH"])
@require_auth
def update_address(address_id):
    """Update existing address (IDOR protected)."""
    address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
    if not address:
        raise APIException("Address not found", status_code=404, code="ADDRESS_NOT_FOUND")

    data = request.get_json() or {}
    validate_address_input(data, is_update=True)

    if "is_default" in data and bool(data["is_default"]):
        # Set all other addresses for user to false in same transaction
        Address.query.filter_by(user_id=g.current_user.id).update({"is_default": False})
        address.is_default = True

    if "full_name" in data:
        address.full_name = data["full_name"].strip()
    if "phone" in data:
        address.phone = data["phone"].strip()
    if "address_line1" in data:
        address.address_line1 = data["address_line1"].strip()
    if "address_line2" in data:
        address.address_line2 = (data["address_line2"] or "").strip() or None
    if "city" in data:
        address.city = data["city"].strip()
    if "state" in data:
        address.state = data["state"].strip()
    if "postal_code" in data:
        address.postal_code = data["postal_code"].strip()
    if "country" in data:
        address.country = data["country"].strip()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Address updated successfully",
        "data": serialize_address(address)
    }), 200


@api_v1.route("/addresses/<int:address_id>/default", methods=["PATCH", "POST"])
@require_auth
def set_default_address(address_id):
    """Set address as default in an atomic transaction (IDOR protected)."""
    address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
    if not address:
        raise APIException("Address not found", status_code=404, code="ADDRESS_NOT_FOUND")

    # Transactionally clear other default flags and set target address as default
    Address.query.filter_by(user_id=g.current_user.id).update({"is_default": False})
    address.is_default = True
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Default address updated successfully",
        "data": serialize_address(address)
    }), 200


@api_v1.route("/addresses/<int:address_id>", methods=["DELETE"])
@require_auth
def delete_address(address_id):
    """Delete address (IDOR protected)."""
    address = Address.query.filter_by(id=address_id, user_id=g.current_user.id).first()
    if not address:
        raise APIException("Address not found", status_code=404, code="ADDRESS_NOT_FOUND")

    was_default = address.is_default
    db.session.delete(address)
    db.session.flush()

    # If deleted address was default, promote the remaining most recently updated address to default
    if was_default:
        remaining_address = (
            Address.query.filter_by(user_id=g.current_user.id)
            .order_by(Address.updated_at.desc())
            .first()
        )
        if remaining_address:
            remaining_address.is_default = True

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Address deleted successfully"
    }), 200
