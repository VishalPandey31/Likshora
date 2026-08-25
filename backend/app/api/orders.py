import secrets
from datetime import datetime, timezone
from decimal import Decimal
from flask import jsonify, request, g
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from app.api import api_v1
from app.auth.decorators import require_auth, require_admin
from app.models import Order, OrderItem, Address, CartItem, Product, Coupon, CouponUsage, User, Payment, Shipment
from app.services import TrackingService, ShiprocketService
from app.extensions import db
from app.errors import APIException

ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["processing", "cancelled"],
    "processing": ["shipped"],
    "shipped": ["delivered"],
    "delivered": [],
    "cancelled": [],
}


def generate_order_number() -> str:
    """Generate unique human-friendly order number (e.g. ORD-20260822-7A9B3C)."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_hex = secrets.token_hex(3).upper()
    return f"ORD-{date_str}-{random_hex}"


def serialize_order(order: Order, include_items: bool = True) -> dict:
    """Serialize Order model to JSON dictionary."""
    res = {
        "id": order.id,
        "order_number": order.order_number,
        "order_status": order.order_status,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "subtotal": float(order.subtotal),
        "discount_amount": float(order.discount_amount),
        "shipping_amount": float(order.shipping_amount),
        "total_amount": float(order.total_amount),
        "notes": order.notes,
        "shipping_address": {
            "full_name": order.shipping_full_name,
            "phone": order.shipping_phone,
            "address_line1": order.shipping_address_line1,
            "address_line2": order.shipping_address_line2,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "postal_code": order.shipping_postal_code,
            "country": order.shipping_country,
        },
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }

    active_shipment = next((s for s in order.shipments if s.status != "cancelled"), None) if hasattr(order, "shipments") and order.shipments else None
    res["shipment"] = {
        "id": active_shipment.id,
        "provider": active_shipment.provider,
        "status": active_shipment.status,
        "awb_code": active_shipment.awb_code,
        "courier_name": active_shipment.courier_name,
        "tracking_url": active_shipment.tracking_url,
    } if active_shipment else None

    if include_items:
        res["items"] = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "subtotal": float(item.subtotal),
            }
            for item in order.order_items
        ]
        res["item_count"] = sum(item.quantity for item in order.order_items)

    return res


def validate_and_calculate_coupon(coupon_code: str, user_id: int, subtotal_dec: Decimal):
    """Validate coupon code and return (coupon_instance, discount_decimal)."""
    if not coupon_code:
        return None, Decimal("0.00")

    coupon = Coupon.query.filter_by(code=coupon_code.strip().upper()).first()
    if not coupon:
        raise APIException("Invalid coupon code", status_code=400, code="INVALID_COUPON")

    if not coupon.is_active:
        raise APIException("Coupon is no longer active", status_code=400, code="COUPON_INACTIVE")

    now = datetime.now(timezone.utc)
    if coupon.starts_at:
        starts = coupon.starts_at.replace(tzinfo=timezone.utc) if coupon.starts_at.tzinfo is None else coupon.starts_at
        if now < starts:
            raise APIException("Coupon is not active yet", status_code=400, code="COUPON_NOT_STARTED")

    if coupon.expires_at:
        expires = coupon.expires_at.replace(tzinfo=timezone.utc) if coupon.expires_at.tzinfo is None else coupon.expires_at
        if now > expires:
            raise APIException("Coupon has expired", status_code=400, code="COUPON_EXPIRED")

    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise APIException("Coupon usage limit reached", status_code=400, code="COUPON_LIMIT_REACHED")

    user_usage_count = CouponUsage.query.filter_by(coupon_id=coupon.id, user_id=user_id).count()
    if user_usage_count >= coupon.per_user_limit:
        raise APIException("You have reached your usage limit for this coupon", status_code=400, code="PER_USER_LIMIT_REACHED")

    if subtotal_dec < Decimal(str(coupon.minimum_order_amount)):
        raise APIException(
            f"Minimum order amount for this coupon is {float(coupon.minimum_order_amount)}",
            status_code=400,
            code="MIN_ORDER_NOT_MET",
        )

    discount_val = Decimal(str(coupon.discount_value))
    if coupon.discount_type == "percentage":
        calculated_discount = subtotal_dec * (discount_val / Decimal("100"))
        if coupon.maximum_discount_amount is not None:
            max_disc = Decimal(str(coupon.maximum_discount_amount))
            calculated_discount = min(calculated_discount, max_disc)
    else:  # fixed
        calculated_discount = discount_val

    # Ensure discount does not exceed subtotal
    final_discount = min(calculated_discount, subtotal_dec)
    return coupon, final_discount.quantize(Decimal("0.01"))


@api_v1.route("/coupons/validate", methods=["POST"])
@require_auth
def validate_coupon_endpoint():
    """Preview coupon discount against current user's cart."""
    data = request.get_json() or {}
    coupon_code = data.get("coupon_code")
    if not coupon_code:
        raise APIException("coupon_code is required", status_code=400, code="VALIDATION_ERROR")

    cart_items = (
        CartItem.query.options(joinedload(CartItem.product))
        .filter(CartItem.user_id == g.current_user.id)
        .all()
    )
    if not cart_items:
        raise APIException("Cart is empty", status_code=400, code="EMPTY_CART")

    subtotal_dec = Decimal("0.00")
    for item in cart_items:
        if item.product and item.product.is_active:
            subtotal_dec += Decimal(str(item.product.price)) * Decimal(item.quantity)

    coupon, discount_dec = validate_and_calculate_coupon(coupon_code, g.current_user.id, subtotal_dec)

    return jsonify({
        "success": True,
        "data": {
            "coupon_code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "calculated_discount": float(discount_dec),
            "subtotal": float(subtotal_dec),
            "discounted_subtotal": float(subtotal_dec - discount_dec),
        }
    }), 200


