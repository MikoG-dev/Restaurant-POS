import sqlite3

conn = sqlite3.connect('restaurant.db')
cursor = conn.cursor()

# Check kitchen printing settings
cursor.execute('SELECT key, value FROM settings WHERE key LIKE "%kitchen%" OR key LIKE "%print%"')
settings = cursor.fetchall()

print('Kitchen/Printer related settings:')
for setting in settings:
    print(f'  {setting[0]}: {setting[1]}')

# If no kitchen print setting exists, create it
if not any('enable_kitchen_print' in setting[0] for setting in settings):
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('enable_kitchen_print', 'true'))
    conn.commit()
    print('\nEnabled kitchen printing (was not set)')
else:
    # Ensure it's enabled
    cursor.execute('UPDATE settings SET value = ? WHERE key = ?', ('true', 'enable_kitchen_print'))
    conn.commit()
    print('\nKitchen printing is enabled')

# Also check if printer settings exist
printer_settings = [
    ('printer_name', 'Kitchen Printer'),
    ('printer_paper_width', '32'),
    ('printer_use_escpos', 'true')
]

for key, default_value in printer_settings:
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    if not result:
        cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?)', (key, default_value))
        print(f'Added default setting: {key} = {default_value}')

conn.commit()
conn.close()
print('\nAll printer settings are configured.')