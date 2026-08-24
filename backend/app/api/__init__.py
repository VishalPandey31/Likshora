from flask import Blueprint

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

from app.api import (  # noqa: F401, E402
    health,
    auth,
    profile,
    admin,
    categories,
    products,
    cart,
    wishlist,
    addresses,
    orders,
    payments,
    shipments,
    content,
    upload,
    search_history,
    reviews,
)