@api_v1.route("/orders", methods=["POST"])
@require_auth
def create_order():
    """Atomic Checkout endpoint to create a new customer order."""
    data = request.get_json() or {}
    address_id = data.get("address_id")
    payment_method = (data.get("payment_method") or "").strip().lower()

    if not address_id and not data.get("shipping_address"):
        raise APIException("address_id or shipping_address is required", status_code=400, code="VALIDATION_ERROR")

    if payment_method not in ["cod", "online"]:
        raise APIException("payment_method must be 'cod' or 'online'", status_code=400, code="VALIDATION_ERROR")

    # 1. Load customer cart
    cart_items = (
        CartItem.query.options(joinedload(CartItem.product))
        .filter(CartItem.user_id == g.current_user.id)
        .all()
    )
    if not cart_items:
        raise APIException("Cannot checkout with an empty cart", status_code=400, code="EMPTY_CART")

    # 2. Validate or Create Delivery Address
    address = None
    if address_id and str(address_id).isdigit():
        address = Address.query.filter_by(id=int(address_id), user_id=g.current_user.id).first()
    
    if not address:
        shipping_address = data.get("shipping_address")
        if shipping_address and isinstance(shipping_address, dict):
            # Create a new address from inline payload
            address = Address(
                user_id=g.current_user.id,
                full_name=shipping_address.get("recipient") or shipping_address.get("name", "Customer"),
                phone=shipping_address.get("phone", ""),
                address_line1=shipping_address.get("street", ""),
                city=shipping_address.get("city", ""),
                state=shipping_address.get("state", ""),
                postal_code=shipping_address.get("pincode", ""),
                country=shipping_address.get("country", "India"),
                is_default=False
            )
            db.session.add(address)
            db.session.flush()

    if not address:
        raise APIException("Delivery address not found or invalid", status_code=400, code="INVALID_ADDRESS")

    # 3. Validate products and stock availability
    subtotal_dec = Decimal("0.00")
    validated_items = []

    for cart_item in cart_items:
        product = db.session.get(Product, cart_item.product_id)
        if not product or not product.is_active:
            raise APIException(
                f"Product '{cart_item.product.name if cart_item.product else cart_item.product_id}' is unavailable",
                status_code=400,
                code="PRODUCT_UNAVAILABLE",
            )

        if product.stock_quantity < cart_item.quantity:
            raise APIException(
                f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, Requested: {cart_item.quantity}",
                status_code=400,
                code="INSUFFICIENT_STOCK",
            )

        unit_price_dec = Decimal(str(product.price))
        item_subtotal_dec = unit_price_dec * Decimal(cart_item.quantity)
        subtotal_dec += item_subtotal_dec

        validated_items.append({
            "product": product,
            "quantity": cart_item.quantity,
            "unit_price": unit_price_dec,
            "subtotal": item_subtotal_dec,
        })

    # 4. Coupon validation and discount calculation
    coupon_code = data.get("coupon_code")
    coupon, discount_dec = validate_and_calculate_coupon(coupon_code, g.current_user.id, subtotal_dec)

    shipping_dec = Decimal("0.00")
    total_dec = subtotal_dec - discount_dec + shipping_dec

    # 5. Execute atomic database transaction
    try:
        order_num = generate_order_number()
        # Guarantee order_number uniqueness
        while Order.query.filter_by(order_number=order_num).first():
            order_num = generate_order_number()

        order = Order(
            user_id=g.current_user.id,
            address_id=address.id,
            order_number=order_num,
            subtotal=subtotal_dec,
            discount_amount=discount_dec,
            shipping_amount=shipping_dec,
            total_amount=total_dec,
            payment_method=payment_method,
            payment_status="pending",
            order_status="pending",
            coupon_id=coupon.id if coupon else None,
            notes=data.get("notes"),
            # Shipping Address Snapshot
            shipping_full_name=address.full_name,
            shipping_phone=address.phone,
            shipping_address_line1=address.address_line1,
            shipping_address_line2=address.address_line2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
        )
        db.session.add(order)
        db.session.flush()  # Assign order.id

        # Create OrderItem Snapshots and deduct stock
        for item in validated_items:
            prod = item["product"]
            order_item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                product_name=prod.name,
                sku=prod.sku,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"],
            )
            db.session.add(order_item)

            # Atomic stock deduction
            prod.stock_quantity = prod.stock_quantity - item["quantity"]

        # Record coupon usage if coupon applied
        if coupon:
            coupon_usage = CouponUsage(
                coupon_id=coupon.id,
                user_id=g.current_user.id,
                order_id=order.id,
                discount_amount=discount_dec,
            )
            db.session.add(coupon_usage)
            coupon.used_count += 1

        # Create payment record placeholder
        payment = Payment(
            order_id=order.id,
            payment_method=payment_method,
            provider="cod" if payment_method == "cod" else "razorpay",
            amount=total_dec,
            currency="INR",
            status="pending",
        )
        db.session.add(payment)

        # Clear customer cart
        CartItem.query.filter_by(user_id=g.current_user.id).delete()

        if payment_method == "cod":
            order.order_status = "confirmed"

        db.session.commit()

        response_data = serialize_order(order, include_items=True)
        if payment_method == "cod":
            response_data["order_status"] = "pending"

        # Automatic Shiprocket Order Creation & Fulfillment for COD orders
        if payment_method == "cod":
            try:
                ShiprocketService.fulfill_order_in_shiprocket(order)
            except Exception as e_sr:
                from flask import current_app
                current_app.logger.error(f"Automatic Shiprocket COD fulfillment failed for {order.order_number}: {str(e_sr)}")

        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "data": response_data
        }), 201

    except APIException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise e


