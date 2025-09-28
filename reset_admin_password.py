#!/usr/bin/env python3
"""
Script to reset admin password to default credentials
This will create or update the admin user with default password 'admin123'
"""

import sqlite3
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset admin password to default"""
    try:
        conn = sqlite3.connect('restaurant.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        admin = cursor.fetchone()
        
        # Check if there's a user with undefined username
        cursor.execute('SELECT * FROM users WHERE username = ?', ('undefined',))
        undefined_user = cursor.fetchone()
        
        # Default password
        default_password = 'admin123'
        password_hash = generate_password_hash(default_password)
        
        if admin:
            # Update existing admin user
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, role = ? 
                WHERE username = ?
            ''', (password_hash, 'admin', 'admin'))
            print("✓ Admin password has been reset to default")
            print(f"  Username: admin")
            print(f"  Password: {default_password}")
            
        elif undefined_user:
            # Update undefined user to admin
            cursor.execute('''
                UPDATE users 
                SET username = ?, password_hash = ?, role = ? 
                WHERE username = ?
            ''', ('admin', password_hash, 'admin', 'undefined'))
            print("✓ Updated undefined user to admin with default credentials")
            print(f"  Username: admin")
            print(f"  Password: {default_password}")
            
        else:
            # Create new admin user
            cursor.execute('''
                INSERT INTO users (username, password_hash, role) 
                VALUES (?, ?, ?)
            ''', ('admin', password_hash, 'admin'))
            print("✓ New admin user created with default credentials")
            print(f"  Username: admin")
            print(f"  Password: {default_password}")
        
        conn.commit()
        
        # Verify the changes
        cursor.execute('SELECT id, username, role FROM users WHERE username = ?', ('admin',))
        updated_admin = cursor.fetchone()
        
        if updated_admin:
            print(f"\n✓ Verification successful:")
            print(f"  User ID: {updated_admin['id']}")
            print(f"  Username: {updated_admin['username']}")
            print(f"  Role: {updated_admin['role']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error resetting admin password: {e}")
        return False

def show_current_users():
    """Show all current users in the database"""
    try:
        conn = sqlite3.connect('restaurant.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, role FROM users ORDER BY id')
        users = cursor.fetchall()
        
        print("\nCurrent users in database:")
        for user in users:
            role = user['role'] if user['role'] else 'Not specified'
            print(f"  - ID: {user['id']}, Username: {user['username']}, Role: {role}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error showing users: {e}")

if __name__ == "__main__":
    print("Restaurant Admin Password Reset Tool")
    print("=" * 40)
    
    print("\nBefore reset:")
    show_current_users()
    
    print("\nResetting admin password...")
    success = reset_admin_password()
    
    if success:
        print("\nAfter reset:")
        show_current_users()
        print("\n" + "=" * 40)
        print("✓ Admin password reset completed successfully!")
        print("You can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
    else:
        print("\n✗ Password reset failed!")