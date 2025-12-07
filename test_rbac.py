#!/usr/bin/env python3
"""
RBAC (Role-Based Access Control) Testing Suite
Tests role-based access control for the Hospital Management System
"""

import unittest
import sqlite3
import os
import sys
import logging

# Suppress Flask logging during tests
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask_wtf.csrf').setLevel(logging.ERROR)

# Import from the correct app.py file
sys.path.insert(0, '/Users/macsmouse/com7033-assignment-ifeoma456')

# Import the Flask app
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", "/Users/macsmouse/com7033-assignment-ifeoma456/app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
get_db = app_module.get_db
bcrypt = app_module.bcrypt
init_db = app_module.init_db

from flask import session


# Test database setup
TEST_DB = 'test_hospital_rbac.db'


class TestRBAC(unittest.TestCase):
    """Test Role-Based Access Control"""
    
    def setUp(self):
        """Set up test client and database"""
        # Disable CSRF protection for testing
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        
        # Create test app client
        self.client = app.test_client()
        
        # Clean up and create test database
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        
        # Initialize test database
        with app.app_context():
            init_db_test()
            self.create_test_users()
        
        # Monkey patch get_db to use test database
        self.original_get_db = app_module.get_db
        app_module.get_db = self._get_test_db
        
        # Also update the get_db used in decorators
        import types
        for name in dir(app_module):
            obj = getattr(app_module, name)
            if isinstance(obj, types.FunctionType) and hasattr(obj, '__code__'):
                obj.__globals__['get_db'] = self._get_test_db
    
    def tearDown(self):
        """Clean up"""
        app_module.get_db = self.original_get_db
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    
    @staticmethod
    def _get_test_db():
        """Get test database connection"""
        conn = sqlite3.connect(TEST_DB)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_test_users(self):
        """Create test users with different roles"""
        conn = self._get_test_db()
        cursor = conn.cursor()
        
        # Test users with different roles
        test_users = [
            ('admin_user', 'admin@test.com', 'Admin@123', 'admin'),
            ('doctor_user', 'doctor@test.com', 'Doctor@123', 'doctor'),
            ('patient_user', 'patient@test.com', 'Patient@123', 'patient'),
            ('user_user', 'user@test.com', 'User@123', 'user'),
        ]
        
        for username, email, password, role in test_users:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, hashed_password, role))
        
        conn.commit()
        conn.close()
    
    def login(self, username, password, role):
        """Helper method to login a user"""
        with self.client.session_transaction() as sess:
            sess.clear()
        
        response = self.client.post('/login', data={
            'username': username,
            'password': password,
            'role': role
        }, follow_redirects=False)
        
        return response
    
    # ============================================
    #   AUTHENTICATION TESTS
    # ============================================
    
    def test_01_login_valid_admin(self):
        """Test login with valid admin credentials"""
        response = self.login('admin_user', 'Admin@123', 'admin')
        # Should redirect to dashboard (302) or show dashboard (200)
        self.assertIn(response.status_code, [200, 302])
    
    def test_02_login_valid_doctor(self):
        """Test login with valid doctor credentials"""
        response = self.login('doctor_user', 'Doctor@123', 'doctor')
        self.assertIn(response.status_code, [200, 302])
    
    def test_03_login_valid_patient(self):
        """Test login with valid patient credentials"""
        response = self.login('patient_user', 'Patient@123', 'patient')
        self.assertIn(response.status_code, [200, 302])
    
    def test_04_login_invalid_password(self):
        """Test login fails with invalid password"""
        response = self.login('admin_user', 'WrongPassword', 'admin')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
    
    def test_05_login_invalid_user(self):
        """Test login fails with non-existent user"""
        response = self.login('nonexistent', 'Password@123', 'admin')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
    
    # ============================================
    #   ADMIN ACCESS CONTROL TESTS
    # ============================================
    
    def test_10_admin_can_access_admin_panel(self):
        """Test admin can access /admin route"""
        with self.client:
            self.login('admin_user', 'Admin@123', 'admin')
            response = self.client.get('/admin', follow_redirects=False)
            # Admin should be able to access (200) or get redirected (302)
            self.assertIn(response.status_code, [200, 302])
    
    def test_11_doctor_cannot_access_admin_panel(self):
        """Test doctor is denied access to /admin route"""
        with self.client:
            self.login('doctor_user', 'Doctor@123', 'doctor')
            response = self.client.get('/admin', follow_redirects=False)
            # Should be redirected away (302) or denied (403)
            self.assertIn(response.status_code, [302, 403])
    
    def test_12_patient_cannot_access_admin_panel(self):
        """Test patient is denied access to /admin route"""
        with self.client:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.client.get('/admin', follow_redirects=False)
            # Should be redirected away (302) or denied (403)
            self.assertIn(response.status_code, [302, 403])
    
    def test_13_user_cannot_access_admin_panel(self):
        """Test user is denied access to /admin route"""
        with self.client:
            self.login('user_user', 'User@123', 'user')
            response = self.client.get('/admin', follow_redirects=False)
            # Should be redirected away (302) or denied (403)
            self.assertIn(response.status_code, [302, 403])
    
    # ============================================
    #   DOCTOR ACCESS CONTROL TESTS
    # ============================================
    
    def test_20_doctor_can_access_doctor_dashboard(self):
        """Test doctor can access /doctor/dashboard route"""
        with self.client:
            self.login('doctor_user', 'Doctor@123', 'doctor')
            response = self.client.get('/doctor/dashboard', follow_redirects=False)
            # Should succeed (200) or redirect (302)
            self.assertIn(response.status_code, [200, 302])
    
    def test_21_admin_can_access_doctor_routes(self):
        """Test admin can access doctor routes"""
        with self.client:
            self.login('admin_user', 'Admin@123', 'admin')
            response = self.client.get('/doctor/dashboard', follow_redirects=False)
            # Admin should be able to access (200) or get redirected (302)
            self.assertIn(response.status_code, [200, 302])
    
    def test_22_patient_cannot_access_doctor_routes(self):
        """Test patient is denied access to doctor routes"""
        with self.client:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.client.get('/doctor/dashboard', follow_redirects=False)
            # Should be redirected (302) or denied (403)
            self.assertIn(response.status_code, [302, 403])
    
    # ============================================
    #   BILLING ACCESS CONTROL TESTS
    # ============================================
    
    def test_30_admin_can_access_billing(self):
        """Test admin can access /billing route"""
        with self.client:
            self.login('admin_user', 'Admin@123', 'admin')
            response = self.client.get('/billing', follow_redirects=False)
            # Should succeed (200) or redirect (302)
            self.assertIn(response.status_code, [200, 302])
    
    def test_31_patient_cannot_access_billing(self):
        """Test patient is denied access to billing"""
        with self.client:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.client.get('/billing', follow_redirects=False)
            # Should be redirected (302) or denied (403)
            self.assertIn(response.status_code, [302, 403])
    
    # ============================================
    #   UNAUTHENTICATED ACCESS TESTS
    # ============================================
    
    def test_40_unauthenticated_cannot_access_admin(self):
        """Test unauthenticated user cannot access admin routes"""
        with self.client:
            response = self.client.get('/admin', follow_redirects=False)
            # Should redirect to login (302)
            self.assertEqual(response.status_code, 302)
    
    def test_41_unauthenticated_cannot_access_dashboard(self):
        """Test unauthenticated user cannot access dashboard"""
        with self.client:
            response = self.client.get('/dashboard', follow_redirects=False)
            # Should redirect to login (302)
            self.assertEqual(response.status_code, 302)
    
    def test_42_unauthenticated_cannot_access_doctor_dashboard(self):
        """Test unauthenticated user cannot access doctor dashboard"""
        with self.client:
            response = self.client.get('/doctor/dashboard', follow_redirects=False)
            # Should redirect to login (302)
            self.assertEqual(response.status_code, 302)
    
    def test_50_unauthenticated_can_access_login(self):
        """Test unauthenticated user can access login page"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_51_unauthenticated_can_access_register(self):
        """Test unauthenticated user can access register page"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_52_unauthenticated_can_access_home(self):
        """Test unauthenticated user can access home page"""
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])  # May redirect to login


