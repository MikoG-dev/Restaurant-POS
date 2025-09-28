import sqlite3
from datetime import datetime

conn = sqlite3.connect('restaurant.db')
cursor = conn.cursor()

cursor.execute('SELECT id, created_at FROM orders ORDER BY id DESC LIMIT 5')
print('Recent orders:')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Created: {row[1]}')

print(f'\nCurrent local time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

conn.close()