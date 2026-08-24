from decimal import Decimal
from flask import jsonify, request, g
from sqlalchemy.orm import joinedload, selectinload
from app.api import api_v1
from app.auth.decorators import require_auth
from app.models import CartItem, Product
from app.extensions import db
from app.errors import APIException


def serialize_cart_item(cart_item: CartItem) -> dict:
    """Serialize a single cart item with product information."""
    product = cart_item.product
    if not product:
        return {
            "id": cart_item.id,
            "product_id": cart_item.product_id,
            "quantity": cart_item.quantity,
            "available": False,
            "reason": "PRODUCT_NOT_FOUND",
            "in_stock": False,
            "subtotal": 0.0,
        }

    images = sorted(product.images, key=lambda img: (not img.is_primary, img.display_order)) if product.images else []
    primary_image = images[0].image_url if images else None

    is_active = product.is_active
    is_in_stock = is_active and product.stock_quantity >= cart_item.quantity and product.stock_quantity > 0
    price_dec = Decimal(str(product.price))
    item_subtotal_dec = price_dec * Decimal(cart_item.quantity)

    res = {
        "id": cart_item.id,
        "product_id": product.id,
        "name": product.name,
        "slug": product.slug,
        "price": float(price_dec),
        "compare_at_price": float(product.compare_at_price) if product.compare_at_price is not None else None,
        "quantity": cart_item.quantity,
        "subtotal": float(item_subtotal_dec),
        "image_url": primary_image,
        "stock_quantity": product.stock_quantity,
        "in_stock": is_in_stock,
        "available": is_active,
    }

    if not is_active:
        res["reason"] = "PRODUCT_INACTIVE"

    return res


@api_v1.route("/cart", methods=["GET"])
@require_auth
def get_cart():
    """Retrieve current authenticated user's cart."""
    items = (
        CartItem.query.options(
            joinedload(CartItem.product).selectinload(Product.images)
        )
        .filter(CartItem.user_id == g.current_user.id)
        .order_by(CartItem.created_at.asc())
        .all()
    )

    serialized_items = [serialize_cart_item(item) for item in items]

    total_subtotal_dec = Decimal("0.00")
    item_count = 0

    for item in items:
        if item.product and item.product.is_active:
            price_dec = Decimal(str(item.product.price))
            total_subtotal_dec += price_dec * Decimal(item.quantity)
            item_count += item.quantity

    subtotal_val = float(total_subtotal_dec)

    return jsonify({
        "success": True,
        "data": {
            "items": serialized_items,
            "subtotal": subtotal_val,
            "total": subtotal_val,
            "item_count": item_count,
            "total_unique_items": len(items),
        }
    }), 200


@api_v1.route("/cart", methods=["POST"])
@require_auth
def add_to_cart():
    """Add product to cart or increment quantity."""
    data = request.get_json() or {}
    product_id = data.get("product_id")

    if not product_id:
        raise APIException("product_id is required", status_code=400, code="VALIDATION_ERROR")

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        raise APIException("product_id must be an integer", status_code=400, code="VALIDATION_ERROR")

    try:
        quantity = int(data.get("quantity", 1))
        if quantity <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise APIException("quantity must be a positive integer", status_code=400, code="INVALID_QUANTITY")

    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    if not product.is_active:
        raise APIException("Product is inactive and cannot be added to cart", status_code=400, code="PRODUCT_INACTIVE")

    if product.stock_quantity <= 0:
        raise APIException("Product is out of stock", status_code=400, code="INSUFFICIENT_STOCK")

    # Check if item is already in user's cart
    existing_item = CartItem.query.filter_by(user_id=g.current_user.id, product_id=product.id).first()

    if existing_item:
        new_qty = existing_item.quantity + quantity
        if new_qty > product.stock_quantity:
            raise APIException(
                f"Cannot add {quantity} item(s). Requested total ({new_qty}) exceeds available stock ({product.stock_quantity})",
                status_code=400,
                code="INSUFFICIENT_STOCK",
            )
        existing_item.quantity = new_qty
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Cart item quantity updated",
            "data": serialize_cart_item(existing_item)
        }), 200
    else:
        if quantity > product.stock_quantity:
            raise APIException(
                f"Requested quantity ({quantity}) exceeds available stock ({product.stock_quantity})",
                status_code=400,
                code="INSUFFICIENT_STOCK",
            )
        cart_item = CartItem(user_id=g.current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Product added to cart",
            "data": serialize_cart_item(cart_item)
        }), 201


@api_v1.route("/cart/<int:cart_item_id>", methods=["PUT", "PATCH"])
@require_auth
def update_cart_item(cart_item_id):
    """Update cart item quantity (IDOR protected)."""
    cart_item = CartItem.query.filter_by(id=cart_item_id, user_id=g.current_user.id).first()
    if not cart_item:
        raise APIException("Cart item not found", status_code=404, code="CART_ITEM_NOT_FOUND")

    data = request.get_json() or {}
    if "quantity" not in data:
        raise APIException("quantity is required", status_code=400, code="VALIDATION_ERROR")

    try:
        new_quantity = int(data["quantity"])
        if new_quantity <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise APIException("quantity must be a positive integer", status_code=400, code="INVALID_QUANTITY")

    product = cart_item.product
    if not product or not product.is_active:
        raise APIException("Product is unavailable", status_code=400, code="PRODUCT_UNAVAILABLE")

    if new_quantity > product.stock_quantity:
        raise APIException(
            f"Requested quantity ({new_quantity}) exceeds available stock ({product.stock_quantity})",
            status_code=400,
            code="INSUFFICIENT_STOCK",
        )

    cart_item.quantity = new_quantity
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Cart quantity updated successfully",
        "data": serialize_cart_item(cart_item)
    }), 200


@api_v1.route("/cart/<int:cart_item_id>", methods=["DELETE"])
@require_auth
def delete_cart_item(cart_item_id):
    """Remove single item from cart (IDOR protected)."""
    cart_item = CartItem.query.filter_by(id=cart_item_id, user_id=g.current_user.id).first()
    if not cart_item:
        raise APIException("Cart item not found", status_code=404, code="CART_ITEM_NOT_FOUND")

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Item removed from cart"
    }), 200


@api_v1.route("/cart", methods=["DELETE"])
@require_auth
def clear_cart():
    """Clear all items from current user's cart."""
    CartItem.query.filter_by(user_id=g.current_user.id).delete()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Cart cleared successfully",
        "data": {
            "items": [],
            "subtotal": 0.0,
            "total": 0.0,
            "item_count": 0,
            "total_unique_items": 0,
        }
    }), 200
