import re
from flask import jsonify, request, g
from app.api import api_v1
from app.auth.decorators import require_admin
from app.models import Category, Product
from app.extensions import db
from app.errors import APIException


def slugify(text: str) -> str:
    """Generate a clean URL slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def serialize_category(category: Category) -> dict:
    """Serialize category model to JSON dict."""
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "image_url": category.image_url,
        "is_active": category.is_active,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None,
    }


@api_v1.route("/categories", methods=["GET"])
def get_categories():
    """Retrieve list of categories."""
    include_inactive = request.args.get("include_inactive", "").lower() == "true"
    query = Category.query

    # Only expose inactive categories if explicitly requested
    if not include_inactive:
        query = query.filter_by(is_active=True)

    categories = query.order_by(Category.name.asc()).all()
    return jsonify({
        "success": True,
        "data": [serialize_category(cat) for cat in categories]
    }), 200


@api_v1.route("/categories/<category_identifier>", methods=["GET"])
def get_category_detail(category_identifier):
    """Retrieve single category and its active products."""
    if category_identifier.isdigit():
        category = db.session.get(Category, int(category_identifier))
    else:
        category = Category.query.filter_by(slug=category_identifier).first()

    if not category or not category.is_active:
        raise APIException("Category not found", status_code=404, code="CATEGORY_NOT_FOUND")

    # Retrieve active products belonging to category
    active_products = (
        Product.query.filter_by(category_id=category.id, is_active=True)
        .order_by(Product.created_at.desc())
        .all()
    )

    category_data = serialize_category(category)
    category_data["products_count"] = len(active_products)

    return jsonify({
        "success": True,
        "data": {
            "category": category_data,
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "price": float(p.price),
                    "compare_at_price": float(p.compare_at_price) if p.compare_at_price else None,
                    "sku": p.sku,
                    "stock_quantity": p.stock_quantity,
                    "in_stock": p.stock_quantity > 0,
                    "is_featured": p.is_featured,
                    "is_trending": p.is_trending,
                }
                for p in active_products
            ],
        }
    }), 200


@api_v1.route("/categories", methods=["POST"])
@require_admin
def create_category():
    """Create new category (Admin-only)."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()

    if not name:
        raise APIException("Category name is required", status_code=400, code="VALIDATION_ERROR")

    slug = (data.get("slug") or "").strip()
    if not slug:
        slug = slugify(name)

    # Validate uniqueness of name and slug
    if Category.query.filter_by(name=name).first():
        raise APIException("Category with this name already exists", status_code=409, code="CATEGORY_EXISTS")
    if Category.query.filter_by(slug=slug).first():
        raise APIException("Category slug already exists", status_code=409, code="SLUG_EXISTS")

    category = Category(
        name=name,
        slug=slug,
        description=data.get("description"),
        image_url=data.get("image_url"),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Category created successfully",
        "data": serialize_category(category)
    }), 201


@api_v1.route("/categories/<int:category_id>", methods=["PUT"])
@require_admin
def update_category(category_id):
    """Update existing category (Admin-only)."""
    category = db.session.get(Category, category_id)
    if not category:
        raise APIException("Category not found", status_code=404, code="CATEGORY_NOT_FOUND")

    data = request.get_json() or {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            raise APIException("Category name cannot be empty", status_code=400, code="VALIDATION_ERROR")
        existing = Category.query.filter(Category.name == name, Category.id != category_id).first()
        if existing:
            raise APIException("Category with this name already exists", status_code=409, code="CATEGORY_EXISTS")
        category.name = name

    if "slug" in data:
        slug = slugify(data["slug"])
        if not slug:
            raise APIException("Category slug cannot be empty", status_code=400, code="VALIDATION_ERROR")
        existing = Category.query.filter(Category.slug == slug, Category.id != category_id).first()
        if existing:
            raise APIException("Category slug already exists", status_code=409, code="SLUG_EXISTS")
        category.slug = slug

    if "description" in data:
        category.description = data["description"]

    if "image_url" in data:
        category.image_url = data["image_url"]

    if "is_active" in data:
        category.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Category updated successfully",
        "data": serialize_category(category)
    }), 200


@api_v1.route("/categories/<int:category_id>", methods=["DELETE"])
@require_admin
def delete_category(category_id):
    """Soft-deactivate category (Admin-only)."""
    category = db.session.get(Category, category_id)
    if not category:
        raise APIException("Category not found", status_code=404, code="CATEGORY_NOT_FOUND")

    # Soft deactivate category to preserve product and historical relations
    category.is_active = False
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Category '{category.name}' has been deactivated successfully",
        "data": serialize_category(category)
    }), 200
