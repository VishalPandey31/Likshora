from decimal import Decimal
from flask import jsonify, request, g
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload, selectinload
from app.api import api_v1
from app.auth.decorators import require_admin
from app.models import (
    Order, OrderItem, Product, Category, User, Address, Payment, Shipment, CouponUsage,
    CartItem, WishlistItem, SearchHistory, Review, CustomerLoginLog
)
from app.extensions import db
from app.errors import APIException
from app.api.orders import serialize_order
from app.api.products import serialize_product

LOW_STOCK_THRESHOLD = 5


def serialize_admin_customer(user: User, total_spent: float = 0.0, order_count: int = 0) -> dict:
    """Serialize customer profile for admin view without sensitive authentication credentials."""
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "order_count": order_count,
        "total_spent": total_spent,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@api_v1.route("/admin/dashboard", methods=["GET"])
@require_admin
def get_admin_dashboard():
    """Retrieve summary metrics for Admin Dashboard."""
    # 1. Total Orders count
    total_orders = db.session.query(func.count(Order.id)).scalar() or 0

    # 2. Total Revenue (sum of grand_total for paid non-cancelled valid orders)
    revenue_sum = (
        db.session.query(func.coalesce(func.sum(Order.grand_total), 0))
        .join(Payment, Order.id == Payment.order_id)
        .filter(
            Order.status.in_(["confirmed", "processing", "shipped", "delivered"]),
            Payment.status == "captured"
        )
        .scalar()
    )
    total_revenue = float(revenue_sum or 0.0)

    # 3. Total Customers count (role = 'customer')
    total_customers = User.query.filter_by(role="customer").count()

    # 4. Total Active Products count
    total_products = Product.query.filter_by(is_active=True).count()

    # 5. Low Stock Products count (0 < stock <= LOW_STOCK_THRESHOLD)
    low_stock_products = Product.query.filter(
        Product.is_active == True,  # noqa: E712
        Product.stock_quantity <= LOW_STOCK_THRESHOLD,
        Product.stock_quantity > 0,
    ).count()

    # 6. Pending Orders count
    pending_orders = Order.query.filter_by(status="pending").count()

    return jsonify({
        "success": True,
        "data": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "total_products": total_products,
            "low_stock_products": low_stock_products,
            "pending_orders": pending_orders,
        }
    }), 200


@api_v1.route("/admin/products/low-stock", methods=["GET"])
@require_admin
def get_low_stock_products():
    """Retrieve list of products with stock at or below low-stock threshold."""
    products = (
        Product.query.options(joinedload(Product.category), selectinload(Product.images))
        .filter(
            Product.is_active == True,  # noqa: E712
            Product.stock_quantity <= LOW_STOCK_THRESHOLD,
            Product.stock_quantity > 0,
        )
        .order_by(Product.stock_quantity.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "data": [serialize_product(p, include_details=True) for p in products],
        "count": len(products),
        "threshold": LOW_STOCK_THRESHOLD,
    }), 200


