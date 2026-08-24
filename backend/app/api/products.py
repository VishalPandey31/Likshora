import re
from flask import jsonify, request, g
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from app.api import api_v1
from app.auth.decorators import require_admin, get_authenticated_user_optional
from app.models import Product, Category, ProductImage, SearchHistory
from app.extensions import db
from app.errors import APIException


def slugify(text: str) -> str:
    """Generate a clean URL slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def serialize_product(product: Product, include_details: bool = True) -> dict:
    """Serialize product model to JSON dictionary."""
    images = sorted(product.images, key=lambda img: (not img.is_primary, img.display_order))
    primary_image = images[0].image_url if images else None

    res = {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": float(product.price),
        "selling_price": float(product.price),
        "compare_at_price": float(product.compare_at_price) if product.compare_at_price is not None else None,
        "list_price": float(product.compare_at_price) if product.compare_at_price is not None else None,
        "was": float(product.compare_at_price) if product.compare_at_price is not None else None,
        "sku": product.sku,
        "stock_quantity": product.stock_quantity,
        "stock": product.stock_quantity,
        "in_stock": product.stock_quantity > 0,
        "tagline": getattr(product, "tagline", None),
        "tags": getattr(product, "tags", None),
        "is_active": product.is_active,
        "is_featured": product.is_featured,
        "is_trending": product.is_trending,
        "primary_image_url": primary_image,
        "image": primary_image,
        "category": product.category.slug if product.category else None,
        "category_rel": {
            "id": product.category.id,
            "name": product.category.name,
            "slug": product.category.slug,
        } if product.category else None,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }

    if include_details:
        res["images"] = [
            {
                "id": img.id,
                "image_url": img.image_url,
                "alt_text": img.alt_text,
                "display_order": img.display_order,
                "is_primary": img.is_primary,
            }
            for img in images
        ]

    return res


def seed_catalog_if_empty():
    """Seed initial categories, products, and gallery images if catalog database is empty."""
    if Category.query.count() == 0:
        default_cats = [
            Category(name="Printed Kurtis", slug="kurtis", description="Breathable cotton dailywear kurtis", image_url="../../assets/images/products/product-kurti-1.jpg", is_active=True),
            Category(name="Kurta Sets", slug="sets", description="Paired with matching dupattas and bottoms", image_url="../../assets/images/products/product-kurti-2.jpg", is_active=True),
            Category(name="Co-ord Sets", slug="coords", description="Contemporary short kurtis paired with flared trousers", image_url="../../assets/images/products/product-kurti-3.jpg", is_active=True),
            Category(name="Festive Edit", slug="festive", description="Rich maroons, zari gold highlights for celebrations", image_url="../../assets/images/products/product-kurti-5.jpg", is_active=True),
        ]
        for c in default_cats:
            db.session.add(c)
        db.session.commit()

    if Product.query.count() == 0:
        cats_by_slug = {c.slug: c.id for c in Category.query.all()}
        default_prods = [
            {"sku": "AK01-RUST", "name": "Rust Bell-Sleeve Printed Kurti", "slug": "rust-bell-sleeve-printed-kurti", "price": 2299, "compare_at_price": 2799, "category_slug": "kurtis", "stock_quantity": 3, "description": "Breathable 100% cotton printed kurti with bell sleeves.", "image_url": "../../assets/images/products/product-kurti-1.jpg", "is_featured": True, "is_trending": True},
            {"sku": "AK02-MRN", "name": "Maroon Paisley Kurti — Desi Edit", "slug": "maroon-paisley-kurti-desi-edit", "price": 2599, "compare_at_price": None, "category_slug": "kurtis", "stock_quantity": 12, "description": "Rich burgundy maroon base with traditional paisley prints.", "image_url": "../../assets/images/products/product-kurti-2.jpg", "is_featured": True, "is_trending": True},
            {"sku": "SK01-BLK", "name": "Black Printed Cami Kurti", "slug": "black-printed-cami-kurti", "price": 1499, "compare_at_price": None, "category_slug": "kurtis", "stock_quantity": 2, "description": "Sleek black cami-style kurti with ivory block prints.", "image_url": "../../assets/images/products/product-kurti-3.jpg", "is_featured": False, "is_trending": False},
            {"sku": "SK02-BLK", "name": "Black Bell-Sleeve V-Neck Kurti", "slug": "black-bell-sleeve-v-neck-kurti", "price": 1699, "compare_at_price": 1999, "category_slug": "kurtis", "stock_quantity": 18, "description": "Classic black V-neck framed by flared bell sleeves.", "image_url": "../../assets/images/products/product-kurti-4.jpg", "is_featured": False, "is_trending": True},
            {"sku": "KS01-GLD", "name": "Aria Premium Long Kurti — Black Gold", "slug": "aria-premium-long-kurti-black-gold", "price": 2899, "compare_at_price": None, "category_slug": "sets", "stock_quantity": 8, "description": "Floor-length black kurta with hand-applied gold zari foil print.", "image_url": "../../assets/images/products/product-kurti-5.jpg", "is_featured": True, "is_trending": True},
            {"sku": "KS02-WINE", "name": "Rust Bell-Sleeve Printed Kurti — Wine", "slug": "rust-bell-sleeve-printed-kurti-wine", "price": 3299, "compare_at_price": 3799, "category_slug": "sets", "stock_quantity": 4, "description": "Wine maroon two-piece set featuring sleeve embroidery.", "image_url": "../../assets/images/products/product-kurti-1.jpg", "is_featured": False, "is_trending": False},
            {"sku": "CK01-MRN", "name": "Maroon Paisley Kurti — Blush Trim", "slug": "maroon-paisley-kurti-blush-trim", "price": 1399, "compare_at_price": None, "category_slug": "coords", "stock_quantity": 14, "description": "Short co-ord top with blush pink collar trimming.", "image_url": "../../assets/images/products/product-kurti-2.jpg", "is_featured": False, "is_trending": False},
            {"sku": "CK02-TEAL", "name": "Aria Premium Long Kurti — Teal Yoke", "slug": "aria-premium-long-kurti-teal-yoke", "price": 1899, "compare_at_price": None, "category_slug": "coords", "stock_quantity": 0, "description": "Teal yoke accent panel over structured maroon cotton.", "image_url": "../../assets/images/products/product-kurti-5.jpg", "is_featured": False, "is_trending": False},
        ]
        for item in default_prods:
            cat_id = cats_by_slug.get(item["category_slug"])
            prod = Product(
                sku=item["sku"],
                name=item["name"],
                slug=item["slug"],
                price=item["price"],
                compare_at_price=item["compare_at_price"],
                category_id=cat_id,
                stock_quantity=item["stock_quantity"],
                description=item["description"],
                is_active=True,
                is_featured=item["is_featured"],
                is_trending=item["is_trending"],
            )
            db.session.add(prod)
            db.session.flush()
            db.session.add(ProductImage(
                product_id=prod.id,
                image_url=item["image_url"],
                is_primary=True,
                display_order=0,
            ))
        db.session.commit()


@api_v1.route("/products", methods=["GET"])
def get_products():
    """Retrieve paginated, filtered, and sorted product catalog."""
    seed_catalog_if_empty()
    query = Product.query.options(joinedload(Product.category), selectinload(Product.images))

    include_inactive = request.args.get("include_inactive", "").lower() == "true"
    if not include_inactive:
        query = query.filter(Product.is_active == True)  # noqa: E712

    # Filter by category
    category_param = request.args.get("category", "").strip()
    if category_param:
        if category_param.isdigit():
            cat = db.session.get(Category, int(category_param))
        else:
            cat = Category.query.filter_by(slug=category_param).first()

        if not cat:
            raise APIException(f"Category '{category_param}' not found", status_code=404, code="CATEGORY_NOT_FOUND")
        query = query.filter(Product.category_id == cat.id)

    # Search filter (name, description, SKU)
    search_term = request.args.get("search", "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern),
                Product.sku.ilike(pattern),
            )
        )

    # Price range filter
    min_price_str = request.args.get("min_price")
    max_price_str = request.args.get("max_price")
    min_price = None
    max_price = None

    if min_price_str is not None and min_price_str.strip() != "":
        try:
            min_price = float(min_price_str)
            if min_price < 0:
                raise ValueError()
        except ValueError:
            raise APIException("min_price must be a non-negative number", status_code=400, code="INVALID_PRICE_FILTER")
        query = query.filter(Product.price >= min_price)

    if max_price_str is not None and max_price_str.strip() != "":
        try:
            max_price = float(max_price_str)
            if max_price < 0:
                raise ValueError()
        except ValueError:
            raise APIException("max_price must be a non-negative number", status_code=400, code="INVALID_PRICE_FILTER")
        query = query.filter(Product.price <= max_price)

    if min_price is not None and max_price is not None and min_price > max_price:
        raise APIException("min_price cannot be greater than max_price", status_code=400, code="INVALID_PRICE_RANGE")

    # Featured & Trending filters
    if request.args.get("featured", "").lower() == "true":
        query = query.filter(Product.is_featured == True)  # noqa: E712

    if request.args.get("trending", "").lower() == "true":
        query = query.filter(Product.is_trending == True)  # noqa: E712

    # Sorting
    sort_option = request.args.get("sort", "newest").lower().strip()
    if sort_option == "price_low_to_high":
        query = query.order_by(Product.price.asc())
    elif sort_option == "price_high_to_low":
        query = query.order_by(Product.price.desc())
    elif sort_option == "name_asc":
        query = query.order_by(Product.name.asc())
    elif sort_option == "name_desc":
        query = query.order_by(Product.name.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    # Pagination
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        if page < 1 or per_page < 1:
            raise ValueError()
        per_page = min(per_page, 100)
    except ValueError:
        raise APIException("page and per_page must be positive integers", status_code=400, code="INVALID_PAGINATION")

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    if search_term:
        user = get_authenticated_user_optional()
        if user:
            try:
                search_entry = SearchHistory(
                    user_id=user.id,
                    search_query=search_term,
                    results_count=pagination.total,
                )
                db.session.add(search_entry)
                db.session.commit()
            except Exception:
                db.session.rollback()

    return jsonify({
        "success": True,
        "data": [serialize_product(p, include_details=True) for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    }), 200


@api_v1.route("/products/<product_identifier>", methods=["GET"])
def get_product_detail(product_identifier):
    """Retrieve detailed product information."""
    query = Product.query.options(joinedload(Product.category), selectinload(Product.images))

    if product_identifier.isdigit():
        product = query.filter(Product.id == int(product_identifier)).first()
    else:
        product = query.filter(Product.slug == product_identifier).first()

    if not product or not product.is_active:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    return jsonify({
        "success": True,
        "data": serialize_product(product, include_details=True)
    }), 200


@api_v1.route("/products", methods=["POST"])
@require_admin
def create_product():
    """Create new product listing (Admin-only)."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    sku = (data.get("sku") or "").strip()

    if not name or not sku:
        raise APIException("Product name and SKU are required", status_code=400, code="VALIDATION_ERROR")

    try:
        price = float(data.get("price", -1))
        if price < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise APIException("Product price must be a non-negative number", status_code=400, code="INVALID_PRICE")

    cap_val = data.get("compare_at_price") if "compare_at_price" in data else data.get("was")
    compare_at_price = None
    if cap_val is not None and str(cap_val).strip() != "":
        try:
            compare_at_price = float(cap_val)
            if compare_at_price < 0:
                raise ValueError()
        except ValueError:
            raise APIException("compare_at_price must be a non-negative number", status_code=400, code="INVALID_PRICE")

    stock_val = data.get("stock_quantity") if "stock_quantity" in data else data.get("stock", 0)
    try:
        stock_quantity = int(stock_val)
        if stock_quantity < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise APIException("stock_quantity must be a non-negative integer", status_code=400, code="INVALID_STOCK")

    category_id = data.get("category_id")
    category_param = data.get("category")
    if not category_id and category_param:
        if isinstance(category_param, int) or (isinstance(category_param, str) and category_param.isdigit()):
            category_id = int(category_param)
        else:
            cat = Category.query.filter((Category.slug == category_param) | (Category.name == category_param)).first()
            if cat:
                category_id = cat.id

    if category_id:
        cat = db.session.get(Category, category_id)
        if not cat:
            raise APIException("Category not found", status_code=404, code="CATEGORY_NOT_FOUND")

    slug = (data.get("slug") or "").strip()
    if not slug:
        slug = slugify(name)

    if Product.query.filter_by(sku=sku).first():
        raise APIException("Product SKU already exists", status_code=409, code="SKU_EXISTS")
    if Product.query.filter_by(slug=slug).first():
        raise APIException("Product slug already exists", status_code=409, code="SLUG_EXISTS")

    is_active = bool(data.get("is_active", True))
    if "status" in data:
        is_active = data["status"] != "Draft" and data["status"] != "Inactive"

    product = Product(
        name=name,
        slug=slug,
        sku=sku,
        price=price,
        compare_at_price=compare_at_price,
        stock_quantity=stock_quantity,
        category_id=category_id,
        description=data.get("description"),
        tagline=data.get("tagline"),
        tags=data.get("tags"),
        is_active=is_active,
        is_featured=bool(data.get("is_featured", False)),
        is_trending=bool(data.get("is_trending", False)),
    )
    db.session.add(product)
    db.session.flush()

    # Save images if provided in request
    image_url = data.get("image") or data.get("image_url")
    if image_url:
        db.session.add(ProductImage(
            product_id=product.id,
            image_url=image_url,
            is_primary=True,
            display_order=0,
        ))

    images_list = data.get("images")
    if images_list and isinstance(images_list, list):
        for idx, img_item in enumerate(images_list):
            url = img_item if isinstance(img_item, str) else (img_item.get("url") or img_item.get("image_url"))
            if url and url != image_url:
                db.session.add(ProductImage(
                    product_id=product.id,
                    image_url=url,
                    is_primary=False,
                    display_order=idx + 1,
                ))

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Product created successfully",
        "data": serialize_product(product, include_details=True)
    }), 201


