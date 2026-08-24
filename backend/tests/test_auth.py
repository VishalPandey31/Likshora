import pytest
from app.models import User, CustomerLoginLog
from app.extensions import db
from app.auth.utils import (
    validate_email_format,
    validate_password_strength,
)
from app.errors import APIException


def test_password_strength_validation():
    """Test password strength rules."""
    # Too short
    with pytest.raises(APIException) as exc1:
        validate_password_strength("Short1")
    assert exc1.value.code == "WEAK_PASSWORD"

    # Only letters
    with pytest.raises(APIException) as exc2:
        validate_password_strength("OnlyLettersHere")
    assert exc2.value.code == "WEAK_PASSWORD"

    # Only numbers
    with pytest.raises(APIException) as exc3:
        validate_password_strength("1234567890")
    assert exc3.value.code == "WEAK_PASSWORD"

    # Valid password
    assert validate_password_strength("ValidPass123") == "ValidPass123"


def test_invalid_email_validation():
    """Test email format validation."""
    with pytest.raises(APIException) as exc:
        validate_email_format("invalid-email-string")
    assert exc.value.code == "INVALID_EMAIL"

    assert validate_email_format("user@example.com") == "user@example.com"


def test_protected_route_without_token_returns_401(client):
    """Test accessing protected route without Bearer token returns 401."""
    response = client.get("/api/v1/profile")
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] in ("UNAUTHORIZED", "INVALID_HEADER")


def test_protected_route_with_customer_token(client, app, monkeypatch):
    """Test accessing protected profile with valid customer token."""
    # Create test customer user in database
    with app.app_context():
        customer = User(
            supabase_uid="test-customer-uid-123",
            name="Customer User",
            email="customer@example.com",
            role="customer",
            is_active=True,
            email_verified=True,
        )
        db.session.add(customer)
        db.session.commit()

    # Mock Supabase token verification
    def mock_verify_token(token):
        return {
            "id": "test-customer-uid-123",
            "email": "customer@example.com",
            "user_metadata": {"name": "Customer User"},
            "confirmed_at": "2026-01-01T00:00:00Z",
        }

    monkeypatch.setattr("app.auth.decorators.supabase_auth.verify_token", mock_verify_token)

    response = client.get(
        "/api/v1/profile",
        headers={"Authorization": "Bearer mock-customer-jwt-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "customer@example.com"
    assert data["data"]["role"] == "customer"


def test_admin_route_denied_for_customer(client, app, monkeypatch):
    """Test accessing admin dashboard with customer token returns 403 Forbidden."""
    with app.app_context():
        customer = User(
            supabase_uid="test-customer-uid-456",
            name="Normal Customer",
            email="normalcustomer@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(customer)
        db.session.commit()

    def mock_verify_token(token):
        return {
            "id": "test-customer-uid-456",
            "email": "normalcustomer@example.com",
        }

    monkeypatch.setattr("app.auth.decorators.supabase_auth.verify_token", mock_verify_token)

    response = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": "Bearer mock-customer-jwt-token"},
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"


def test_admin_route_allowed_for_admin(client, app, monkeypatch):
    """Test accessing admin dashboard with admin token returns 200 OK."""
    with app.app_context():
        admin_user = User(
            supabase_uid="test-admin-uid-789",
            name="Admin User",
            email="admin@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin_user)
        db.session.commit()

    def mock_verify_token(token):
        return {
            "id": "test-admin-uid-789",
            "email": "admin@example.com",
        }

    monkeypatch.setattr("app.auth.decorators.supabase_auth.verify_token", mock_verify_token)

    response = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": "Bearer mock-admin-jwt-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "total_orders" in data["data"]


def test_profile_update_blocks_role_spoofing(client, app, monkeypatch):
    """Test that PUT /api/v1/profile rejects client attempts to elevate role to admin."""
    with app.app_context():
        customer = User(
            supabase_uid="test-spoof-uid",
            name="Attacker",
            email="attacker@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(customer)
        db.session.commit()

    def mock_verify_token(token):
        return {
            "id": "test-spoof-uid",
            "email": "attacker@example.com",
        }

    monkeypatch.setattr("app.auth.decorators.supabase_auth.verify_token", mock_verify_token)

    response = client.put(
        "/api/v1/profile",
        json={"role": "admin", "name": "Attacker Hacked"},
        headers={"Authorization": "Bearer mock-customer-jwt-token"},
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN_FIELD_UPDATE"


def test_login_logging_on_authentication(client, app, monkeypatch):
    """Test login attempt writes records to customer_login_logs table."""
    with app.app_context():
        user = User(
            supabase_uid="test-login-log-uid",
            name="Logging User",
            email="logginguser@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

    def mock_supabase_login(email, password):
        return {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 3600,
            "user": {
                "id": "test-login-log-uid",
                "email": "logginguser@example.com",
                "confirmed_at": "2026-01-01T00:00:00Z",
            },
        }

    monkeypatch.setattr("app.api.auth.supabase_auth.login", mock_supabase_login)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "logginguser@example.com", "password": "ValidPassword123"},
    )
    assert response.status_code == 200

    # Verify log entry in database
    with app.app_context():
        db_user = User.query.filter_by(email="logginguser@example.com").first()
        log_entry = CustomerLoginLog.query.filter_by(user_id=db_user.id).first()
        assert log_entry is not None
        assert log_entry.success is True


def test_resend_verification_endpoint(client, monkeypatch):
    """Test resend verification email endpoint."""
    def mock_resend(email):
        return {"message": f"Verification email has been sent again to {email}."}

    monkeypatch.setattr("app.api.auth.supabase_auth.resend_verification", mock_resend)

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "resendtest@example.com"}
    )
    assert response.status_code == 200
    assert response.json["success"] is True
    assert "sent again" in response.json["message"]


def test_update_password_endpoint(client, monkeypatch):
    """Test updating password using reset token."""
    def mock_update(access_token, new_password):
        return {"id": "user-123"}

    monkeypatch.setattr("app.api.auth.supabase_auth.update_password_with_token", mock_update)

    response = client.post(
        "/api/v1/auth/update-password",
        json={"access_token": "valid-token-xyz", "password": "NewSecurePassword123"}
    )
    assert response.status_code == 200
    assert response.json["success"] is True
    assert "Password updated" in response.json["message"]

