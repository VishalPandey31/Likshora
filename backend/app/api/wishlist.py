from flask import jsonify, request, g
from sqlalchemy.orm import joinedload, selectinload
from app.api import api_v1
from app.auth.decorators import require_auth
from app.models import WishlistItem, CartItem, Product
from app.extensions import db
from app.errors import APIException
from app.api.cart import serialize_cart_item


def serialize_wishlist_item(item: WishlistItem) -> dict:
    """Serialize a single wishlist item with product details."""
    product = item.product
    if not product:
        return {
            "id": item.id,
            "product_id": item.product_id,
            "available": False,
            "reason": "PRODUCT_NOT_FOUND",
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }

    images = sorted(product.images, key=lambda img: (not img.is_primary, img.display_order)) if product.images else []
    primary_image = images[0].image_url if images else None

    is_active = product.is_active
    is_in_stock = is_active and product.stock_quantity > 0

    res = {
        "id": item.id,
        "product_id": product.id,
        "name": product.name,
        "slug": product.slug,
        "price": float(product.price),
        "compare_at_price": float(product.compare_at_price) if product.compare_at_price is not None else None,
        "image_url": primary_image,
        "stock_quantity": product.stock_quantity,
        "in_stock": is_in_stock,
        "available": is_active,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

    if not is_active:
        res["reason"] = "PRODUCT_INACTIVE"

    return res


@api_v1.route("/wishlist", methods=["GET"])
@require_auth
def get_wishlist():
    """Retrieve current authenticated user's wishlist items."""
    items = (
        WishlistItem.query.options(
            joinedload(WishlistItem.product).selectinload(Product.images)
        )
        .filter(WishlistItem.user_id == g.current_user.id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "data": [serialize_wishlist_item(item) for item in items],
        "item_count": len(items),
    }), 200


@api_v1.route("/wishlist/check/<int:product_id>", methods=["GET"])
@require_auth
def check_wishlist_status(product_id):
    """Check whether a product is in current user's wishlist."""
    item = WishlistItem.query.filter_by(user_id=g.current_user.id, product_id=product_id).first()
    return jsonify({
        "success": True,
        "data": {
            "product_id": product_id,
            "is_wishlisted": item is not None,
            "wishlist_item_id": item.id if item else None,
        }
    }), 200


@api_v1.route("/wishlist", methods=["POST"])
@require_auth
def add_to_wishlist():
    """Add product to wishlist."""
    data = request.get_json() or {}
    product_id = data.get("product_id")

    if not product_id:
        raise APIException("product_id is required", status_code=400, code="VALIDATION_ERROR")

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        raise APIException("product_id must be an integer", status_code=400, code="VALIDATION_ERROR")

    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    if not product.is_active:
        raise APIException("Product is inactive and cannot be saved to wishlist", status_code=400, code="PRODUCT_INACTIVE")

    # Check for existing wishlist item
    existing = WishlistItem.query.filter_by(user_id=g.current_user.id, product_id=product.id).first()
    if existing:
        return jsonify({
            "success": True,
            "message": "Product is already in your wishlist",
            "data": serialize_wishlist_item(existing)
        }), 200

    item = WishlistItem(user_id=g.current_user.id, product_id=product.id)
    db.session.add(item)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Product added to wishlist",
        "data": serialize_wishlist_item(item)
    }), 201


@api_v1.route("/wishlist/<int:wishlist_item_id>", methods=["DELETE"])
@require_auth
def delete_wishlist_item(wishlist_item_id):
    """Remove item from wishlist (IDOR protected)."""
    item = WishlistItem.query.filter_by(id=wishlist_item_id, user_id=g.current_user.id).first()
    if not item:
        raise APIException("Wishlist item not found", status_code=404, code="WISHLIST_ITEM_NOT_FOUND")

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Item removed from wishlist"
    }), 200


@api_v1.route("/wishlist/<int:wishlist_item_id>/move-to-cart", methods=["POST"])
@require_auth
def move_wishlist_to_cart(wishlist_item_id):
    """Move product from wishlist to cart atomically (IDOR protected)."""
    wishlist_item = WishlistItem.query.filter_by(id=wishlist_item_id, user_id=g.current_user.id).first()
    if not wishlist_item:
        raise APIException("Wishlist item not found", status_code=404, code="WISHLIST_ITEM_NOT_FOUND")

    product = wishlist_item.product
    if not product or not product.is_active:
        raise APIException("Product is inactive and cannot be moved to cart", status_code=400, code="PRODUCT_INACTIVE")

    if product.stock_quantity <= 0:
        raise APIException("Product is out of stock and cannot be moved to cart", status_code=400, code="INSUFFICIENT_STOCK")

    # Check if item is already in user's cart
    existing_cart_item = CartItem.query.filter_by(user_id=g.current_user.id, product_id=product.id).first()

    if existing_cart_item:
        new_qty = existing_cart_item.quantity + 1
        if new_qty > product.stock_quantity:
            raise APIException(
                f"Cannot move to cart. Existing cart quantity ({existing_cart_item.quantity}) + 1 exceeds available stock ({product.stock_quantity})",
                status_code=400,
                code="INSUFFICIENT_STOCK",
            )
        existing_cart_item.quantity = new_qty
        target_cart_item = existing_cart_item
    else:
        target_cart_item = CartItem(user_id=g.current_user.id, product_id=product.id, quantity=1)
        db.session.add(target_cart_item)

    # Remove from wishlist in the same transaction
    db.session.delete(wishlist_item)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Item moved from wishlist to cart successfully",
        "data": serialize_cart_item(target_cart_item)
    }), 200