@api_v1.route("/products/<int:product_id>", methods=["PUT"])
@require_admin
def update_product(product_id):
    """Update existing product details (Admin-only)."""
    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    data = request.get_json() or {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            raise APIException("Product name cannot be empty", status_code=400, code="VALIDATION_ERROR")
        product.name = name

    if "slug" in data:
        slug = slugify(data["slug"])
        if not slug:
            raise APIException("Product slug cannot be empty", status_code=400, code="VALIDATION_ERROR")
        existing = Product.query.filter(Product.slug == slug, Product.id != product_id).first()
        if existing:
            raise APIException("Product slug already exists", status_code=409, code="SLUG_EXISTS")
        product.slug = slug

    if "sku" in data:
        sku = (data["sku"] or "").strip()
        if not sku:
            raise APIException("Product SKU cannot be empty", status_code=400, code="VALIDATION_ERROR")
        existing = Product.query.filter(Product.sku == sku, Product.id != product_id).first()
        if existing:
            raise APIException("Product SKU already exists", status_code=409, code="SKU_EXISTS")
        product.sku = sku

    if "price" in data:
        try:
            price = float(data["price"])
            if price < 0:
                raise ValueError()
            product.price = price
        except (ValueError, TypeError):
            raise APIException("Product price must be a non-negative number", status_code=400, code="INVALID_PRICE")

    cap_val = data.get("compare_at_price") if "compare_at_price" in data else data.get("was")
    if cap_val is not None:
        if cap_val == "" or cap_val is None:
            product.compare_at_price = None
        else:
            try:
                cap = float(cap_val)
                if cap < 0:
                    raise ValueError()
                product.compare_at_price = cap
            except (ValueError, TypeError):
                raise APIException("compare_at_price must be a non-negative number", status_code=400, code="INVALID_PRICE")

    stock_val = data.get("stock_quantity") if "stock_quantity" in data else data.get("stock")
    if stock_val is not None:
        try:
            stock = int(stock_val)
            if stock < 0:
                raise ValueError()
            product.stock_quantity = stock
        except (ValueError, TypeError):
            raise APIException("stock_quantity must be a non-negative integer", status_code=400, code="INVALID_STOCK")

    if "category_id" in data or "category" in data:
        cid = data.get("category_id")
        category_param = data.get("category")
        if not cid and category_param:
            cat = Category.query.filter((Category.slug == category_param) | (Category.name == category_param)).first()
            if cat: cid = cat.id
        if cid is not None:
            cat = db.session.get(Category, cid)
            if not cat:
                raise APIException("Category not found", status_code=404, code="CATEGORY_NOT_FOUND")
            product.category_id = cid

    if "description" in data:
        product.description = data["description"]

    if "tagline" in data:
        product.tagline = data["tagline"]

    if "tags" in data:
        product.tags = data["tags"]

    if "is_active" in data:
        product.is_active = bool(data["is_active"])
    elif "status" in data:
        product.is_active = data["status"] != "Draft" and data["status"] != "Inactive"

    if "is_featured" in data:
        product.is_featured = bool(data["is_featured"])

    if "is_trending" in data:
        product.is_trending = bool(data["is_trending"])

    # Update primary image if passed
    image_url = data.get("image") or data.get("image_url")
    if image_url:
        ProductImage.query.filter_by(product_id=product_id).update({"is_primary": False})
        primary_img = ProductImage.query.filter_by(product_id=product_id, image_url=image_url).first()
        if primary_img:
            primary_img.is_primary = True
        else:
            db.session.add(ProductImage(product_id=product_id, image_url=image_url, is_primary=True, display_order=0))

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Product updated successfully",
        "data": serialize_product(product, include_details=True)
    }), 200


