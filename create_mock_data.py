import sqlite3
import uuid
from faker import Faker

fake = Faker()

# Connect to SQLite database (creates crm.db file)
conn = sqlite3.connect("crm.db")
cursor = conn.cursor()

# Create customers table
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    total_orders INTEGER,
    returns_last_12m INTEGER,
    lifetime_value REAL
)
""")

# Insert 15 fake customers
for _ in range(15):
    customer_id = str(uuid.uuid4())[:8]
    name = fake.name()
    email = fake.email()
    total_orders = fake.random_int(min=1, max=50)
    returns_last_12m = fake.random_int(min=0, max=10)
    lifetime_value = round(fake.random_number(digits=4), 2)
    
    cursor.execute("""
    INSERT INTO customers (customer_id, name, email, total_orders, returns_last_12m, lifetime_value)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (customer_id, name, email, total_orders, returns_last_12m, lifetime_value))

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM customers")
count = cursor.fetchone()[0]
print(f"✅ Inserted {count} customer records into crm.db")

# Show first 5 records as sample
cursor.execute("SELECT * FROM customers LIMIT 5")
print("\nSample records:")
for row in cursor.fetchall():
    print(row)

conn.close()