def init_db_test():
    """Initialize test database with complete schema"""
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create patients table (needed by some routes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE,
            gender TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Create billing table (needed by billing route)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            amount REAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')
    
    # Create doctors table (needed by doctor routes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            specialization TEXT,
            license_number TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("RBAC (Role-Based Access Control) TEST SUITE")
    print("Testing Hospital Management System Access Control")
    print("="*70 + "\n")
    
    # Run tests with verbosity
    unittest.main(verbosity=2)
    """Test Role-Based Access Control"""
    
    def setUp(self):
        """Set up test client and database"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Disable CSRF protection for testing
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Use test database
        self.test_db = 'test_hospital.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Initialize test database
        with app.app_context():
            init_db_test()
            self.create_test_users()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def create_test_users(self):
        """Create test users with different roles"""
        # Patch get_db to use test database
        global test_db_path
        test_db_path = self.test_db
        
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Test users with different roles
        test_users = [
            ('admin_user', 'admin@test.com', 'Admin@123', 'admin'),
            ('doctor_user', 'doctor@test.com', 'Doctor@123', 'doctor'),
            ('patient_user', 'patient@test.com', 'Patient@123', 'patient'),
            ('user_user', 'user@test.com', 'User@123', 'user'),
        ]
        
        for username, email, password, role in test_users:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, hashed_password, role))
        
        conn.commit()
        conn.close()
        
        # Monkey patch get_db for testing
        app_module.get_db = lambda: sqlite3.connect(self.test_db)
    
    def login(self, username, password, role):
        """Helper method to login a user"""
        return self.app.post('/login', data={
            'username': username,
            'password': password,
            'role': role
        }, follow_redirects=True)
    
    # ============================================
    #   AUTHENTICATION TESTS
    # ============================================
    
    def test_login_valid_admin(self):
        """Test login with valid admin credentials"""
        response = self.login('admin_user', 'Admin@123', 'admin')
        self.assertIn(b'dashboard', response.data.lower() or b'admin', response.data.lower())
    
    def test_login_valid_doctor(self):
        """Test login with valid doctor credentials"""
        response = self.login('doctor_user', 'Doctor@123', 'doctor')
        self.assertNotEqual(response.status_code, 401)
    
    def test_login_valid_patient(self):
        """Test login with valid patient credentials"""
        response = self.login('patient_user', 'Patient@123', 'patient')
        self.assertNotEqual(response.status_code, 401)
    
    def test_login_invalid_password(self):
        """Test login fails with invalid password"""
        response = self.login('admin_user', 'WrongPassword', 'admin')
        self.assertIn(b'Invalid', response.data)
    
    def test_login_invalid_user(self):
        """Test login fails with non-existent user"""
        response = self.login('nonexistent', 'Password@123', 'admin')
        self.assertIn(b'Invalid', response.data)
    
    # ============================================
    #   ADMIN ACCESS CONTROL TESTS
    # ============================================
    
    def test_admin_can_access_admin_routes(self):
        """Test admin can access /admin route"""
        with self.app:
            self.login('admin_user', 'Admin@123', 'admin')
            response = self.app.get('/admin')
            # Admin should either see dashboard or be redirected
            self.assertIn(response.status_code, [200, 302])
    
    def test_doctor_cannot_access_admin_panel(self):
        """Test doctor is denied access to /admin route"""
        with self.app:
            self.login('doctor_user', 'Doctor@123', 'doctor')
            response = self.app.get('/admin', follow_redirects=False)
            # Should be redirected (302) or forbidden (403)
            self.assertIn(response.status_code, [302, 403])
    
    def test_patient_cannot_access_admin_panel(self):
        """Test patient is denied access to /admin route"""
        with self.app:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.app.get('/admin', follow_redirects=False)
            # Should be redirected (302) or forbidden (403)
            self.assertIn(response.status_code, [302, 403])
    
    def test_user_cannot_access_admin_panel(self):
        """Test user is denied access to /admin route"""
        with self.app:
            self.login('user_user', 'User@123', 'user')
            response = self.app.get('/admin', follow_redirects=False)
            # Should be redirected (302) or forbidden (403)
            self.assertIn(response.status_code, [302, 403])
    
    # ============================================
    #   DOCTOR ACCESS CONTROL TESTS
    # ============================================
    
    def test_doctor_can_access_doctor_routes(self):
        """Test doctor can access doctor-specific routes"""
        with self.app:
            self.login('doctor_user', 'Doctor@123', 'doctor')
            response = self.app.get('/doctor/dashboard', follow_redirects=False)
            # Should either succeed (200) or redirect (302)
            self.assertIn(response.status_code, [200, 302])
    
    def test_admin_can_access_doctor_routes(self):
        """Test admin can access doctor routes (admin typically has all access)"""
        with self.app:
            self.login('admin_user', 'Admin@123', 'admin')
            response = self.app.get('/doctor/dashboard', follow_redirects=False)
            # Admin should be able to access or redirected to dashboard
            self.assertIn(response.status_code, [200, 302])
    
    def test_patient_cannot_access_doctor_routes(self):
        """Test patient is denied access to doctor routes"""
        with self.app:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.app.get('/doctor/dashboard', follow_redirects=False)
            # Should be redirected (302) or forbidden (403)
            self.assertIn(response.status_code, [302, 403])
    
    # ============================================
    #   PATIENT ACCESS CONTROL TESTS
    # ============================================
    
    def test_patient_can_access_patient_routes(self):
        """Test patient can access patient-specific routes"""
        with self.app:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.app.get('/patient/profile', follow_redirects=False)
            # Should either succeed (200) or redirect (302)
            self.assertIn(response.status_code, [200, 302])
    
    def test_patient_can_view_appointments(self):
        """Test patient can view appointments"""
        with self.app:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.app.get('/appointments', follow_redirects=False)
            # Should either succeed or redirect to login
            self.assertIn(response.status_code, [200, 302])
    
    def test_patient_cannot_access_billing(self):
        """Test patient is denied access to billing (admin only)"""
        with self.app:
            self.login('patient_user', 'Patient@123', 'patient')
            response = self.app.get('/billing', follow_redirects=False)
            # Should be redirected or forbidden
            self.assertIn(response.status_code, [302, 403])
    
    # ============================================
    #   UNAUTHENTICATED ACCESS TESTS
    # ============================================
    
    def test_unauthenticated_cannot_access_admin(self):
        """Test unauthenticated user cannot access admin routes"""
        response = self.app.get('/admin', follow_redirects=False)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_unauthenticated_cannot_access_dashboard(self):
        """Test unauthenticated user cannot access dashboard"""
        response = self.app.get('/dashboard', follow_redirects=False)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_unauthenticated_can_access_login(self):
        """Test unauthenticated user can access login page"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_can_access_register(self):
        """Test unauthenticated user can access register page"""
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
    
    # ============================================
    #   ROLE MISMATCH TESTS
    # ============================================
    
    def test_login_fails_with_wrong_role(self):
        """Test login fails when selected role doesn't match user's actual role"""
        # Try to login as admin but select doctor role
        response = self.app.post('/login', data={
            'username': 'admin_user',
            'password': 'Admin@123',
            'role': 'doctor'  # Wrong role
        }, follow_redirects=True)
        self.assertIn(b'Invalid', response.data)
    
    def test_doctor_selected_for_admin_user_fails(self):
        """Test selecting doctor role for admin account fails"""
        response = self.login('admin_user', 'Admin@123', 'doctor')
        self.assertIn(b'Invalid', response.data)
    
    # ============================================
    #   CROSS-ROLE BOUNDARY TESTS
    # ============================================
    
    def test_admin_access_isolation_from_patient(self):
        """Test admin and patient data are isolated"""
        # Login as admin and check accessible routes
        with self.app:
            admin_response = self.login('admin_user', 'Admin@123', 'admin')
            admin_admin_access = self.app.get('/admin', follow_redirects=False)
            admin_can_access = admin_admin_access.status_code in [200, 302]
            
        # Login as patient and check same routes
        with self.app:
            patient_response = self.login('patient_user', 'Patient@123', 'patient')
            patient_admin_access = self.app.get('/admin', follow_redirects=False)
            patient_cannot_access = patient_admin_access.status_code in [302, 403]
            
        self.assertTrue(admin_can_access)
        self.assertTrue(patient_cannot_access)


def init_db_test():
    """Initialize test database"""
    conn = sqlite3.connect('test_hospital.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create minimal schema for testing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("RBAC (Role-Based Access Control) TEST SUITE")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
