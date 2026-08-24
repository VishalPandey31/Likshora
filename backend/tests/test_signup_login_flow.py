import pytest
from app.models import (
    User, Address, CartItem, WishlistItem, Order, Payment
)
from app.extensions import db


def test_complete_signup_and_db_persistence(client, app, monkeypatch):
    """Test Create Account flow: backend receives request, creates Supabase user & DB profile with same UUID."""
    signup_uuid = "supa-auth-uuid-signup-test"

    def mock_supabase_signup(email, password, user_metadata):
        return {
            "user": {
                "id": signup_uuid,
                "email": email,
                "user_metadata": user_metadata,
                "confirmed_at": None,
            }
        }

    monkeypatch.setattr("app.api.auth.supabase_auth.signup", mock_supabase_signup)

    # 1. Frontend sends signup request
    signup_payload = {
        "name": "Rahul Sharma",
        "email": "rahul.signup@example.com",
        "phone": "9876543210",
        "password": "ValidPassword123",
    }
    res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert res.status_code == 201
    assert res.json["success"] is True

    # 2. Database contains profile with SAME Supabase Auth UUID
    with app.app_context():
        user = User.query.filter_by(email="rahul.signup@example.com").first()
        assert user is not None
        assert user.id == signup_uuid
        assert user.supabase_uid == signup_uuid
        assert user.name == "Rahul Sharma"
        assert user.phone == "9876543210"
        assert user.role == "customer"
        assert user.password_hash is None  # Password NOT stored in app database!


def test_duplicate_signup_prevention(client, app, monkeypatch):
    """Test duplicate signup returns error and prevents duplicate database user records."""
    with app.app_context():
        existing = User(
            id="dup-user-uuid",
            supabase_uid="dup-user-uuid",
            name="Existing User",
            email="existing@example.com",
            phone="9876543211",
            role="customer",
        )
        db.session.add(existing)
        db.session.commit()

    res = client.post("/api/v1/auth/signup", json={
        "name": "Existing User 2",
        "email": "existing@example.com",
        "phone": "9876543212",
        "password": "ValidPassword123",
    })
    assert res.status_code == 400
    assert res.json["success"] is False
    assert res.json["error"]["code"] == "EMAIL_EXISTS"


def test_login_uses_same_supabase_uuid(client, app, monkeypatch):
    """Test login authenticates with Supabase, identifies same Supabase UUID, and loads profile."""
    user_uuid = "supa-auth-uuid-login-test"

    with app.app_context():
        user = User(
            id=user_uuid,
            supabase_uid=user_uuid,
            name="Priya Patel",
            email="priya@example.com",
            phone="9876543299",
            role="customer",
            is_active=True,
            email_verified=True,
        )
        db.session.add(user)
        db.session.commit()

    def mock_supabase_login(email, password):
        return {
            "access_token": "mock-access-token-priya",
            "refresh_token": "mock-refresh-token-priya",
            "expires_in": 3600,
            "user": {
                "id": user_uuid,
                "email": "priya@example.com",
                "confirmed_at": "2026-01-01T00:00:00Z",
            },
        }

    monkeypatch.setattr("app.api.auth.supabase_auth.login", mock_supabase_login)

    # User logs in with email & password
    res = client.post("/api/v1/auth/login", json={
        "email": "priya@example.com",
        "password": "ValidPassword123",
    })
    assert res.status_code == 200
    assert res.json["success"] is True
    assert res.json["data"]["access_token"] == "mock-access-token-priya"
    assert res.json["data"]["user"]["id"] == user_uuid
    assert res.json["data"]["user"]["email"] == "priya@example.com"
    assert res.json["data"]["user"]["name"] == "Priya Patel"