@api_v1.route("/orders", methods=["GET"])
@require_auth
def get_user_orders():
    """Retrieve paginated order history for current user."""
    query = Order.query.options(selectinload(Order.order_items), selectinload(Order.shipments)).filter(Order.user_id == g.current_user.id)

    status_param = request.args.get("status", "").strip().lower()
    if status_param:
        query = query.filter(Order.order_status == status_param)

    query = query.order_by(Order.created_at.desc())

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        if page < 1 or per_page < 1:
            raise ValueError()
        per_page = min(per_page, 100)
    except ValueError:
        raise APIException("page and per_page must be positive integers", status_code=400, code="INVALID_PAGINATION")

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "data": [serialize_order(order, include_items=True) for order in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    }), 200


@api_v1.route("/orders/<order_identifier>", methods=["GET"])
@require_auth
def get_order_detail(order_identifier):
    """Retrieve single order details (IDOR protected)."""
    query = Order.query.options(selectinload(Order.order_items), selectinload(Order.shipments)).filter(Order.user_id == g.current_user.id)

    if order_identifier.isdigit():
        order = query.filter(Order.id == int(order_identifier)).first()
    else:
        order = query.filter(Order.order_number == order_identifier).first()

    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    return jsonify({
        "success": True,
        "data": serialize_order(order, include_items=True)
    }), 200


@api_v1.route("/orders/<order_identifier>/tracking", methods=["GET"])
@require_auth
def get_order_tracking(order_identifier):
    """Retrieve normalized order tracking timeline and shipment state (IDOR protected)."""
    query = Order.query.options(selectinload(Order.shipments).selectinload(Shipment.tracking_events))

    # Admin can view tracking for any order; Customer can view only own orders
    if g.current_user.role != "admin":
        query = query.filter(Order.user_id == g.current_user.id)

    if order_identifier.isdigit():
        order = query.filter(Order.id == int(order_identifier)).first()
    else:
        order = query.filter(Order.order_number == order_identifier).first()

    if not order:
        raise APIException("Order not found or access denied", status_code=404, code="ORDER_NOT_FOUND")

    active_shipment = next((s for s in order.shipments if s.status != "cancelled"), None) if order.shipments else None
    timeline_data = TrackingService.generate_order_timeline(order, active_shipment)

    return jsonify({
        "success": True,
        "data": timeline_data
    }), 200


