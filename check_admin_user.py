#!/usr/bin/env python3
"""
Script to check admin user details and database structure
"""

import sqlite3

def check_admin_user():
    """Check current admin user details"""
    try:
        conn = sqlite3.connect('restaurant.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        admin = cursor.fetchone()
        
        if admin:
            print("Admin user found:")
            print(f"  ID: {admin['id']}")
            print(f"  Username: {admin['username']}")
            print(f"  Role: {admin['role'] if admin['role'] else 'Not specified'}")
            print(f"  Password hash: {admin['password_hash'][:20]}...")
        else:
            print("No admin user found")
        
        # Check users table structure
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        print("\nUsers table structure:")
        for col in columns:
            print(f"  {col['name']}: {col['type']} (nullable: {not col['notnull']})")
        
        # Check all users
        cursor.execute('SELECT id, username, role, password_hash FROM users')
        all_users = cursor.fetchall()
        print(f"\nTotal users in database: {len(all_users)}")
        for user in all_users:
            role = user['role'] if user['role'] else 'Not specified'
            print(f"  - {user['username']} (ID: {user['id']}, Role: {role})")
            print(f"    Password hash: {user['password_hash'][:20]}...")
        
        conn.close()
        return admin is not None
        
    except Exception as e:
        print(f"Error checking admin user: {e}")
        return False

if __name__ == "__main__":
    check_admin_user()