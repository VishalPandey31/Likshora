# Likshora - E-Commerce Backend

Likshora is a modern e-commerce clothing system. This repository contains the backend RESTful API built with Python Flask, Flask-SQLAlchemy, Flask-Migrate, Supabase Auth, and PostgreSQL (Supabase).

---

## 🛠️ Technology Stack

- **Backend Framework:** Python Flask (v3.0+)
- **Database:** Supabase PostgreSQL
- **Authentication:** Supabase Auth (JWT + Bearer Token)
- **Payment Integration:** Razorpay Python SDK (Online) & Cash on Delivery (COD)
- **Shipping Gateway Integration:** Shiprocket API v2 (Adhoc Order Creation, AWB Generation & Live Tracking)
- **Order Tracking Engine:** Real-Time Tracking Timelines, Status Normalization & Event Logging (`ShipmentTrackingEvent`)
- **ORM:** Flask-SQLAlchemy (SQLAlchemy 2.0+)
- **Database Migrations:** Flask-Migrate (Alembic)
- **CORS Management:** Flask-CORS
- **Environment Management:** python-dotenv
- **Testing:** Pytest

---

## 📁 Project Structure

```
likshora/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask Application Factory (create_app)
│   │   ├── config.py            # Environment Configuration Loader
│   │   ├── extensions.py        # Centralized SQLAlchemy, Migrate, CORS Instances
│   │   ├── errors.py            # Centralized JSON Error Handlers (400, 401, 403, 404, 405, 500)
│   │   ├── logging_config.py    # Structured Logging Setup
│   │   │
│   │   ├── auth/                # Supabase Auth Client & Authorization Middleware
│   │   │   ├── __init__.py
│   │   │   ├── supabase_client.py
│   │   │   ├── decorators.py    # @require_auth & @require_admin
│   │   │   └── utils.py         # Validation helpers
│   │   │
│   │   ├── services/            # External Integration & Domain Service Layer
│   │   │   ├── __init__.py
│   │   │   ├── shiprocket_service.py # Shiprocket API Authentication, Order Creation, AWB & Live Tracking
│   │   │   └── tracking_service.py   # Status Normalization, Event Sync & Timeline Generator
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py      # Versioned API Blueprint Registration (/api/v1)
│   │   │   ├── health.py        # API & DB Health Endpoints
│   │   │   ├── auth.py          # Signup, Login, Logout, Password Recovery
│   │   │   ├── profile.py       # Customer Profile GET/PUT Endpoints
│   │   │   ├── admin.py         # Admin Dashboard Metrics, Inventory Low-Stock Alerts & Customer Management
│   │   │   ├── categories.py    # Category CRUD Endpoints
│   │   │   ├── products.py      # Product Catalog, Search, Filter, Stock, Image Endpoints
│   │   │   ├── cart.py          # Customer Cart Endpoints & Subtotal Calculations
│   │   │   ├── wishlist.py      # Customer Wishlist Endpoints, Status Check & Move-to-Cart
│   │   │   ├── addresses.py     # Customer Address CRUD & Default Address Endpoints
│   │   │   ├── orders.py        # Atomic Checkout (COD + Online), Coupon Engine, Order Tracking GET & Admin COD Payment Endpoint
│   │   │   ├── payments.py      # Razorpay Order Creation, HMAC Signature Verification & RAW Body Webhooks
│   │   │   └── shipments.py     # Admin Shipment Creation, Admin Sync Refresh & Shiprocket Webhooks
│   │   │
│   │   └── models/              # Database Models (17 Domain Tables)
│   │       ├── __init__.py      # Exports all models for Alembic discovery
│   │       ├── base.py          # TimestampMixin (created_at, updated_at)
│   │       ├── user.py          # User, CustomerLoginLog models
│   │       ├── category.py      # Category model
│   │       ├── product.py       # Product model (with is_trending)
│   │       ├── product_image.py # ProductImage model
│   │       ├── cart_item.py     # CartItem model
│   │       ├── wishlist_item.py # WishlistItem model
│   │       ├── address.py       # Address model
│   │       ├── coupon.py        # Coupon, CouponUsage models
│   │       ├── order.py         # Order (with Address Snapshot), OrderItem models
│   │       ├── payment.py       # Payment, PaymentWebhookEvent models
│   │       └── shipment.py      # Shipment, ShipmentWebhookEvent & ShipmentTrackingEvent models
│   │
│   ├── migrations/              # Database Migration Scripts (Flask-Migrate)
│   │   └── versions/            # Migration Version Files
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest Fixtures (App & Client)
│   │   ├── test_config.py       # Configuration & URL Normalization Tests
│   │   ├── test_health.py       # Health Check & Error Response Tests
│   │   ├── test_models.py       # Model Schema & Constraint Tests
│   │   ├── test_auth.py         # Supabase Auth & RBAC Tests
│   │   ├── test_categories.py   # Category Endpoint Tests
│   │   ├── test_products.py     # Product Catalog & Admin Endpoint Tests
│   │   ├── test_cart.py         # Cart & Stock Validation Tests
│   │   ├── test_wishlist.py     # Wishlist, Status Check & Move-to-Cart Tests
│   │   ├── test_addresses.py    # Address CRUD & Default Address Tests
│   │   ├── test_orders.py       # Order Checkout, Coupon, Stock & State Machine Tests
│   │   ├── test_admin.py        # Admin Dashboard Metrics, Low-Stock & Customer Management Tests
│   │   ├── test_payments.py     # Razorpay Order, Signature Verification & RAW Webhook Tests
│   │   ├── test_cod.py          # Cash on Delivery (COD) Checkout, Isolation & Admin Payment Confirmation Tests
│   │   ├── test_shipments.py    # Shiprocket Authentication, Adhoc Order Creation, AWB & Webhook Tests
│   │   └── test_tracking.py     # Order Tracking Timeline, Status Normalization, IDOR & Event Logging Tests
│   │
│   ├── run.py                   # Server Entry Point Launcher
│   ├── requirements.txt         # Project Dependencies
│   ├── .env                     # Local Environment Secrets (Git Ignored)
│   ├── .env.example             # Environment Variable Template
│   └── .gitignore               # Exclusions for Git
│
└── README.md                    # Project Documentation
```

---

## ⚙️ Local Setup Instructions

### 1. Navigate to the Backend Directory
```bash
cd backend
```

### 2. Create Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv venv
```

### 3. Activate Virtual Environment
On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration

Update `.env` with your credentials:
```env
FLASK_ENV=development
SECRET_KEY=your-secure-random-secret-key
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
SHIPROCKET_EMAIL=your_shiprocket_email@example.com
SHIPROCKET_PASSWORD=your_shiprocket_password
SHIPROCKET_WEBHOOK_TOKEN=your_shiprocket_webhook_token
SHIPROCKET_PICKUP_LOCATION=Primary
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🚀 Running the Backend Server

```bash
python run.py
```
The server starts at `http://127.0.0.1:5000`.

---

## 🧪 Automated Testing

To run the full 114-test automated Pytest suite:
```bash
pytest -v
```

---

## 🔄 Database Migrations (Flask-Migrate)

Applying database migrations to Supabase PostgreSQL:

```bash
flask db upgrade
```
