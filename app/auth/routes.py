from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from app.utils.sqlite_db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        cursor = db.execute('SELECT password FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row['password'], password):
            session['user'] = username
            flash('Login successful', 'success')
            return redirect(url_for('patients.list_patients'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password_raw = request.form.get('password', '')
        db = get_db()
        if db.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone():
            flash('User already exists', 'warning')
        else:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, generate_password_hash(password_raw)))
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))