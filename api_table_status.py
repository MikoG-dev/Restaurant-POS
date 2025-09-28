# API endpoint for table status management
# This file contains template code for table status API endpoints

def get_table_status_api_code():
    """
    Returns the code for table status API endpoints
    This can be integrated into app.py
    """
    return """
@app.route('/api/tables/status')
@login_required
def api_table_status():
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
            GROUP_CONCAT(DISTINCT w.name, ', ') as waiter_name,
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
        'waiter_id': None,
        'pending_orders': table['pending_orders'],
        'pending_total': float(table['pending_total']),
        'first_order_time': table['first_order_time']
    } for table in tables_status])

@app.route('/api/tables/<int:table_id>/pending-orders')
@login_required
def api_table_pending_orders(table_id):
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
                oi.added_at,
                mi.name as item_name,
                mi.category
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
            ORDER BY oi.added_at
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
"""

if __name__ == "__main__":
    print("This is a template file for table status API endpoints.")
    print("The actual endpoints are implemented in app.py")