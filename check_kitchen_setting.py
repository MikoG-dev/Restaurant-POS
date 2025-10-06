import sqlite3

# Connect to database
conn = sqlite3.connect('restaurant.db')
conn.row_factory = sqlite3.Row

# Check kitchen printing setting
result = conn.execute('SELECT key, value FROM settings WHERE key = ?', ('enable_kitchen_print',)).fetchone()

if result:
    print(f"Key: {result['key']}")
    print(f"Value: '{result['value']}'")
    print(f"Type: {type(result['value'])}")
    print(f"Value == 'true': {result['value'] == 'true'}")
    print(f"Value != 'true': {result['value'] != 'true'}")
else:
    print("Setting 'enable_kitchen_print' not found in database")

conn.close()