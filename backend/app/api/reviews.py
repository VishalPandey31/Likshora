from flask import jsonify, request, g
from app.api import api_v1
from app.auth.decorators import require_auth
from app.models import Review, Product
from app.extensions import db
from app.errors import APIException


def serialize_review(review: Review, include_customer: bool = True) -> dict:
    """Serialize review model object."""
    data = {
        "id": review.id,
        "product_id": review.product_id,
        "rating": review.rating,
        "comment": review.comment,
        "status": review.status,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    }
    if include_customer and review.user:
        data["customer_name"] = review.user.name
        data["customer_email"] = review.user.email
    if review.product:
        data["product_name"] = review.product.name

    return data


@api_v1.route("/products/<int:product_id>/reviews", methods=["GET"])
def get_product_reviews(product_id):
    """Retrieve approved customer reviews for a specific product."""
    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    reviews = (
        Review.query.filter_by(product_id=product_id, status="approved")
        .order_by(Review.created_at.desc())
        .all()
    )

    avg_rating = 0.0
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    return jsonify({
        "success": True,
        "data": {
            "reviews": [serialize_review(r) for r in reviews],
            "average_rating": avg_rating,
            "total_reviews": len(reviews),
        }
    }), 200


@api_v1.route("/products/<int:product_id>/reviews", methods=["POST"])
@require_auth
def submit_product_review(product_id):
    """Submit or update a product review (authenticated customer)."""
    product = db.session.get(Product, product_id)
    if not product:
        raise APIException("Product not found", status_code=404, code="PRODUCT_NOT_FOUND")

    data = request.get_json() or {}
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()

    if not rating:
        raise APIException("Rating is required", status_code=400, code="VALIDATION_ERROR")

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError()
    except (ValueError, TypeError):
        raise APIException("Rating must be an integer between 1 and 5", status_code=400, code="INVALID_RATING")

    # Upsert review per user & product
    existing_review = Review.query.filter_by(user_id=g.current_user.id, product_id=product_id).first()

    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.status = "pending"  # Reset to pending for admin moderation if edited
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Review updated successfully and is pending approval",
            "data": serialize_review(existing_review)
        }), 200
    else:
        review = Review(
            user_id=g.current_user.id,
            product_id=product_id,
            rating=rating,
            comment=comment,
            status="pending",
        )
        db.session.add(review)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Review submitted successfully and is pending approval",
            "data": serialize_review(review)
        }), 201