@api_v1.route("/orders/<int:order_id>/cancel", methods=["POST"])
@require_auth
def cancel_order(order_id):
    """Cancel pending or confirmed order and restore product stock (IDOR protected)."""
    order = Order.query.options(selectinload(Order.order_items)).filter_by(id=order_id, user_id=g.current_user.id).first()
    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    if order.order_status in ["cancelled", "shipped", "delivered"]:
        raise APIException(
            f"Cannot cancel order in '{order.order_status}' status",
            status_code=400,
            code="CANNOT_CANCEL",
        )

    # Execute cancellation transaction
    try:
        # Idempotent stock restoration
        for item in order.order_items:
            if item.product_id:
                product = db.session.get(Product, item.product_id)
                if product:
                    product.stock_quantity += item.quantity

        order.order_status = "cancelled"

        active_shipment = next((s for s in order.shipments if s.status != "cancelled"), None) if hasattr(order, "shipments") and order.shipments else None
        if active_shipment:
            active_shipment.status = "cancelled"
            if active_shipment.shiprocket_order_id:
                try:
                    ShiprocketService.cancel_order([active_shipment.shiprocket_order_id])
                except Exception as e_sr:
                    from flask import current_app
                    current_app.logger.warning(f"Shiprocket cancel API warning for order {order.id}: {str(e_sr)}")

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Order cancelled successfully",
            "data": serialize_order(order, include_items=True)
        }), 200

    except APIException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise e


@api_v1.route("/admin/orders/<int:order_id>/status", methods=["PATCH"])
@require_admin
def update_admin_order_status(order_id):
    """Update order status using state machine transitions (Admin-only)."""
    order = Order.query.options(selectinload(Order.order_items), selectinload(Order.payments)).filter_by(id=order_id).first()
    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    data = request.get_json() or {}
    new_status = (data.get("status") or "").strip().lower()

    if not new_status:
        raise APIException("status is required", status_code=400, code="VALIDATION_ERROR")

    current_status = order.order_status
    if new_status == current_status:
        return jsonify({
            "success": True,
            "message": f"Order status is already '{current_status}'",
            "data": serialize_order(order, include_items=True)
        }), 200

    allowed_next = ALLOWED_TRANSITIONS.get(current_status, [])

    if new_status not in allowed_next:
        raise APIException(
            f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed transitions: {allowed_next}",
            status_code=400,
            code="INVALID_STATUS_TRANSITION",
        )

    try:
        # If admin cancels a pending/confirmed order, restore stock
        if new_status == "cancelled" and current_status in ["pending", "confirmed"]:
            for item in order.order_items:
                if item.product_id:
                    product = db.session.get(Product, item.product_id)
                    if product:
                        product.stock_quantity += item.quantity

        order.order_status = new_status

        # Update payment_status to 'paid' if delivered and method is COD
        if new_status == "delivered" and order.payment_method == "cod":
            order.payment_status = "paid"
            for payment in order.payments:
                payment.status = "captured"
                payment.paid_at = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Order status updated from '{current_status}' to '{new_status}'",
            "data": serialize_order(order, include_items=True)
        }), 200

    except APIException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise e


@api_v1.route("/admin/orders/<int:order_id>/cod-payment", methods=["PATCH"])
@require_admin
def confirm_admin_cod_payment(order_id):
    """Confirm cash collection on delivery for a COD order (Admin-only)."""
    order = Order.query.options(selectinload(Order.payments)).filter_by(id=order_id).first()
    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    if order.payment_method != "cod":
        raise APIException("This endpoint is only for Cash on Delivery (COD) orders", status_code=400, code="INVALID_PAYMENT_METHOD")

    if order.order_status in ["cancelled"]:
        raise APIException(f"Cannot confirm payment for order in '{order.order_status}' status", status_code=400, code="INVALID_ORDER_STATE")

    if order.payment_status == "paid":
        return jsonify({
            "success": True,
            "message": "COD payment has already been marked as paid",
            "data": serialize_order(order, include_items=True)
        }), 200

    try:
        order.payment_status = "paid"
        for payment in order.payments:
            if payment.payment_method == "cod":
                payment.status = "captured"
                payment.paid_at = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "COD payment marked as collected and paid",
            "data": serialize_order(order, include_items=True)
        }), 200

    except APIException:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise e