@api_v1.route("/products/<int:product_id>", methods=["DELETE"])
@require_admin
def delete_product(product_id):
    """Soft-deactivate product (Admin-only)."""
    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    product.is_active = False
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Product '{product.name}' has been deactivated successfully",
        "data": serialize_product(product, include_details=False)
    }), 200


@api_v1.route("/products/<int:product_id>/stock", methods=["PATCH"])
@require_admin
def update_product_stock(product_id):
    """Update inventory stock quantity (Admin-only)."""
    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    data = request.get_json() or {}
    stock_val = data.get("stock_quantity") if "stock_quantity" in data else data.get("stock")
    if stock_val is None:
        raise APIException("stock_quantity or stock is required", status_code=400, code="VALIDATION_ERROR")

    try:
        new_stock = int(stock_val)
        if new_stock < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise APIException("stock_quantity must be a non-negative integer", status_code=400, code="INVALID_STOCK")

    product.stock_quantity = new_stock
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Stock updated successfully",
        "data": {
            "product_id": product.id,
            "sku": product.sku,
            "stock_quantity": product.stock_quantity,
            "in_stock": product.stock_quantity > 0,
        }
    }), 200


@api_v1.route("/products/<int:product_id>/images", methods=["POST"])
@require_admin
def add_product_image(product_id):
    """Add gallery image to product (Admin-only)."""
    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    data = request.get_json() or {}
    image_url = (data.get("image_url") or "").strip()
    if not image_url:
        raise APIException("image_url is required", status_code=400, code="VALIDATION_ERROR")

    is_primary = bool(data.get("is_primary", False))
    if is_primary:
        # Unset existing primary image flags for this product
        ProductImage.query.filter_by(product_id=product_id).update({"is_primary": False})

    try:
        display_order = int(data.get("display_order", 0))
    except (ValueError, TypeError):
        display_order = 0

    image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        alt_text=data.get("alt_text"),
        display_order=display_order,
        is_primary=is_primary,
    )
    db.session.add(image)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Product image added successfully",
        "data": {
            "id": image.id,
            "product_id": image.product_id,
            "image_url": image.image_url,
            "alt_text": image.alt_text,
            "display_order": image.display_order,
            "is_primary": image.is_primary,
        }
    }), 201


@api_v1.route("/products/<int:product_id>/images/<int:image_id>", methods=["DELETE"])
@require_admin
def delete_product_image(product_id, image_id):
    """Delete gallery image from product (Admin-only)."""
    image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first()
    if not image:
        raise APIException("Product image not found", status_code=404, code="IMAGE_NOT_FOUND")

    db.session.delete(image)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Product image deleted successfully"
    }), 200
