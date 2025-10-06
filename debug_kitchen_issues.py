import requests
import sqlite3
import json

BASE_URL = "http://localhost:5000"

def login():
    """Login and return session"""
    session = requests.Session()
    
    # Login
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        return session
    else:
        print("❌ Login failed")
        return None

def check_kitchen_setting():
    """Check current kitchen printing setting"""
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT value FROM settings WHERE key = "enable_kitchen_print"')
    result = cursor.fetchone()
    
    if result:
        print(f"Current kitchen printing setting: {result[0]}")
        return result[0]
    else:
        print("Kitchen printing setting not found")
        return None
    
    conn.close()

def toggle_kitchen_setting(session, enable):
    """Toggle kitchen printing setting"""
    data = {
        'restaurant_name': 'Test Restaurant',
        'enable_kitchen_print': 'true' if enable else 'false'
    }
    
    response = session.post(f"{BASE_URL}/api/settings/restaurant", data=data)
    if response.status_code == 200:
        print(f"✅ Kitchen printing setting updated to: {enable}")
        return True
    else:
        print(f"❌ Failed to update kitchen printing setting: {response.text}")
        return False

def create_order_and_test(session, table_id):
    """Create an order and test kitchen printing"""
    # Get menu items
    response = session.get(f"{BASE_URL}/api/menu-items")
    menu_items = response.json()
    
    # Find food and drink items
    food_item = None
    drink_item = None
    
    for item in menu_items:
        if item['category'].lower() in ['food', 'main', 'appetizer']:
            food_item = item
        elif item['category'].lower() in ['drink', 'drinks', 'beverage']:
            drink_item = item
    
    if not food_item or not drink_item:
        print("❌ Could not find both food and drink items")
        return None
    
    # Create order
    order_data = {
        'table_id': table_id,
        'waiter_id': 1,
        'total_amount': food_item['price'],  # Add total_amount
        'items': [
            {
                'menu_item_id': food_item['id'],
                'quantity': 1,
                'price': food_item['price']
            }
        ]
    }
    
    response = session.post(f"{BASE_URL}/api/orders", 
                          headers={'Content-Type': 'application/json'},
                          data=json.dumps(order_data))
    
    if response.status_code == 200:
        order_id = response.json()['order_id']
        print(f"✅ Order {order_id} created for table {table_id}")
        return order_id
    else:
        print(f"❌ Failed to create order: {response.text}")
        return None

def add_items_to_existing_order(session, table_id):
    """Add more items to existing pending order"""
    # Get menu items
    response = session.get(f"{BASE_URL}/api/menu-items")
    menu_items = response.json()
    
    # Find another food item
    food_item = None
    for item in menu_items:
        if item['category'].lower() in ['food', 'main', 'appetizer']:
            food_item = item
            break
    
    if not food_item:
        print("❌ Could not find food item")
        return None
    
    # Add to existing order
    order_data = {
        'table_id': table_id,
        'waiter_id': 1,
        'force_add': True,  # Force adding to existing order
        'total_amount': food_item['price'] * 2,  # Add total_amount
        'items': [
            {
                'menu_item_id': food_item['id'],
                'quantity': 2,
                'price': food_item['price']
            }
        ]
    }
    
    response = session.post(f"{BASE_URL}/api/orders", 
                          headers={'Content-Type': 'application/json'},
                          data=json.dumps(order_data))
    
    if response.status_code == 200:
        order_id = response.json()['order_id']
        print(f"✅ Items added to order {order_id} for table {table_id}")
        return order_id
    else:
        print(f"❌ Failed to add items: {response.text}")
        return None

def check_order_items_status(order_id):
    """Check kitchen_printed status of order items"""
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT oi.id, mi.name, oi.quantity, oi.kitchen_printed, mi.category
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        ORDER BY oi.id
    ''', (order_id,))
    
    items = cursor.fetchall()
    print(f"\nOrder {order_id} items:")
    for item in items:
        print(f"  - {item[1]} (qty: {item[2]}, kitchen_printed: {item[3]}, category: {item[4]})")
    
    conn.close()
    return items

def main():
    print("🔍 Debugging Kitchen Printing Issues")
    print("=" * 50)
    
    # Login
    session = login()
    if not session:
        return
    
    # Check current setting
    current_setting = check_kitchen_setting()
    
    # Test 1: Kitchen printing toggle behavior
    print("\n📋 Test 1: Kitchen Printing Toggle")
    print("-" * 30)
    
    # Enable kitchen printing
    toggle_kitchen_setting(session, True)
    check_kitchen_setting()
    
    # Create first order
    print("\n🍽️ Creating first order...")
    order_id1 = create_order_and_test(session, 15)  # Use different table
    if order_id1:
        check_order_items_status(order_id1)
    
    # Add items to existing order
    print("\n➕ Adding items to existing order...")
    order_id2 = add_items_to_existing_order(session, 15)  # Same table
    if order_id2:
        check_order_items_status(order_id2)
    
    # Test 2: Disable kitchen printing and test
    print("\n📋 Test 2: Disabled Kitchen Printing")
    print("-" * 30)
    
    toggle_kitchen_setting(session, False)
    check_kitchen_setting()
    
    # Create order with disabled setting
    print("\n🍽️ Creating order with disabled kitchen printing...")
    order_id3 = create_order_and_test(session, 16)  # Use different table
    if order_id3:
        check_order_items_status(order_id3)

if __name__ == "__main__":
    main()