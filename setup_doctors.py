#!/usr/bin/env python
"""
Script to setup doctor profiles for testing Option C
"""
import sqlite3
from datetime import datetime

def setup_test_doctors():
    """Create test doctor profiles"""
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    try:
        # Check if we have any users with doctor role
        cursor.execute("SELECT id, username, full_name FROM users WHERE role = 'doctor' LIMIT 3")
        doctors = cursor.fetchall()
        
        if not doctors:
            print("No doctors found. Please create doctor users first via the registration page.")
            print("Then assign them the 'doctor' role via admin panel.")
            return
        
        print(f"✓ Found {len(doctors)} doctor user(s)")
        
        # Create doctor profiles for each doctor user
        for user_id, username, full_name in doctors:
            # Check if profile exists
            cursor.execute("SELECT id FROM doctors WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO doctors (
                        user_id, specialization, license_number, 
                        qualification, experience_years, availability_status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    'General Practice',
                    f'LIC-{user_id}-{int(datetime.now().timestamp())}',
                    'MD',
                    5,
                    'available'
                ))
                print(f"  ✓ Created profile for: {full_name} (@{username})")
            else:
                print(f"  ℹ Profile already exists for: {full_name} (@{username})")
        
        conn.commit()
        print("\n✓ Doctor profiles setup complete!")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_test_doctors()
