import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
print(f"Connecting to DB...")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    cur.execute("UPDATE auth.users SET email_confirmed_at = now() WHERE email_confirmed_at IS NULL;")
    print(f"Updated {cur.rowcount} users in auth.users")
    conn.commit()
    
    cur.execute("UPDATE users SET email_verified = true WHERE email_verified = false;")
    print(f"Updated {cur.rowcount} users in public.users")
    conn.commit()
    
    cur.close()
    conn.close()
except Exception as e:
    print("Error:", e)
