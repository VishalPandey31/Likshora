import pytest
from app.models import Address, User
from app.extensions import db


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-a-addr-uid",
            name="Customer A",
            email="customeraaddr@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def customer_user_b(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-b-addr-uid",
            name="Customer B",
            email="customerbaddr@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


def test_unauthenticated_address_returns_401(client):
    """Test address endpoints return 401 when no token is provided."""
    assert client.get("/api/v1/addresses").status_code == 401
    assert client.post("/api/v1/addresses", json={}).status_code == 401


def test_get_empty_addresses(client, customer_user_a, monkeypatch):
    """Test GET /api/v1/addresses returns empty list for new user."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    response = client.get("/api/v1/addresses", headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"] == []
    assert data["count"] == 0


def test_create_and_manage_addresses(client, app, customer_user_a, monkeypatch):
    """Test creating addresses, automatic default logic, updating, and single default transaction."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    # 1. Create first address (Home) - should automatically become default
    res1 = client.post(
        "/api/v1/addresses",
        json={
            "full_name": "John Doe",
            "phone": "9876543210",
            "address_line1": "123 Main Street",
            "address_line2": "Apt 4B",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India",
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res1.status_code == 201
    addr1_id = res1.get_json()["data"]["id"]
    assert res1.get_json()["data"]["is_default"] is True

    # 2. Create second address (Office) with is_default=True
    res2 = client.post(
        "/api/v1/addresses",
        json={
            "full_name": "John Doe (Office)",
            "phone": "9876543210",
            "address_line1": "456 Tech Park",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400051",
            "country": "India",
            "is_default": True,
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res2.status_code == 201
    addr2_id = res2.get_json()["data"]["id"]
    assert res2.get_json()["data"]["is_default"] is True

    # Verify Address 1 default flag was cleared in database
    with app.app_context():
        a1 = db.session.get(Address, addr1_id)
        a2 = db.session.get(Address, addr2_id)
        assert a1.is_default is False
        assert a2.is_default is True

    # 3. Toggle Address 1 back to default via PATCH /api/v1/addresses/<id>/default
    res_def = client.patch(
        f"/api/v1/addresses/{addr1_id}/default",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_def.status_code == 200
    assert res_def.get_json()["data"]["is_default"] is True

    with app.app_context():
        a1 = db.session.get(Address, addr1_id)
        a2 = db.session.get(Address, addr2_id)
        assert a1.is_default is True
        assert a2.is_default is False


def test_delete_default_address_reassigns_default(client, app, customer_user_a, monkeypatch):
    """Test deleting default address promotes the remaining address to default."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    # Create Address 1 (Default)
    res1 = client.post(
        "/api/v1/addresses",
        json={
            "full_name": "Jane Doe",
            "phone": "9876543211",
            "address_line1": "789 Lake View",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "country": "India",
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    addr1_id = res1.get_json()["data"]["id"]

    # Create Address 2 (Non-Default)
    res2 = client.post(
        "/api/v1/addresses",
        json={
            "full_name": "Jane Doe Work",
            "phone": "9876543211",
            "address_line1": "101 Work Towers",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560002",
            "country": "India",
            "is_default": False,
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    addr2_id = res2.get_json()["data"]["id"]

    # Delete Address 1 (Default)
    res_del = client.delete(f"/api/v1/addresses/{addr1_id}", headers={"Authorization": "Bearer mock-token"})
    assert res_del.status_code == 200

    # Verify Address 2 was promoted to default
    with app.app_context():
        a2 = db.session.get(Address, addr2_id)
        assert a2 is not None
        assert a2.is_default is True


def test_address_validation_errors(client, customer_user_a, monkeypatch):
    """Test missing required fields returns 400 validation error."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    # Missing full_name and phone
    response = client.post(
        "/api/v1/addresses",
        json={
            "address_line1": "Street 1",
            "city": "Delhi",
            "state": "Delhi",
            "postal_code": "110001",
            "country": "India",
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_idor_protection_address(client, app, customer_user_a, customer_user_b, monkeypatch):
    """Test User B cannot access, update, default, or delete User A's address."""
    # User A creates address
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_a = client.post(
        "/api/v1/addresses",
        json={
            "full_name": "User A",
            "phone": "9999999999",
            "address_line1": "User A Home",
            "city": "Pune",
            "state": "Maharashtra",
            "postal_code": "411001",
            "country": "India",
        },
        headers={"Authorization": "Bearer user-a-token"},
    )
    user_a_addr_id = res_a.get_json()["data"]["id"]

    # User B attempts operations on User A's address
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )

    assert client.get(f"/api/v1/addresses/{user_a_addr_id}", headers={"Authorization": "Bearer user-b-token"}).status_code == 404
    assert client.put(f"/api/v1/addresses/{user_a_addr_id}", json={"full_name": "Hacked"}, headers={"Authorization": "Bearer user-b-token"}).status_code == 404
    assert client.patch(f"/api/v1/addresses/{user_a_addr_id}/default", headers={"Authorization": "Bearer user-b-token"}).status_code == 404
    assert client.delete(f"/api/v1/addresses/{user_a_addr_id}", headers={"Authorization": "Bearer user-b-token"}).status_code == 404
