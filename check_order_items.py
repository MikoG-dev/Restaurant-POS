import sqlite3

conn = sqlite3.connect('restaurant.db')
conn.row_factory = sqlite3.Row

# Check the last few orders
orders = conn.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 3').fetchall()
for order in orders:
    print(f'Order {order["id"]}: Table {order["table_id"]}')
    items = conn.execute('''
        SELECT oi.*, mi.name, mi.category, oi.kitchen_printed
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order['id'],)).fetchall()
    for item in items:
        print(f'  - {item["name"]} ({item["category"]}) - kitchen_printed: {item["kitchen_printed"]}')
    print()

conn.close()