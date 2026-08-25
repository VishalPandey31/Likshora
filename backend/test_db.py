import sqlite3

def check_db():
    conn = sqlite3.connect('instance/likshora.db')
    c = conn.cursor()
    c.execute("SELECT id, user_id, order_number, order_status FROM orders ORDER BY id DESC LIMIT 5;")
    orders = c.fetchall()
    print("Latest Orders:")
    for o in orders:
        print(o)

    c.execute("SELECT id, email, role FROM users;")
    users = c.fetchall()
    print("\nUsers:")
    for u in users:
        print(u)
        
    conn.close()

if __name__ == '__main__':
    check_db()
a