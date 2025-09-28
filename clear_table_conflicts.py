#!/usr/bin/env python3
"""
Script to clear table assignment conflicts by removing all pending orders.
This will allow fresh order placement without waiter conflicts.
"""

import sqlite3
from datetime import datetime

def clear_table_conflicts():
    """Clear all pending orders to resolve table assignment conflicts"""
    
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    
    try:
        # First, show current pending orders
        cursor.execute('''
            SELECT 
                o.id,
                o.table_id,
                o.waiter_id,
                o.total_amount,
                t.table_number,
                w.name as waiter_name
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            LEFT JOIN waiters w ON o.waiter_id = w.id
            WHERE o.status = 'pending'
            ORDER BY o.created_at DESC
        ''')
        
        pending_orders = cursor.fetchall()
        print(f"Found {len(pending_orders)} pending orders that will be cleared:")
        
        for order in pending_orders:
            print(f"  Order {order[0]}: Table {order[4]}, Waiter {order[5]}, Amount ${order[3]:.2f}")
        
        if pending_orders:
            # Ask for confirmation
            response = input(f"\nDo you want to clear all {len(pending_orders)} pending orders? (yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                # Delete order items first (foreign key constraint)
                cursor.execute('DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE status = "pending")')
                deleted_items = cursor.rowcount
                
                # Delete pending orders
                cursor.execute('DELETE FROM orders WHERE status = "pending"')
                deleted_orders = cursor.rowcount
                
                conn.commit()
                
                print(f"\nSuccessfully cleared:")
                print(f"  - {deleted_orders} pending orders")
                print(f"  - {deleted_items} order items")
                print("\nAll table assignment conflicts have been resolved!")
                print("You can now place new orders without waiter conflicts.")
                
            else:
                print("Operation cancelled. No changes made.")
        else:
            print("No pending orders found. Tables are already clear.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Restaurant Table Conflict Resolver")
    print("=" * 40)
    clear_table_conflicts()