@api_v1.route("/admin/orders", methods=["GET"])
@require_admin
def get_admin_orders():
    """Retrieve paginated orders for Admin Management with multi-field search and filters."""
    query = Order.query.options(joinedload(Order.user), selectinload(Order.order_items))

    # Filter by order_status
    status_param = request.args.get("status", "").strip().lower()
    if status_param:
        query = query.filter(Order.status == status_param)

    # Filter by payment_status
    payment_status_param = request.args.get("payment_status", "").strip().lower()
    if payment_status_param:
        query = query.join(Payment, Order.id == Payment.order_id, isouter=True).filter(Payment.status == payment_status_param)

    # Filter by customer_id
    customer_id = request.args.get("customer_id")
    if customer_id and customer_id.isdigit():
        query = query.filter(Order.user_id == int(customer_id))

    # Search filter (order_number, customer name, customer email)
    search_term = request.args.get("search", "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        query = query.join(User, Order.user_id == User.id, isouter=True).filter(
            or_(
                Order.order_number.ilike(pattern),
                Order.shipping_address_snapshot.ilike(pattern),
                User.name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

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

    orders_data = []
    for order in pagination.items:
        o_dict = serialize_order(order, include_items=True)
        if order.user:
            o_dict["customer"] = {
                "id": order.user.id,
                "name": order.user.name,
                "email": order.user.email,
                "phone": order.user.phone,
            }
        orders_data.append(o_dict)

    return jsonify({
        "success": True,
        "data": orders_data,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    }), 200


@api_v1.route("/admin/orders/<int:order_id>", methods=["GET"])
@require_admin
def get_admin_order_detail(order_id):
    """Retrieve comprehensive order details for admin view."""
    order = (
        Order.query.options(
            joinedload(Order.user),
            selectinload(Order.order_items),
            selectinload(Order.payments),
            selectinload(Order.shipments),
        )
        .filter_by(id=order_id)
        .first()
    )
    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    res = serialize_order(order, include_items=True)

    if order.user:
        res["customer"] = {
            "id": order.user.id,
            "name": order.user.name,
            "email": order.user.email,
            "phone": order.user.phone,
            "created_at": order.user.created_at.isoformat() if order.user.created_at else None,
        }

    res["payments"] = [
        {
            "id": p.id,
            "payment_method": p.payment_method,
            "provider": p.provider,
            "provider_payment_id": p.provider_payment_id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        }
        for p in order.payments
    ]

    res["shipments"] = [
        {
            "id": s.id,
            "courier_name": s.courier_name,
            "awb_code": s.awb_code,
            "status": s.status,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None,
        }
        for s in order.shipments
    ]

    return jsonify({
        "success": True,
        "data": res
    }), 200


@api_v1.route("/admin/customers", methods=["GET"])
@require_admin
def get_admin_customers():
    """Retrieve paginated list of customer accounts with aggregated metrics."""
    query = User.query.filter_by(role="customer")

    search_term = request.args.get("search", "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                User.name.ilike(pattern),
                User.email.ilike(pattern),
                User.phone.ilike(pattern),
            )
        )

    query = query.order_by(User.created_at.desc())

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        if page < 1 or per_page < 1:
            raise ValueError()
        per_page = min(per_page, 100)
    except ValueError:
        raise APIException("page and per_page must be positive integers", status_code=400, code="INVALID_PAGINATION")

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Perform group aggregation for order count and total spending
    customer_ids = [u.id for u in pagination.items]
    order_stats = {}
    if customer_ids:
        stats = (
            db.session.query(
                Order.user_id,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.grand_total), 0).label("total_spent"),
            )
            .filter(
                Order.user_id.in_(customer_ids),
                Order.status.in_(["confirmed", "processing", "shipped", "delivered"]),
            )
            .group_by(Order.user_id)
            .all()
        )
        order_stats = {row.user_id: {"order_count": row.order_count, "total_spent": float(row.total_spent)} for row in stats}

    customers_data = []
    for user in pagination.items:
        st = order_stats.get(user.id, {"order_count": 0, "total_spent": 0.0})
        customers_data.append(serialize_admin_customer(user, total_spent=st["total_spent"], order_count=st["order_count"]))

    return jsonify({
        "success": True,
        "data": customers_data,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    }), 200


