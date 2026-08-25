from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    email = "karanrajput.officials@gmail.com"
    admin = User.query.filter_by(email=email).first()
    
    if not admin:
        print("Admin user not found. Creating a new one...")
        admin = User(
            email=email,
            name="Admin Karan",
            role="admin",
            password_hash=generate_password_hash("Karan@2026")
        )
        admin.is_active = True
        admin.is_verified = True
        db.session.add(admin)
        db.session.commit()
        print(f"Created Admin ID: {admin.id} | Email: {email} | Password: Karan@2026")
    else:
        print("Admin user found. Resetting password...")
        admin.role = "admin"
        admin.is_active = True
        admin.password_hash = generate_password_hash("Karan@2026")
        db.session.commit()
        print(f"Reset Admin ID: {admin.id} | Email: {email} | Password: Karan@2026")
