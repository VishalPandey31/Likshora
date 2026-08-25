from app import create_app
from app.extensions import db
from app.models import Product

app = create_app()

with app.app_context():
    print("Connecting to database:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    products = Product.query.all()
    print(f"Found {len(products)} products.")
    
    for product in products:
        product.stock_quantity = 100
        product.is_active = True
        print(f"Updated {product.name} stock to 100")
        
    db.session.commit()
    print("Successfully updated all product stocks in the database!")
