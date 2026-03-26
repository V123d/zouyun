import sqlite3
import os

db_path = r'd:\zouyun\backend\app\data\app.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

import json

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Check standard_quotas data
if ('standard_quotas',) in [t for t in tables]:
    cursor.execute("SELECT * FROM standard_quotas")
    rows = cursor.fetchall()
    print("\nStandard Quotas Data:")
    for row in rows:
        id, class_type, quotas_json = row
        quotas = json.loads(quotas_json)
        print(f"\n--- {class_type} ---")
        print(f"Categories ({len(quotas)}): {list(quotas.keys())}")
        for k, v in quotas.items():
            print(f"  {k}: {v}g")
else:
    print("\nTable 'standard_quotas' not found!")

conn.close()
