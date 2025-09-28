from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
import json
import uuid

app = Flask(__name__)
app.secret_key = 'restaurant_cashier_secret_key_2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

DATABASE = 'restaurant.db'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'cashier',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add role column to existing users table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "cashier"')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Menu items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tables table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number INTEGER UNIQUE NOT NULL,
            active INTEGER DEFAULT 1
        )
    ''')
    
    # Waiters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add phone column to existing waiters table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE waiters ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER,
            waiter_id INTEGER,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            session_id TEXT,
            is_final_bill INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES tables (id),
            FOREIGN KEY (waiter_id) REFERENCES waiters (id)
        )
    ''')
    
    # Add new columns to existing orders table if they don't exist
    try:
        cursor.execute('ALTER TABLE orders ADD COLUMN session_id TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE orders ADD COLUMN is_final_bill INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE orders ADD COLUMN closed_at TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    # Order items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            menu_item_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        )
    ''')
    
    # Add timestamp column to existing order_items table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE order_items ADD COLUMN added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash',
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user if not exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash('admin123')
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      ('admin', password_hash))
    
    # Create default tables (1-20)
    for i in range(1, 21):
        cursor.execute('INSERT OR IGNORE INTO tables (table_number) VALUES (?)', (i,))
    
    # Create default waiters
    default_waiters = ['John Doe', 'Jane Smith', 'Mike Johnson']
    for waiter in default_waiters:
        cursor.execute('INSERT OR IGNORE INTO waiters (name) VALUES (?)', (waiter,))
    
    # Create sample menu items
    sample_items = [
        ('Burger', 'food', 12.99),
        ('Pizza', 'food', 18.50),
        ('Pasta', 'food', 14.75),
        ('Salad', 'food', 9.99),
        ('Coca Cola', 'drink', 2.99),
        ('Coffee', 'drink', 3.50),
        ('Orange Juice', 'drink', 4.25),
        ('Water', 'drink', 1.99)
    ]
    
    for name, category, price in sample_items:
        cursor.execute('INSERT OR IGNORE INTO menu_items (name, category, price) VALUES (?, ?, ?)', 
                      (name, category, price))
    
    # Create default settings
    default_settings = [
        ('restaurant_name', 'The Golden Fork'),
        ('restaurant_phone', '+1 (555) 123-4567'),
        ('restaurant_address', '123 Main Street\nDowntown City, State 12345'),
        ('tax_rate', '8.25'),
        ('currency', 'USD')
    ]
    
    for key, value in default_settings:
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/pos')
@login_required
def pos():
    return render_template('pos.html')

@app.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

@app.route('/orders')
@login_required
def orders():
    return render_template('orders.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# API Routes
@app.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    conn = get_db_connection()
    
    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Today's orders count
    today_orders = conn.execute('''
        SELECT COUNT(*) as count FROM orders 
        WHERE DATE(created_at) = ?
    ''', (today,)).fetchone()['count']
    
    # Today's revenue
    today_revenue = conn.execute('''
        SELECT COALESCE(SUM(p.total_amount), 0) as revenue 
        FROM payments p
        JOIN orders o ON p.order_id = o.id
        WHERE DATE(o.created_at) = ?
    ''', (today,)).fetchone()['revenue']
    
    # Active tables (tables with pending orders)
    active_tables = conn.execute('''
        SELECT COUNT(DISTINCT table_id) as count 
        FROM orders 
        WHERE status = 'pending'
    ''').fetchone()['count']
    
    # Total items sold today
    total_items_sold = conn.execute('''
        SELECT COALESCE(SUM(oi.quantity), 0) as total_items
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) = ?
    ''', (today,)).fetchone()['total_items']
    
    # Orders per hour calculation (today's orders divided by hours since start of day)
    current_time = datetime.now()
    start_of_day = datetime.combine(current_time.date(), datetime.min.time())
    hours_elapsed = max(1, (current_time - start_of_day).total_seconds() / 3600)  # At least 1 hour to avoid division by zero
    orders_per_hour = today_orders / hours_elapsed
    
    # Sales data for last 7 days
    sales_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        revenue = conn.execute('''
            SELECT COALESCE(SUM(p.total_amount), 0) as revenue 
            FROM payments p
            JOIN orders o ON p.order_id = o.id
            WHERE DATE(o.created_at) = ?
        ''', (date,)).fetchone()['revenue']
        sales_data.append(float(revenue))
    
    # Top items today
    top_items = conn.execute('''
        SELECT mi.name, SUM(oi.quantity) as quantity
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) = ?
        GROUP BY mi.id, mi.name
        ORDER BY quantity DESC
        LIMIT 5
    ''', (today,)).fetchall()
    
    # Recent orders
    recent_orders = conn.execute('''
        SELECT o.id, o.total_amount, o.status, o.created_at,
               t.table_number, w.name as waiter_name,
               COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN waiters w ON o.waiter_id = w.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE DATE(o.created_at) = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
        LIMIT 10
    ''', (today,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'todayOrders': today_orders,
        'todayRevenue': float(today_revenue),
        'totalItemsSold': int(total_items_sold),
        'ordersPerHour': float(orders_per_hour),
        'activeTables': active_tables,
        'salesData': sales_data,
        'topItems': [{'name': item['name'], 'quantity': item['quantity']} for item in top_items],
        'recentOrders': [dict(order) for order in recent_orders]
    })

@app.route('/api/menu-items')
@login_required
def api_menu_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM menu_items WHERE active = 1 ORDER BY category, name').fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

@app.route('/api/menu-items', methods=['POST'])
@login_required
def api_add_menu_item():
    data = request.get_json()
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO menu_items (name, category, price)
        VALUES (?, ?, ?)
    ''', (data['name'], data['category'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/menu-items/<int:item_id>', methods=['PUT'])
@login_required
def api_update_menu_item(item_id):
    data = request.get_json()
    conn = get_db_connection()
    conn.execute('''
        UPDATE menu_items 
        SET name = ?, category = ?, price = ?
        WHERE id = ?
    ''', (data['name'], data['category'], data['price'], item_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/menu-items/<int:item_id>', methods=['DELETE'])
@login_required
def api_delete_menu_item(item_id):
    conn = get_db_connection()
    conn.execute('UPDATE menu_items SET active = 0 WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/tables')
@login_required
def api_tables():
    conn = get_db_connection()
    tables = conn.execute('SELECT * FROM tables WHERE active = 1 ORDER BY table_number').fetchall()
    conn.close()
    return jsonify([dict(table) for table in tables])

@app.route('/api/waiters')
@login_required
def api_waiters():
    conn = get_db_connection()
    waiters = conn.execute('SELECT * FROM waiters WHERE active = 1 ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(waiter) for waiter in waiters])

@app.route('/api/orders', methods=['POST'])
@login_required
def api_create_order():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    table_id = data['table_id']
    waiter_id = data['waiter_id']
    
    # Check if there's an existing pending order for this table
    existing_order = conn.execute('''
        SELECT id, waiter_id FROM orders 
        WHERE table_id = ? AND status = 'pending' AND is_final_bill = 0
        ORDER BY created_at DESC LIMIT 1
    ''', (table_id,)).fetchone()
    
    if existing_order:
        # Check if it's the same waiter or if force_add flag is set
        force_add = data.get('force_add', False)
        
        if existing_order['waiter_id'] != waiter_id and not force_add:
            # Get waiter names for better error message
            current_waiter = conn.execute('SELECT name FROM waiters WHERE id = ?', (existing_order['waiter_id'],)).fetchone()
            new_waiter = conn.execute('SELECT name FROM waiters WHERE id = ?', (waiter_id,)).fetchone()
            
            conn.close()
            return jsonify({
                'error': f'Table {table_id} is currently assigned to {current_waiter["name"] if current_waiter else "another waiter"}. You ({new_waiter["name"] if new_waiter else "current waiter"}) can still add items to this table.',
                'warning': True,
                'existing_waiter': current_waiter['name'] if current_waiter else 'Unknown',
                'current_waiter': new_waiter['name'] if new_waiter else 'Unknown',
                'table_id': table_id,
                'can_force': True
            }), 409  # Conflict status code instead of 400
        
        # Add items to existing order (either same waiter or forced)
        order_id = existing_order['id']
        
        # Add new items to the existing order
        for item in data['items']:
            cursor.execute('''
                INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['menu_item_id'], item['quantity'], item['price']))
        
        # Update total amount
        new_total = conn.execute('''
            SELECT SUM(oi.quantity * oi.price) as total
            FROM order_items oi
            WHERE oi.order_id = ?
        ''', (order_id,)).fetchone()['total']
        
        cursor.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (new_total, order_id))
        
    else:
        # Create new order with session ID for grouping
        import uuid
        session_id = str(uuid.uuid4())
        
        # Use local datetime instead of SQLite's CURRENT_TIMESTAMP (which uses UTC)
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO orders (table_id, waiter_id, total_amount, status, session_id, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
        ''', (table_id, waiter_id, data['total_amount'], session_id, local_time))
        
        order_id = cursor.lastrowid
        
        # Add order items
        for item in data['items']:
            cursor.execute('''
                INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['menu_item_id'], item['quantity'], item['price']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/orders/<int:order_id>/pay', methods=['POST'])
@login_required
def api_pay_order(order_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get order details
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    
    # If this is a table order, we need to finalize all pending orders for this table
    if order['table_id']:
        # Get all pending orders for this table
        pending_orders = conn.execute('''
            SELECT id, total_amount FROM orders 
            WHERE table_id = ? AND status = 'pending'
        ''', (order['table_id'],)).fetchall()
        
        # Calculate total amount for all pending orders
        total_bill = sum(order['total_amount'] for order in pending_orders)
        
        # Use local datetime for consistency
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mark all orders as paid
        for pending_order in pending_orders:
            cursor.execute('UPDATE orders SET status = ?, closed_at = ? WHERE id = ?', 
                         ('paid', local_time, pending_order['id']))
        
        # Create a single payment record for the entire bill
        cursor.execute('''
            INSERT INTO payments (order_id, total_amount, payment_method, paid_at)
            VALUES (?, ?, ?, ?)
        ''', (order_id, total_bill, data.get('payment_method', 'cash'), local_time))
        
    else:
        # Single order payment (fallback for individual orders)
        cursor.execute('UPDATE orders SET status = ?, closed_at = ? WHERE id = ?', 
                     ('paid', local_time, order_id))
        
        cursor.execute('''
            INSERT INTO payments (order_id, total_amount, payment_method, paid_at)
            VALUES (?, ?, ?, ?)
        ''', (order_id, data['total_amount'], data.get('payment_method', 'cash'), local_time))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/orders/table/<int:table_id>/pay', methods=['POST'])
@login_required
def api_pay_table_orders(table_id):
    """Process payment for all pending orders at a specific table"""
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all pending orders for this table
        pending_orders = conn.execute('''
            SELECT id, total_amount, waiter_id FROM orders 
            WHERE table_id = ? AND status = 'pending'
            ORDER BY created_at ASC
        ''', (table_id,)).fetchall()
        
        if not pending_orders:
            conn.close()
            return jsonify({'error': 'No pending orders found for this table'}), 404
        
        # Calculate total amount for all pending orders
        total_bill = sum(order['total_amount'] for order in pending_orders)
        
        # Use local datetime for consistency
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mark all orders as paid and set final bill flag
        for i, pending_order in enumerate(pending_orders):
            is_final_bill = 1 if i == len(pending_orders) - 1 else 0  # Mark last order as final bill
            cursor.execute('''
                UPDATE orders 
                SET status = ?, closed_at = ?, is_final_bill = ?
                WHERE id = ?
            ''', ('paid', local_time, is_final_bill, pending_order['id']))
        
        # Create a single payment record for the entire bill (linked to the last order)
        last_order_id = pending_orders[-1]['id']
        cursor.execute('''
            INSERT INTO payments (order_id, total_amount, payment_method, paid_at)
            VALUES (?, ?, ?, ?)
        ''', (last_order_id, total_bill, data.get('payment_method', 'cash'), local_time))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'total_amount': total_bill,
            'orders_count': len(pending_orders),
            'payment_method': data.get('payment_method', 'cash')
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Payment processing failed: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/api/orders')
@login_required
def api_orders():
    # Get pagination parameters with validation
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
    except ValueError:
        # If conversion fails, use defaults
        page = 1
        per_page = 25
    
    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 25
    if per_page > 100:  # Limit maximum per_page to prevent performance issues
        per_page = 100
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    table_filter = request.args.get('table', '')
    waiter_filter = request.args.get('waiter', '')
    date_filter = request.args.get('date', '')
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'DESC')
    
    # Validate sort parameters
    valid_sort_columns = ['id', 'created_at', 'total_amount', 'status', 'table_number', 'waiter_name']
    if sort_by not in valid_sort_columns:
        sort_by = 'created_at'
    
    if sort_order.upper() not in ['ASC', 'DESC']:
        sort_order = 'DESC'
    
    # Validate per_page limits
    if per_page > 100:
        per_page = 100
    elif per_page < 1:
        per_page = 25
    
    conn = get_db_connection()
    
    # Build WHERE clause for filters
    where_conditions = []
    params = []
    
    if status_filter:
        where_conditions.append('o.status = ?')
        params.append(status_filter)
    
    if table_filter:
        where_conditions.append('t.table_number = ?')
        params.append(int(table_filter))
    
    if waiter_filter:
        where_conditions.append('w.id = ?')
        params.append(int(waiter_filter))
    
    if date_filter:
        where_conditions.append('DATE(o.created_at) = ?')
        params.append(date_filter)
    
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    # Get total count for pagination
    count_query = f'''
        SELECT COUNT(DISTINCT o.id) as total
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN waiters w ON o.waiter_id = w.id
        {where_clause}
    '''
    
    total_orders = conn.execute(count_query, params).fetchone()['total']
    total_pages = (total_orders + per_page - 1) // per_page  # Ceiling division
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Map sort columns to their table aliases
    sort_column_map = {
        'id': 'o.id',
        'created_at': 'o.created_at',
        'total_amount': 'o.total_amount',
        'status': 'o.status',
        'table_number': 't.table_number',
        'waiter_name': 'w.name'
    }
    
    order_by_column = sort_column_map.get(sort_by, 'o.created_at')
    
    # Build main query with pagination
    main_query = f'''
        SELECT o.id, o.table_id, o.waiter_id, o.total_amount as total, 
               o.status, o.created_at as timestamp,
               t.table_number, w.name as waiter_name, w.id as waiter_id_alias,
               COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN waiters w ON o.waiter_id = w.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        {where_clause}
        GROUP BY o.id, o.table_id, o.waiter_id, o.total_amount, o.status, o.created_at, t.table_number, w.name, w.id
        ORDER BY {order_by_column} {sort_order}
        LIMIT ? OFFSET ?
    '''
    
    # Add pagination parameters to params
    params.extend([per_page, offset])
    
    orders = conn.execute(main_query, params).fetchall()
    conn.close()
    
    return jsonify({
        'orders': [dict(order) for order in orders],
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_orders': total_orders,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    })

@app.route('/api/orders/<int:order_id>')
@login_required
def api_order_details(order_id):
    conn = get_db_connection()
    
    # Get order details
    order = conn.execute('''
        SELECT o.id, o.table_id, o.waiter_id, o.total_amount as total, 
               o.status, o.created_at as timestamp,
               t.table_number, w.name as waiter_name
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN waiters w ON o.waiter_id = w.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    
    # Get order items
    items = conn.execute('''
        SELECT oi.quantity, oi.price, mi.name, mi.category
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    conn.close()
    
    if order:
        order_dict = dict(order)
        order_dict['items'] = [dict(item) for item in items]
        return jsonify(order_dict)
    else:
        return jsonify({'error': 'Order not found'}), 404

@app.route('/api/print-receipt/<int:order_id>')
@login_required
def api_print_receipt(order_id):
    conn = get_db_connection()
    
    # Get restaurant settings
    settings = {}
    settings_rows = conn.execute('SELECT key, value FROM settings').fetchall()
    for row in settings_rows:
        settings[row['key']] = row['value']
    
    # Get order details
    order = conn.execute('''
        SELECT o.*, t.table_number, w.name as waiter_name
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN waiters w ON o.waiter_id = w.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    
    # Get order items
    items = conn.execute('''
        SELECT oi.*, mi.name as item_name
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    conn.close()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Generate HTML receipt content with dynamic restaurant information
    receipt_html = []
    receipt_html.append('<div class="receipt-content">')
    
    # Add logo image if logo exists - centered at top
    if settings.get('restaurant_logo'):
        logo_url = settings.get('restaurant_logo')
        receipt_html.append(f'<div class="logo-container" style="text-align: center; margin: 5px 0 10px 0;">')
        receipt_html.append(f'<img src="{logo_url}" alt="Restaurant Logo" style="max-width: 120px; max-height: 60px; object-fit: contain;">')
        receipt_html.append('</div>')
    
    # Header section - centered
    receipt_html.append('<div class="receipt-header" style="text-align: center; margin-bottom: 10px;">')
    receipt_html.append(f'<div style="font-weight: bold; font-size: 14px; margin-bottom: 2px;">{settings.get("restaurant_name", "RESTAURANT POS")}</div>')
    receipt_html.append(f'<div style="font-size: 11px; line-height: 1.2;">{settings.get("restaurant_address", "123 Main Street<br>City, State 12345")}</div>')
    receipt_html.append(f'<div style="font-size: 11px;">Phone: {settings.get("restaurant_phone", "(555) 123-4567")}</div>')
    receipt_html.append('</div>')
    
    # Receipt title and order info
    receipt_html.append('<div style="text-align: center; font-weight: bold; margin: 10px 0 5px 0; font-size: 14px;">RECEIPT</div>')
    receipt_html.append('<div class="receipt-body" style="font-size: 11px; line-height: 1.3;">')
    receipt_html.append(f'Cashier: {order["waiter_name"] or "Unassigned"}<br>')
    receipt_html.append(f'Table: {order["table_number"] or "N/A"}<br>')
    
    # Items section
    total = 0
    for item in items:
        item_total = item['quantity'] * item['price']
        total += item_total
        # Item name on first line
        receipt_html.append(f'<div style="margin: 3px 0;"><strong>{item["item_name"]}</strong></div>')
        # Quantity and price details on second line with right-aligned total
        receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin-left: 10px; margin-bottom: 2px;"><span>{item["quantity"]:.2f} x {item["price"]:.2f} Br</span><span style="font-weight: bold;">{item_total:.2f} Br</span></div>')
    
    # Add tax calculation if tax rate is set
    tax_rate = float(settings.get('tax_rate', 0)) / 100 if settings.get('tax_rate') else 0
    if tax_rate > 0:
        tax_amount = total * tax_rate
        receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin: 5px 0;"><span>Subtotal:</span><span style="font-weight: bold;">{total:.2f} Br</span></div>')
        receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin: 2px 0;"><span>Tax ({settings.get("tax_rate", 0)}%):</span><span style="font-weight: bold;">{tax_amount:.2f} Br</span></div>')
        total += tax_amount
    
    # Total section with emphasis
    receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin: 8px 0 5px 0; font-size: 13px; font-weight: bold; border-top: 1px dashed #000; padding-top: 5px;"><span>TOTAL</span><span>{total:.2f} Br</span></div>')
    
    # Footer section
    receipt_html.append('<div class="receipt-footer" style="text-align: center; margin-top: 15px; font-size: 12px; font-weight: bold;">')
    receipt_html.append('THANK YOU')
    receipt_html.append('</div>')
    
    # Company info footer
    receipt_html.append('<div style="text-align: center; font-size: 9px; margin-top: 10px; line-height: 1.2;">')
    receipt_html.append('Developed by Miko<br>')
    receipt_html.append('0933245672<br>')
    # receipt_html.append('09320385599<br>')
    # receipt_html.append('CBE:1000601921034<br>')
    receipt_html.append(f'Order {order["id"]}<br>')
    receipt_html.append(f'{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    receipt_html.append('</div>')
    
    # Add payment options if bank accounts are configured
    payment_options = []
    if settings.get('cbe_account'):
        payment_options.append(f"CBE Bank: {settings.get('cbe_account')}")
    if settings.get('telebirr_account'):
        payment_options.append(f"Telebirr: {settings.get('telebirr_account')}")
    
    if payment_options:
        receipt_html.append('<div style="text-align: center; margin-top: 10px; font-size: 10px;">')
        receipt_html.append('<strong>PAYMENT OPTIONS:</strong><br>')
        for option in payment_options:
            receipt_html.append(f'{option}<br>')
        receipt_html.append('</div>')
    
    receipt_html.append('</div>')
    receipt_html.append('</div>')
    
    return jsonify({
        'success': True,
        'receipt': ''.join(receipt_html)
    })

@app.route('/api/orders/<int:order_id>/receipt')
@login_required
def api_order_receipt(order_id):
    """Get receipt content for a specific order"""
    conn = get_db_connection()
    
    # Get restaurant settings
    settings = {}
    settings_rows = conn.execute('SELECT key, value FROM settings').fetchall()
    for row in settings_rows:
        settings[row['key']] = row['value']
    
    # Get order details
    order = conn.execute('''
        SELECT o.*, t.table_number, w.name as waiter_name
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        LEFT JOIN waiters w ON o.waiter_id = w.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    
    # Get order items
    items = conn.execute('''
        SELECT oi.*, mi.name as item_name
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    conn.close()
    
    if not order:
        return "Order not found", 404
    
    # Generate HTML receipt content with dynamic restaurant information
    receipt_html = []
    receipt_html.append('<div class="receipt-content">')
    
    # Add logo image if logo exists - centered at top
    if settings.get('restaurant_logo'):
        logo_url = settings.get('restaurant_logo')
        receipt_html.append(f'<div class="logo-container" style="text-align: center; margin: 5px 0 10px 0;">')
        receipt_html.append(f'<img src="{logo_url}" alt="Restaurant Logo" style="max-width: 120px; max-height: 60px; object-fit: contain;">')
        receipt_html.append('</div>')
    
    # Header section - centered
    receipt_html.append('<div class="receipt-header" style="text-align: center; margin-bottom: 10px;">')
    receipt_html.append(f"<div style='font-weight: bold; font-size: 14px; margin-bottom: 2px;'>{settings.get('restaurant_name', 'RESTAURANT POS')}</div>")
    receipt_html.append(f"<div style='font-size: 11px; line-height: 1.2;'>{settings.get('restaurant_address', '123 Main Street<br>City, State 12345')}</div>")
    receipt_html.append(f"<div style='font-size: 11px;'>Phone: {settings.get('restaurant_phone', '(555) 123-4567')}</div>")
    receipt_html.append('</div>')
    
    # Receipt title and order info - left aligned
    receipt_html.append('<div style="text-align: center; font-weight: bold; margin: 1px 0 2px 0; font-size: 14px;">RECEIPT</div>')
    receipt_html.append('<div class="receipt-body" style="font-size: 11px; line-height: 1.3;">')
    receipt_html.append(f"Cashier: {order['waiter_name'] or 'Unassigned'}<br>")
    receipt_html.append(f"Table: {order['table_number'] or 'N/A'}<br>")
    
    # Items section
    total = 0
    for item in items:
        item_total = item['quantity'] * item['price']
        total += item_total
        # Item name on first line
        receipt_html.append(f"<div style='margin: 3px 0;'><strong>{item['item_name']}</strong></div>")
        # Quantity and price details on second line with right-aligned total
        receipt_html.append(f"<div style='display: flex; justify-content: space-between; margin-left: 10px; margin-bottom: 2px;'><span>{item['quantity']:.2f} x {item['price']:.2f} Br</span><span style='font-weight: bold;'>{item_total:.2f} Br</span></div>")
    
    # Add tax calculation if tax rate is set
    tax_rate = float(settings.get('tax_rate', 0)) / 100 if settings.get('tax_rate') else 0
    if tax_rate > 0:
        tax_amount = total * tax_rate
        receipt_html.append(f"<div style='display: flex; justify-content: space-between; margin: 5px 0;'><span>Subtotal:</span><span style='font-weight: bold;'>{total:.2f} Br</span></div>")
        receipt_html.append(f"<div style='display: flex; justify-content: space-between; margin: 2px 0;'><span>Tax ({settings.get('tax_rate', 0)}%):</span><span style='font-weight: bold;'>{tax_amount:.2f} Br</span></div>")
        total += tax_amount
    
    # Total section with emphasis
    receipt_html.append(f"<div style='display: flex; justify-content: space-between; margin: 8px 0 5px 0; font-size: 13px; font-weight: bold; border-top: 1px dashed #000; padding-top: 5px;'><span>TOTAL</span><span>{total:.2f} Br</span></div>")
    
    # Footer section
    receipt_html.append('<div class="receipt-footer" style="text-align: center; margin-top: 15px; font-size: 12px; font-weight: bold;">')
    receipt_html.append("THANK YOU")
    receipt_html.append('</div>')
    
    # Company info footer
    receipt_html.append('<div style="text-align: center; font-size: 9px; margin-top: 10px; line-height: 1.2;">')
    receipt_html.append("Developed by Miko<br>")
    receipt_html.append("0933245672<br>")
    # receipt_html.append("09320385599<br>")
    # receipt_html.append("CBE:1000601921034<br>")
    receipt_html.append(f"Order {order['id']}<br>")
    receipt_html.append(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    receipt_html.append('</div>')
    
    # Add payment options if bank accounts are configured
    payment_options = []
    if settings.get('cbe_account'):
        payment_options.append(f"CBE Bank: {settings.get('cbe_account')}")
    if settings.get('telebirr_account'):
        payment_options.append(f"Telebirr: {settings.get('telebirr_account')}")
    
    if payment_options:
        receipt_html.append('<div style="text-align: center; margin-top: 10px; font-size: 10px;">')
        receipt_html.append("<strong>PAYMENT OPTIONS:</strong><br>")
        for option in payment_options:
            receipt_html.append(f"{option}<br>")
        receipt_html.append('</div>')
    
    receipt_html.append('</div>')
    receipt_html.append('</div>')
    
    return ''.join(receipt_html)

@app.route('/api/tables/<int:table_id>/receipt')
@login_required
def api_table_receipt(table_id):
    """Get combined receipt for all pending orders at a table"""
    conn = get_db_connection()
    
    # Get restaurant settings
    settings = {}
    settings_rows = conn.execute('SELECT key, value FROM settings').fetchall()
    for row in settings_rows:
        settings[row['key']] = row['value']
    
    # Get table details
    table = conn.execute('SELECT * FROM tables WHERE id = ?', (table_id,)).fetchone()
    if not table:
        conn.close()
        return "Table not found", 404
    
    # Get all pending orders for this table
    orders = conn.execute('''
        SELECT o.*, w.name as waiter_name
        FROM orders o
        LEFT JOIN waiters w ON o.waiter_id = w.id
        WHERE o.table_id = ? AND o.status = 'pending'
        ORDER BY o.created_at ASC
    ''', (table_id,)).fetchall()
    
    if not orders:
        conn.close()
        return "No pending orders found for this table", 404
    
    # Generate HTML receipt content with dynamic restaurant information
    receipt_html = []
    receipt_html.append('<div class="receipt-content">')
    
    # Add logo image if logo exists - centered at top
    if settings.get('restaurant_logo'):
        logo_url = settings.get('restaurant_logo')
        receipt_html.append(f'<div class="logo-container" style="text-align: center; margin: 1px 0 1px 0;">')
        receipt_html.append(f'<img src="{logo_url}" alt="Restaurant Logo" style="max-width: 120px; max-height: 60px; object-fit: contain;">')
        receipt_html.append('</div>')
    
    # Header section - centered
    receipt_html.append('<div class="receipt-header" style="text-align: center; margin-bottom: 1px;">')
    receipt_html.append(f'<div style="font-weight: bold; font-size: 12px; margin-bottom: 2px;">{settings.get("restaurant_name", "RESTAURANT POS")}</div>')
    receipt_html.append(f'<div style="font-size: 11px; line-height: 1.2;">{settings.get("restaurant_address", "123 Main Street<br>City, State 12345")}</div>')
    receipt_html.append(f'<div style="font-size: 11px;">Phone: {settings.get("restaurant_phone", "(555) 123-4567")}</div>')
    receipt_html.append('</div>')
    
    # Receipt title and order info
    receipt_html.append('<div style="text-align: center; font-weight: bold; margin: 0px 0 1px 0; font-size: 12px;">RECEIPT</div>')
    receipt_html.append('<div class="receipt-body" style="font-size: 9px; line-height: 1.3;">')
    receipt_html.append(f'Cashier: {orders[0]["waiter_name"] if orders and orders[0]["waiter_name"] else "System"}<br>')
    receipt_html.append(f'Table: {table["table_number"]}<br>')
    
    receipt_html.append('<div class="receipt-body">')
    grand_total = 0
    
    for order in orders:
        # Get items for this order
        items = conn.execute('''
            SELECT oi.*, mi.name as item_name
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        
        receipt_html.append('<div style="margin: 1px 0; border-bottom: 1px dashed #000; padding-bottom: 2px;">')
        # receipt_html.append(f'<div style="font-size: 11px; font-weight: bold;">Order #{order["id"]} - {order["waiter_name"] or "Unassigned"}</div>')
        # receipt_html.append(f'<div style="font-size: 10px; margin: 2px 0;">Time: {order["created_at"]}</div>')
        
        order_total = 0
        for item in items:
            item_total = item['quantity'] * item['price']
            order_total += item_total
            # Item name on first line
            receipt_html.append(f'<div style="margin: 1px 0;"><strong>{item["item_name"]}</strong></div>')
            # Quantity and price details on second line with right-aligned total
            receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin-left: 10px; margin-bottom: 2px; font-size: 9px"><span>{item["quantity"]:.2f} x {item["price"]:.2f} Br</span><span style="font-weight: bold;">{item_total:.2f} Br</span></div>')
        
        # receipt_html.append(f'<div style="text-align: right; font-size: 11px; font-weight: bold; margin-top: 5px;">Order Total: {order_total:.2f} Br</div>')
        # receipt_html.append('</div>')
        grand_total += order_total
    
    # Add tax calculation if tax rate is set
    tax_rate = float(settings.get('tax_rate', 0)) / 100 if settings.get('tax_rate') else 0
    if tax_rate > 0:
        tax_amount = grand_total * tax_rate
        receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin: 1px 0;"><span>Subtotal:</span><span style="font-weight: bold;">{grand_total:.2f} Br</span></div>')
        receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin: 1px 0;"><span>Tax ({settings.get("tax_rate", 0)}%):</span><span style="font-weight: bold;">{tax_amount:.2f} Br</span></div>')
        grand_total += tax_amount
    
    # Total section with emphasis
    receipt_html.append(f'<div style="display: flex; justify-content: space-between; margin: 2px 0 1px 0; font-size: 14px; font-weight: bold; border-top: 1px dashed #000; padding-top: 3px;"><span>TOTAL</span><span>{grand_total:.2f} Br</span></div>')
    
    # Footer section
    receipt_html.append('<div class="receipt-footer" style="text-align: center; margin-top: 0px; font-size: 12px; font-weight: bold;">')
    receipt_html.append('THANK YOU')
    receipt_html.append('</div>')
    
    # Company info footer
    receipt_html.append('<div style="text-align: center; font-size: 9px; margin-top: 1px; line-height: 1.2;">')
    receipt_html.append('Developed by Miko<br>')
    receipt_html.append('0933245672<br>')
    # receipt_html.append(f"Order {order['id']}<br>")
    # receipt_html.append(f'Table {table["table_number"]} Orders: {len(orders)}<br>')
    receipt_html.append(f'Order #{order['id']} {datetime.now().strftime("%d/%m/%Y")}')
    receipt_html.append('</div>')
    
    # Add payment options if bank accounts are configured
    payment_options = []
    if settings.get('cbe_account'):
        payment_options.append(f"CBE Bank: {settings.get('cbe_account')}")
    if settings.get('telebirr_account'):
        payment_options.append(f"Telebirr: {settings.get('telebirr_account')}")
    
    if payment_options:
        receipt_html.append('<div style="text-align: center; margin-top: 1px; font-size: 10px;">')
        receipt_html.append('<strong>PAYMENT OPTIONS:</strong><br>')
        for option in payment_options:
            receipt_html.append(f'{option}<br>')
        receipt_html.append('</div>')
    
    receipt_html.append('</div>')
    receipt_html.append('</div>')
    
    conn.close()
    return ''.join(receipt_html)

# Settings API endpoints
@app.route('/api/settings/restaurant', methods=['POST'])
@login_required
def save_restaurant_settings():
    try:
        conn = get_db_connection()
        logo_url = None
        
        # Handle file upload if present
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                file_extension = logo_file.filename.rsplit('.', 1)[1].lower()
                
                if file_extension not in allowed_extensions:
                    return jsonify({'success': False, 'error': 'Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.'}), 400
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(app.static_folder, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                import uuid
                filename = f"logo_{uuid.uuid4().hex}.{file_extension}"
                filepath = os.path.join(upload_dir, filename)
                
                # Save the file
                logo_file.save(filepath)
                logo_url = f"/static/uploads/{filename}"
        
        # Get form data
        restaurant_name = request.form.get('restaurant_name')
        restaurant_phone = request.form.get('restaurant_phone')
        restaurant_address = request.form.get('restaurant_address')
        tax_rate = request.form.get('tax_rate')
        cbe_account = request.form.get('cbe_account')
        telebirr_account = request.form.get('telebirr_account')
        
        # Update restaurant settings
        settings_map = {
            'restaurant_name': restaurant_name,
            'restaurant_phone': restaurant_phone,
            'restaurant_address': restaurant_address,
            'tax_rate': tax_rate,
            'cbe_account': cbe_account,
            'telebirr_account': telebirr_account
        }
        
        # Add logo URL if uploaded
        if logo_url:
            settings_map['restaurant_logo'] = logo_url
        
        for key, value in settings_map.items():
            if value is not None:
                conn.execute('''
                    INSERT OR REPLACE INTO settings (key, value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
        
        conn.commit()
        conn.close()
        
        response_data = {'success': True, 'message': 'Restaurant settings saved successfully'}
        if logo_url:
            response_data['logo_url'] = logo_url
            
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/system', methods=['POST'])
@login_required
def save_system_settings():
    try:
        data = request.get_json()
        conn = get_db_connection()
        
        # Update system settings
        for key, value in data.items():
            conn.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, str(value)))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'System settings saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    try:
        conn = get_db_connection()
        
        settings_data = conn.execute('SELECT key, value FROM settings').fetchall()
        
        settings = {}
        for row in settings_data:
            settings[row['key']] = row['value']
        
        conn.close()
        
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Users API endpoints
@app.route('/api/users')
@login_required
def get_users():
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT id, username, role FROM users ORDER BY username').fetchall()
        conn.close()
        return jsonify([dict(user) for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'cashier')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                    (username, password_hash, role))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def edit_user(user_id):
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        conn = get_db_connection()
        
        # Update user information
        if password:
            # If password is provided, update it too
            password_hash = generate_password_hash(password)
            conn.execute('UPDATE users SET username = ?, password_hash = ?, role = ? WHERE id = ?',
                        (username, password_hash, role, user_id))
        else:
            # Update only username and role
            conn.execute('UPDATE users SET username = ?, role = ? WHERE id = ?',
                        (username, role, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    try:
        conn = get_db_connection()
        
        # Check if this is the last admin user
        admin_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = "admin"').fetchone()['count']
        user_to_delete = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if user_to_delete and user_to_delete['role'] == 'admin' and admin_count <= 1:
            conn.close()
            return jsonify({'error': 'Cannot delete the last admin user'}), 400
        
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tables API endpoints (additional CRUD operations)
@app.route('/api/tables', methods=['POST'])
@login_required
def add_table():
    try:
        data = request.get_json()
        table_number = data.get('table_number')
        
        if not table_number:
            return jsonify({'error': 'Table number required'}), 400
        
        conn = get_db_connection()
        conn.execute('INSERT INTO tables (table_number) VALUES (?)', (table_number,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tables/<int:table_id>', methods=['DELETE'])
@login_required
def delete_table(table_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM tables WHERE id = ?', (table_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Waiters API endpoints (additional CRUD operations)
@app.route('/api/waiters', methods=['POST'])
@login_required
def add_waiter():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        
        if not name:
            return jsonify({'error': 'Waiter name required'}), 400
        
        conn = get_db_connection()
        conn.execute('INSERT INTO waiters (name, phone) VALUES (?, ?)', (name, phone))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/waiters/<int:waiter_id>', methods=['PUT'])
@login_required
def edit_waiter(waiter_id):
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        
        if not name:
            return jsonify({'error': 'Waiter name required'}), 400
        
        conn = get_db_connection()
        conn.execute('UPDATE waiters SET name = ?, phone = ? WHERE id = ?', (name, phone, waiter_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/waiters/<int:waiter_id>', methods=['DELETE'])
@login_required
def delete_waiter(waiter_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM waiters WHERE id = ?', (waiter_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Reports API endpoint
@app.route('/api/reports')
@login_required
def api_reports():
    try:
        conn = get_db_connection()
        
        # Get date range from query parameters
        start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Total revenue for the period
        total_revenue = conn.execute('''
            SELECT COALESCE(SUM(p.total_amount), 0) as revenue
            FROM payments p
            JOIN orders o ON p.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        ''', (start_date, end_date)).fetchone()['revenue']
        
        # Total orders for the period
        total_orders = conn.execute('''
            SELECT COUNT(*) as count
            FROM orders
            WHERE DATE(created_at) BETWEEN ? AND ?
        ''', (start_date, end_date)).fetchone()['count']
        
        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Total items sold
        total_items = conn.execute('''
            SELECT COALESCE(SUM(oi.quantity), 0) as items
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
        ''', (start_date, end_date)).fetchone()['items']
        
        # Revenue by day (for chart)
        revenue_trend = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_revenue = conn.execute('''
                SELECT COALESCE(SUM(p.total_amount), 0) as revenue
                FROM payments p
                JOIN orders o ON p.order_id = o.id
                WHERE DATE(o.created_at) = ?
            ''', (date_str,)).fetchone()['revenue']
            
            revenue_trend.append({
                'date': date_str,
                'revenue': float(daily_revenue)
            })
            current_date += timedelta(days=1)
        
        # Payment methods breakdown
        payment_methods = conn.execute('''
            SELECT p.payment_method, COUNT(*) as count, SUM(p.total_amount) as total
            FROM payments p
            JOIN orders o ON p.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY p.payment_method
        ''', (start_date, end_date)).fetchall()
        
        # Top selling items
        top_items = conn.execute('''
            SELECT mi.name, SUM(oi.quantity) as quantity, SUM(oi.quantity * oi.price) as revenue
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            GROUP BY mi.id, mi.name
            ORDER BY quantity DESC
            LIMIT 10
        ''', (start_date, end_date)).fetchall()
        
        # Waiter performance
        waiter_performance = conn.execute('''
            SELECT w.name, COUNT(o.id) as orders, COALESCE(SUM(p.total_amount), 0) as revenue
            FROM waiters w
            LEFT JOIN orders o ON w.id = o.waiter_id AND DATE(o.created_at) BETWEEN ? AND ?
            LEFT JOIN payments p ON o.id = p.order_id
            WHERE w.active = 1
            GROUP BY w.id, w.name
            ORDER BY revenue DESC
        ''', (start_date, end_date)).fetchall()
        
        # Table performance
        table_performance = conn.execute('''
            SELECT t.table_number, COUNT(o.id) as orders, COALESCE(SUM(p.total_amount), 0) as revenue
            FROM tables t
            LEFT JOIN orders o ON t.id = o.table_id AND DATE(o.created_at) BETWEEN ? AND ?
            LEFT JOIN payments p ON o.id = p.order_id
            WHERE t.active = 1
            GROUP BY t.id, t.table_number
            ORDER BY revenue DESC
        ''', (start_date, end_date)).fetchall()
        
        # Hourly sales (for today only if single day selected)
        hourly_sales = []
        if start_date == end_date:
            for hour in range(24):
                hour_revenue = conn.execute('''
                    SELECT COALESCE(SUM(p.total_amount), 0) as revenue
                    FROM payments p
                    JOIN orders o ON p.order_id = o.id
                    WHERE DATE(o.created_at) = ? AND CAST(strftime('%H', o.created_at) AS INTEGER) = ?
                ''', (start_date, hour)).fetchone()['revenue']
                
                hourly_sales.append({
                    'hour': f"{hour:02d}:00",
                    'revenue': float(hour_revenue)
                })
        
        conn.close()
        
        return jsonify({
            'totalRevenue': float(total_revenue),
            'totalOrders': total_orders,
            'avgOrderValue': float(avg_order_value),
            'totalItems': total_items,
            'revenueTrend': revenue_trend,
            'paymentMethods': [dict(pm) for pm in payment_methods],
            'topItems': [dict(item) for item in top_items],
            'waiterPerformance': [dict(waiter) for waiter in waiter_performance],
            'tablePerformance': [dict(table) for table in table_performance],
            'hourlySales': hourly_sales
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Backup API endpoints
@app.route('/api/backup/list', methods=['GET'])
@login_required
def list_backups():
    try:
        import glob
        from datetime import datetime
        
        # Create backups directory if it doesn't exist
        os.makedirs('backups', exist_ok=True)
        
        # Get all .db files in the backups directory
        backup_files = glob.glob(os.path.join('backups', '*.db'))
        
        backups = []
        for backup_path in backup_files:
            filename = os.path.basename(backup_path)
            file_stats = os.stat(backup_path)
            
            # Get file size in MB
            size_mb = round(file_stats.st_size / (1024 * 1024), 2)
            
            # Get creation time
            created_at = datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            
            backups.append({
                'filename': filename,
                'size_mb': size_mb,
                'created_at': created_at,
                'path': backup_path
            })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'success': True, 'backups': backups})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/create', methods=['POST'])
@login_required
def create_backup():
    try:
        import shutil
        from datetime import datetime
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'restaurant_backup_{timestamp}.db'
        backup_path = os.path.join('backups', backup_filename)
        
        # Create backups directory if it doesn't exist
        os.makedirs('backups', exist_ok=True)
        
        # Copy the database file
        shutil.copy2('restaurant.db', backup_path)
        
        return jsonify({'success': True, 'filename': backup_filename})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
@login_required
def restore_backup():
    try:
        import shutil
        import gc
        
        if 'backup_file' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400
        
        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        temp_path = 'temp_restore.db'
        file.save(temp_path)
        
        # Validate the backup file is a valid SQLite database
        try:
            test_conn = sqlite3.connect(temp_path)
            test_conn.execute('SELECT name FROM sqlite_master WHERE type="table"')
            test_conn.close()
        except sqlite3.DatabaseError:
            os.remove(temp_path)
            return jsonify({'error': 'Invalid backup file - not a valid SQLite database'}), 400
        
        # Force garbage collection to close any lingering connections
        gc.collect()
        
        # Replace current database with backup
        shutil.copy2(temp_path, 'restaurant.db')
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Force Python to reload the database by clearing any cached connections
        # This ensures the next database operation will use the restored file
        import importlib
        import sys
        if 'sqlite3' in sys.modules:
            importlib.reload(sys.modules['sqlite3'])
        
        return jsonify({'success': True, 'message': 'Database restored successfully. Please refresh the page to see the restored data.'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/clear-all-data', methods=['POST'])
@login_required
def clear_all_data():
    """Clear all order history while preserving menu, waiters, tables, and settings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete order-related data (in correct order due to foreign key constraints)
        cursor.execute('DELETE FROM payments')
        cursor.execute('DELETE FROM order_items')
        cursor.execute('DELETE FROM orders')
        
        # Reset auto-increment counters for order tables
        cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("orders", "order_items", "payments")')
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'All order data has been cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/export/csv')
@login_required
def export_reports_csv():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        conn = get_db_connection()
        
        # Get orders data for the date range
        orders = conn.execute('''
            SELECT o.id, o.created_at, o.total_amount, o.status,
                   t.table_number, w.name as waiter_name,
                   p.payment_method
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            LEFT JOIN waiters w ON o.waiter_id = w.id
            LEFT JOIN payments p ON o.id = p.order_id
            WHERE DATE(o.created_at) BETWEEN ? AND ?
            ORDER BY o.created_at DESC
        ''', (start_date, end_date)).fetchall()
        
        conn.close()
        
        # Create CSV content
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Order ID', 'Date', 'Table', 'Waiter', 'Amount', 'Status', 'Payment Method'])
        
        # Write data
        for order in orders:
            writer.writerow([
                order['id'],
                order['created_at'],
                f"Table {order['table_number']}" if order['table_number'] else 'N/A',
                order['waiter_name'] or 'N/A',
                f"${order['total_amount']:.2f}",
                order['status'],
                order['payment_method'] or 'N/A'
            ])
        
        # Create response
        from flask import Response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=restaurant_report_{start_date}_to_{end_date}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/export/pdf')
@login_required
def export_reports_pdf():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        # For now, return a simple message since PDF generation requires additional libraries
        # In a production environment, you would use libraries like reportlab or weasyprint
        return jsonify({
            'message': 'PDF export feature is not yet implemented. Please use CSV export instead.',
            'csv_url': f'/api/reports/export/csv?start_date={start_date}&end_date={end_date}'
        }), 501
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tables/status')
@login_required
def api_table_status():
    """Get table status information with pending orders"""
    conn = get_db_connection()
    
    # Get all tables with their current status
    tables_status = conn.execute('''
        SELECT 
            t.id,
            t.table_number,
            t.active,
            CASE 
                WHEN COUNT(o.id) > 0 THEN 'occupied'
                ELSE 'available'
            END as status,
            GROUP_CONCAT(w.name, ', ') as waiter_name,
            COUNT(o.id) as pending_orders,
            COALESCE(SUM(o.total_amount), 0) as pending_total,
            MIN(o.created_at) as first_order_time
        FROM tables t
        LEFT JOIN orders o ON t.id = o.table_id AND o.status = 'pending'
        LEFT JOIN waiters w ON o.waiter_id = w.id
        WHERE t.active = 1
        GROUP BY t.id, t.table_number, t.active
        ORDER BY t.table_number
    ''').fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': table['id'],
        'table_number': table['table_number'],
        'status': table['status'],
        'waiter_name': table['waiter_name'],
        'waiter_id': None,  # Multiple waiters possible
        'pending_orders': table['pending_orders'],
        'pending_total': float(table['pending_total']),
        'first_order_time': table['first_order_time']
    } for table in tables_status])

@app.route('/api/tables/<int:table_id>/pending-orders')
@login_required
def api_table_pending_orders(table_id):
    """Get all pending orders for a specific table"""
    conn = get_db_connection()
    
    # Get pending orders for the table
    orders = conn.execute('''
        SELECT 
            o.id,
            o.total_amount,
            o.created_at,
            w.name as waiter_name,
            COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN waiters w ON o.waiter_id = w.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.table_id = ? AND o.status = 'pending'
        GROUP BY o.id, o.total_amount, o.created_at, w.name
        ORDER BY o.created_at
    ''', (table_id,)).fetchall()
    
    # Get detailed items for each order
    order_details = []
    for order in orders:
        items = conn.execute('''
            SELECT 
                oi.quantity,
                oi.price,
                mi.name as item_name,
                mi.category
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        
        order_details.append({
            'id': order['id'],
            'total_amount': float(order['total_amount']),
            'created_at': order['created_at'],
            'waiter_name': order['waiter_name'],
            'item_count': order['item_count'],
            'items': [dict(item) for item in items]
        })
    
    conn.close()
    
    return jsonify({
        'table_id': table_id,
        'orders': order_details,
        'total_pending': sum(order['total_amount'] for order in order_details)
    })

@app.route('/api/orders/<int:order_id>/mark-paid', methods=['POST'])
@login_required
def api_mark_order_paid(order_id):
    """Mark a single order as paid without cash received dialog"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get order details
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({'error': 'Order not found'}), 404
        
        if order['status'] != 'pending':
            conn.close()
            return jsonify({'error': 'Order is not pending'}), 400
        
        # Use local datetime for consistency
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mark order as paid
        cursor.execute('''
            UPDATE orders 
            SET status = ?, closed_at = ? 
            WHERE id = ?
        ''', ('paid', local_time, order_id))
        
        # Create payment record with default payment method
        cursor.execute('''
            INSERT INTO payments (order_id, total_amount, payment_method, paid_at)
            VALUES (?, ?, ?, ?)
        ''', (order_id, order['total_amount'], 'cash', local_time))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'total_amount': float(order['total_amount'])
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to mark order as paid: {str(e)}'}), 500

@app.route('/api/orders/table/<int:table_id>/mark-paid', methods=['POST'])
@login_required
def api_mark_table_orders_paid(table_id):
    """Mark all pending orders for a table as paid without cash received dialog"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all pending orders for this table
        pending_orders = conn.execute('''
            SELECT id, total_amount, waiter_id FROM orders 
            WHERE table_id = ? AND status = 'pending'
            ORDER BY created_at ASC
        ''', (table_id,)).fetchall()
        
        if not pending_orders:
            conn.close()
            return jsonify({'error': 'No pending orders found for this table'}), 404
        
        # Calculate total amount for all pending orders
        total_bill = sum(order['total_amount'] for order in pending_orders)
        
        # Use local datetime for consistency
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Mark all orders as paid and set final bill flag
        for i, pending_order in enumerate(pending_orders):
            is_final_bill = 1 if i == len(pending_orders) - 1 else 0  # Mark last order as final bill
            cursor.execute('''
                UPDATE orders 
                SET status = ?, closed_at = ?, is_final_bill = ?
                WHERE id = ?
            ''', ('paid', local_time, is_final_bill, pending_order['id']))
        
        # Create a single payment record for the entire bill (linked to the last order)
        last_order_id = pending_orders[-1]['id']
        cursor.execute('''
            INSERT INTO payments (order_id, total_amount, payment_method, paid_at)
            VALUES (?, ?, ?, ?)
        ''', (last_order_id, total_bill, 'cash', local_time))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'table_id': table_id,
            'total_amount': float(total_bill),
            'orders_count': len(pending_orders)
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to mark table orders as paid: {str(e)}'}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False)