@api_v1.route("/admin/customers/<customer_id>", methods=["GET"])
@require_admin
def get_admin_customer_detail(customer_id):
    """Retrieve detailed customer profile, saved addresses, and spending statistics."""
    user = User.query.filter_by(id=customer_id, role="customer").first()
    if not user:
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    stats = (
        db.session.query(
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.grand_total), 0).label("total_spent"),
        )
        .filter(
            Order.user_id == user.id,
            Order.status.in_(["confirmed", "processing", "shipped", "delivered"]),
        )
        .first()
    )

    order_count = stats.order_count if stats else 0
    total_spent = float(stats.total_spent) if stats else 0.0

    recent_orders = (
        Order.query.filter_by(user_id=user.id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    addresses = Address.query.filter_by(user_id=user.id).order_by(Address.is_default.desc()).all()

    profile_data = serialize_admin_customer(user, total_spent=total_spent, order_count=order_count)
    profile_data["addresses"] = [
        {
            "id": a.id,
            "full_name": a.full_name,
            "phone": a.phone,
            "address_line1": a.address_line1,
            "city": a.city,
            "state": a.state,
            "postal_code": a.postal_code,
            "country": a.country,
            "is_default": a.is_default,
        }
        for a in addresses
    ]
    profile_data["recent_orders"] = [serialize_order(o, include_items=False) for o in recent_orders]

    return jsonify({
        "success": True,
        "data": profile_data
    }), 200


@api_v1.route("/admin/customers/<customer_id>/orders", methods=["GET"])
@require_admin
def get_admin_customer_orders(customer_id):
    """Retrieve order history for a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    query = Order.query.options(selectinload(Order.order_items)).filter_by(user_id=customer_id)

    status_param = request.args.get("status", "").strip().lower()
    if status_param:
        query = query.filter(Order.status == status_param)

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


@api_v1.route("/admin/customers/<customer_id>/payments", methods=["GET"])
@require_admin
def get_admin_customer_payments(customer_id):
    """Retrieve payment transaction history for a specific customer across all their orders."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    payments = (
        Payment.query.join(Order, Payment.order_id == Order.id)
        .filter(Order.user_id == customer_id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    data = [
        {
            "id": p.id,
            "order_id": p.order_id,
            "order_number": p.order.order_number if p.order else None,
            "payment_method": p.payment_method,
            "provider": p.provider,
            "provider_payment_id": p.provider_payment_id,
            "provider_order_id": p.provider_order_id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "failure_reason": p.failure_reason,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payments
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/customers/<customer_id>/addresses", methods=["GET"])
@require_admin
def get_admin_customer_addresses(customer_id):
    """Retrieve saved delivery addresses for a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    addresses = Address.query.filter_by(user_id=customer_id).order_by(Address.is_default.desc()).all()

    data = [
        {
            "id": a.id,
            "full_name": a.full_name,
            "phone": a.phone,
            "address_line1": a.address_line1,
            "address_line2": a.address_line2,
            "city": a.city,
            "state": a.state,
            "postal_code": a.postal_code,
            "country": a.country,
            "is_default": a.is_default,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in addresses
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/customers/<customer_id>/cart", methods=["GET"])
@require_admin
def get_admin_customer_cart(customer_id):
    """Retrieve active cart contents for a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    items = (
        CartItem.query.options(joinedload(CartItem.product).selectinload(Product.images))
        .filter_by(user_id=customer_id)
        .order_by(CartItem.created_at.asc())
        .all()
    )

    data = []
    total_val = 0.0
    for item in items:
        p = item.product
        item_subtotal = float(p.price) * item.quantity if p else 0.0
        total_val += item_subtotal
        primary_image = p.images[0].image_url if p and p.images else None
        data.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": p.name if p else "Unknown Product",
            "sku": p.sku if p else None,
            "price": float(p.price) if p else 0.0,
            "quantity": item.quantity,
            "subtotal": item_subtotal,
            "image_url": primary_image,
            "in_stock": p.stock_quantity >= item.quantity if p else False,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    return jsonify({
        "success": True,
        "data": {
            "items": data,
            "total_items": sum(i["quantity"] for i in data),
            "cart_total": total_val,
        }
    }), 200


@api_v1.route("/admin/customers/<customer_id>/wishlist", methods=["GET"])
@require_admin
def get_admin_customer_wishlist(customer_id):
    """Retrieve saved wishlist items for a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    items = (
        WishlistItem.query.options(joinedload(WishlistItem.product).selectinload(Product.images))
        .filter_by(user_id=customer_id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )

    data = []
    for item in items:
        p = item.product
        primary_image = p.images[0].image_url if p and p.images else None
        data.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": p.name if p else "Unknown Product",
            "sku": p.sku if p else None,
            "price": float(p.price) if p else 0.0,
            "in_stock": p.stock_quantity > 0 if p else False,
            "image_url": primary_image,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/customers/<customer_id>/search-history", methods=["GET"])
@require_admin
def get_admin_customer_search_history(customer_id):
    """Retrieve search activity history for a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    searches = (
        SearchHistory.query.filter_by(user_id=customer_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(100)
        .all()
    )

    data = [
        {
            "id": s.id,
            "query": s.search_query,
            "results_count": s.results_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in searches
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/customers/<customer_id>/reviews", methods=["GET"])
@require_admin
def get_admin_customer_reviews(customer_id):
    """Retrieve product reviews submitted by a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    reviews = (
        Review.query.options(joinedload(Review.product))
        .filter_by(user_id=customer_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    data = [
        {
            "id": r.id,
            "product_id": r.product_id,
            "product_name": r.product.name if r.product else "Unknown Product",
            "rating": r.rating,
            "comment": r.comment,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in reviews
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/customers/<customer_id>/login-logs", methods=["GET"])
@require_admin
def get_admin_customer_login_logs(customer_id):
    """Retrieve login activity audit log for a specific customer."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    logs = (
        CustomerLoginLog.query.filter_by(user_id=customer_id)
        .order_by(CustomerLoginLog.timestamp.desc())
        .limit(100)
        .all()
    )

    data = [
        {
            "id": l.id,
            "login_at": l.login_at.isoformat() if l.login_at else None,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "success": l.success,
            "failure_reason": l.failure_reason,
        }
        for l in logs
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/customers/<customer_id>/status", methods=["PATCH"])
@require_admin
def update_admin_customer_status(customer_id):
    """Toggle or update customer account active status (block/unblock)."""
    user = db.session.get(User, customer_id)
    if not user or user.role != "customer":
        raise APIException("Customer account not found", status_code=404, code="CUSTOMER_NOT_FOUND")

    data = request.get_json() or {}
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    elif "status" in data:
        status_str = str(data["status"]).strip().lower()
        user.is_active = status_str in ["active", "true", "enabled"]
    else:
        user.is_active = not user.is_active

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Customer account status updated to {'Active' if user.is_active else 'Blocked'}",
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "status": "Active" if user.is_active else "Blocked",
        }
    }), 200


@api_v1.route("/admin/reviews", methods=["GET"])
@require_admin
def get_admin_reviews():
    """Retrieve product reviews for admin moderation with status filter."""
    query = Review.query.options(joinedload(Review.user), joinedload(Review.product))

    status_param = request.args.get("status", "").strip().lower()
    if status_param and status_param != "all":
        query = query.filter(Review.status == status_param)

    query = query.order_by(Review.created_at.desc())

    reviews = query.all()

    data = [
        {
            "id": r.id,
            "product_id": r.product_id,
            "product_name": r.product.name if r.product else "Unknown Product",
            "product_image": r.product.images[0].image_url if r.product and r.product.images else None,
            "customer_id": r.user_id,
            "customer_name": r.user.name if r.user else "Unknown Customer",
            "customer_email": r.user.email if r.user else "",
            "rating": r.rating,
            "comment": r.comment,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reviews
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/admin/reviews/<int:review_id>/status", methods=["PATCH"])
@require_admin
def update_admin_review_status(review_id):
    """Update moderation status of a customer review (approved/rejected/pending)."""
    review = db.session.get(Review, review_id)
    if not review:
        raise APIException("Review not found", status_code=404, code="REVIEW_NOT_FOUND")

    data = request.get_json() or {}
    status_val = (data.get("status") or "").strip().lower()
    if status_val not in ["approved", "rejected", "pending"]:
        raise APIException("Invalid status. Expected 'approved', 'rejected', or 'pending'", status_code=400, code="INVALID_STATUS")

    review.status = status_val
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Review status updated to {status_val}",
        "data": {
            "id": review.id,
            "status": review.status,
        }
    }), 200


@api_v1.route("/admin/reviews/<int:review_id>", methods=["DELETE"])
@require_admin
def delete_admin_review(review_id):
    """Delete a customer review (Admin-only)."""
    review = db.session.get(Review, review_id)
    if not review:
        raise APIException("Review not found", status_code=404, code="REVIEW_NOT_FOUND")

    db.session.delete(review)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Review deleted successfully"
    }), 200

