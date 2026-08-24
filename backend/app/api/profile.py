from flask import jsonify, request, g
from app.api import api_v1
from app.auth.decorators import require_auth
from app.auth.utils import validate_phone_format
from app.extensions import db
from app.errors import APIException


@api_v1.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    """Retrieve current user profile."""
    user = g.current_user
    return jsonify({
        "success": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    }), 200


@api_v1.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    """Update current user profile (allowed fields: name, phone)."""
    user = g.current_user
    data = request.get_json() or {}

    # Reject unauthorized attempts to modify non-profile or security-critical fields
    allowed_fields = {"name", "phone"}
    attempted_restricted = set(data.keys()) - allowed_fields
    if attempted_restricted:
        raise APIException(
            f"Modifying field(s) {', '.join(sorted(attempted_restricted))} is not allowed via profile update",
            status_code=403,
            code="FORBIDDEN_FIELD_UPDATE",
        )

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            raise APIException("Name cannot be empty", status_code=400, code="VALIDATION_ERROR")
        user.name = name

    if "phone" in data:
        user.phone = validate_phone_format(data["phone"])

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Profile updated successfully",
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    }), 200
