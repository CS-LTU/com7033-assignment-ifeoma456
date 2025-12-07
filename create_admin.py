#!/usr/bin/env python
"""
Script to create or promote a user to admin
"""
import sqlite3
import sys

def create_admin(username, password):
    """Create a new admin user or promote existing user"""
    from flask_bcrypt import Bcrypt
    
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user:
        # Promote existing user to admin
        user_id, current_role = user
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", ('admin', user_id))
        conn.commit()
        print(f"✓ User '{username}' promoted to admin (was: {current_role})")
    else:
        # Create new admin user
        bcrypt = Bcrypt()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, f"{username}@hospital.local", hashed_password, 'admin')
            )
            conn.commit()
            print(f"✓ Admin user '{username}' created successfully")
        except sqlite3.IntegrityError:
            print(f"✗ Error: Username or email already exists")
            return False
    
    conn.close()
    return True

def list_users():
    """List all users and their roles"""
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, role, created_at FROM users ORDER BY id")
    users = cursor.fetchall()
    
    print("\n" + "="*80)
    print("SYSTEM USERS")
    print("="*80)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Created':<15}")
    print("-"*80)
    
    for user in users:
        print(f"{user['id']:<5} {user['username']:<20} {user['email']:<30} {user['role']:<10} {user['created_at']:<15}")
    
    print("="*80 + "\n")
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'list':
            list_users()
        elif command == 'create':
            if len(sys.argv) < 4:
                print("Usage: python create_admin.py create <username> <password>")
                print("Example: python create_admin.py create admin password123")
                sys.exit(1)
                
            
            username = sys.argv[2]
            password = sys.argv[3]
            create_admin(username, password)
        elif command == 'promote':
            if len(sys.argv) < 3:
                print("Usage: python create_admin.py promote <username>")
                print("Example: python create_admin.py promote testuser")
                sys.exit(1)
            
            username = sys.argv[2]
            conn = sqlite3.connect('hospital.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", ('admin', username))
            conn.commit()
            conn.close()
            print(f"✓ User '{username}' promoted to admin")
        else:
            print("Unknown command. Use: create, promote, or list")
    else:
        print("Admin User Manager")
        print("==================\n")
        print("Usage:")
        print("  python create_admin.py create <username> <password>  - Create new admin user")
        print("  python create_admin.py promote <username>            - Promote existing user to admin")
        print("  python create_admin.py list                          - List all users\n")
        print("Examples:")
        print("  python create_admin.py create admin password123")
        print("  python create_admin.py promote testuser")
        print("  python create_admin.py list")
