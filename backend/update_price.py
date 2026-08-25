import os
from app import create_app
from app.extensions import db
from app.models.product import Product

app = create_app(os.environ.get("FLASK_ENV", "development"))

with app.app_context():
    product = Product.query.first()
    if product:
        old_price = product.price
        product.price = 10
        db.session.commit()
        print(f"SUCCESS: Updated product '{product.name}' price from {old_price} to 10.")
    else:
        print("ERROR: No products found.")
