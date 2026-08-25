import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://likshora-api.onrender.com"
EMAIL = "karanrajput.officials@gmail.com"
PASSWORD = "Karan@2026"

SUPABASE_URL = dict(os.environ).get("SUPABASE_URL") or "https://sarebabwvlfpakoedens.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = dict(os.environ).get("SUPABASE_SERVICE_ROLE_KEY")
head = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

print("Attempting to CREATE user via Admin API forcefully...")
res = requests.post(f"{SUPABASE_URL}/auth/v1/admin/users", headers=head, json={
    "email": EMAIL,
    "password": PASSWORD,
    "email_confirm": True
})
print("Result Status:", res.status_code)
print(res.text)

if res.status_code == 422: # Already exists?
    print("User already exists. Finding their ID across all pages...")
    found = False
    for page in range(1, 10):
        url = f"{SUPABASE_URL}/auth/v1/admin/users?page={page}&per_page=50"
        page_res = requests.get(url, headers=head)
        users = page_res.json().get("users", [])
        if not users:
            break
        for u in users:
            if u.get("email") == EMAIL:
                target_uid = u.get("id")
                print(f"FOUND ID: {target_uid}")
                
                # Update password
                upd_res = requests.put(f"{SUPABASE_URL}/auth/v1/admin/users/{target_uid}", headers=head, json={"password": PASSWORD, "email_confirm": True})
                print("Update password response:", upd_res.status_code)
                
                # Update local DB role
                from app import create_app
                from app.extensions import db
                from app.models import User
                app = create_app()
                with app.app_context():
                    local_user = User.query.filter_by(email=EMAIL).first()
                    if local_user:
                        local_user.id = target_uid
                        local_user.supabase_uid = target_uid
                        local_user.role = "admin"
                        db.session.commit()
                        print("Synced to Local DB Successfully!")
                found = True
                break
        if found:
            break
    if not found:
        print("COULD NOT FIND THE USER IN ANY PAGE!")
elif res.status_code < 300:
    uid = res.json().get("id")
    print("CREATED SUCCESSFULLY WITH ID:", uid)
    # Update local DB role
    from app import create_app
    from app.extensions import db
    from app.models import User
    app = create_app()
    with app.app_context():
        local_user = User.query.filter_by(email=EMAIL).first()
        if local_user:
            local_user.id = uid
            local_user.supabase_uid = uid
            local_user.role = "admin"
            db.session.commit()
            print("Synced to Local DB Successfully!")
