import time
import requests
from sqlalchemy import text

BASE_URL = "http://127.0.0.1:5000/api/v1"

def run_tests():
    print("==========================================")
    print("RUNNING AUTHENTICATION & ERROR HANDLER TESTS")
    print("==========================================")

    # TEST A: New valid account signup
    t_stamp = int(time.time())
    test_email = f"test_customer_{t_stamp}@gmail.com"
    test_password = "SecurePassword123!"
    test_name = "Test Customer"
    test_phone = f"98{t_stamp % 100000000:08d}"

    print(f"\n1. TEST A: Signup new account ({test_email})...")
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "name": test_name,
        "email": test_email,
        "phone": test_phone,
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    assert res.json().get("success") is True
    created_user_id = res.json()["data"]["user_id"]
    print("-> TEST A PASSED!")

    # TEST B: Existing email signup
    print(f"\n2. TEST B: Signup existing email ({test_email})...")
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "name": test_name,
        "email": test_email,
        "phone": f"97{t_stamp % 100000000:08d}",
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "EMAIL_EXISTS"
    assert "already exists" in res.json()["error"]["message"].lower()
    print("-> TEST B PASSED!")

    # TEST C: Invalid email format
    print("\n3. TEST C: Signup invalid email format...")
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "name": test_name,
        "email": "not-an-email",
        "phone": f"96{t_stamp % 100000000:08d}",
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 400
    assert res.json()["error"]["code"] in ["INVALID_EMAIL", "VALIDATION_ERROR"]
    print("-> TEST C PASSED!")

    # TEST D: Weak password
    print("\n4. TEST D: Signup weak password...")
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "name": test_name,
        "email": f"weak_{t_stamp}@gmail.com",
        "phone": f"95{t_stamp % 100000000:08d}",
        "password": "short"
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "WEAK_PASSWORD"
    print("-> TEST D PASSED!")

    # TEST E: Missing fields
    print("\n5. TEST E: Signup missing name...")
    res = requests.post(f"{BASE_URL}/auth/signup", json={
        "name": "",
        "email": f"noname_{t_stamp}@gmail.com",
        "phone": f"94{t_stamp % 100000000:08d}",
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    print("-> TEST E PASSED!")

    # TEST F: Login before email verification
    print(f"\n6. TEST F: Login before email verification ({test_email})...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 401
    assert res.json()["error"]["code"] in ["EMAIL_NOT_VERIFIED", "INVALID_CREDENTIALS"]
    print("-> TEST F (Unverified login blocked) PASSED!")

    # Confirm email via Supabase Admin API for login test
    print("\nConfirming email via Supabase Admin API for verified login test...")
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNhcmViYWJ3dmxmcGFrb2VkZW5zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4Njg5NjQyNCwiZXhwIjoyMTAyNDcyNDI0fQ.fW3jjaMj56IPjCx0ZTP3GXhd17xSWz2Ga7KHCObr6L8"
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    confirm_res = requests.put(f"https://sarebabwvlfpakoedens.supabase.co/auth/v1/admin/users/{created_user_id}", json={"email_confirm": True}, headers=headers, verify=False)
    print("Confirm status:", confirm_res.status_code)

    # TEST G: Successful login after verification
    print(f"\n7. TEST G: Login with verified account ({test_email})...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 200
    assert res.json().get("success") is True
    assert "access_token" in res.json()["data"]
    print("-> TEST G PASSED!")

    # TEST H: Wrong password login
    print(f"\n8. TEST H: Login with wrong password ({test_email})...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": "WrongPassword999!"
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert "invalid" in res.json()["error"]["message"].lower()
    print("-> TEST H PASSED!")

    # Clean up test user
    print("\nCleaning up test user...")
    from app import create_app
    from app.extensions import db
    app = create_app()
    with app.app_context():
        db.session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": created_user_id})
        db.session.commit()
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNhcmViYWJ3dmxmcGFrb2VkZW5zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4Njg5NjQyNCwiZXhwIjoyMTAyNDcyNDI0fQ.fW3jjaMj56IPjCx0ZTP3GXhd17xSWz2Ga7KHCObr6L8"
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        requests.delete(f"https://sarebabwvlfpakoedens.supabase.co/auth/v1/admin/users/{created_user_id}", headers=headers, verify=False)
        print("Cleanup completed successfully.")

    print("\n==========================================")
    print("ALL AUTHENTICATION TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
