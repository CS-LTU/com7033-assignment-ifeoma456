"""
Secure Flask Web Application for Stroke Prediction Patient Data Management
This application demonstrates secure software development practices including:
- User authentication with password hashing
- CSRF protection
- Input validation and sanitization
- Secure session handling
- SQL injection prevention
- XSS prevention
- Proper error logging
"""


from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['stroke_prediction']
patients_collection = db['patients']

# SQLite database for user authentication
USER_DB = 'users.db'


class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email


def init_user_db():
    """Initialize SQLite database for user authentication"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("User database initialized successfully")


@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"


def sanitize_input(input_string):
    """Sanitize user input to prevent XSS attacks"""
    if input_string is None:
        return None
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(input_string))
    return sanitized.strip()


def validate_patient_data(data):
    """Validate patient data input"""
    errors = []

    # Validate gender
    valid_genders = ['Male', 'Female', 'Other']
    if data.get('gender') not in valid_genders:
        errors.append("Invalid gender value")

    # Validate age
    try:
        age = float(data.get('age', 0))
        if age < 0 or age > 120:
            errors.append("Age must be between 0 and 120")
    except (ValueError, TypeError):
        errors.append("Invalid age format")

    # Validate hypertension and heart_disease
    valid_binary = ['0', '1', 0, 1]
    if data.get('hypertension') not in valid_binary:
        errors.append("Invalid hypertension value")
    if data.get('heart_disease') not in valid_binary:
        errors.append("Invalid heart disease value")

    # Validate ever_married
    if data.get('ever_married') not in ['Yes', 'No']:
        errors.append("Invalid marital status")

    # Validate work_type
    valid_work_types = ['Children', 'Govt_job', 'Never_worked', 'Private', 'Self-employed']
    if data.get('work_type') not in valid_work_types:
        errors.append("Invalid work type")

    # Validate residence_type
    if data.get('Residence_type') not in ['Rural', 'Urban']:
        errors.append("Invalid residence type")

    # Validate avg_glucose_level
    try:
        glucose = float(data.get('avg_glucose_level', 0))
        if glucose < 0 or glucose > 500:
            errors.append("Average glucose level must be between 0 and 500")
    except (ValueError, TypeError):
        errors.append("Invalid glucose level format")

    # Validate BMI
    bmi = data.get('bmi', '')
    if bmi and bmi != 'N/A':
        try:
            bmi_value = float(bmi)
            if bmi_value < 10 or bmi_value > 100:
                errors.append("BMI must be between 10 and 100")
        except (ValueError, TypeError):
            errors.append("Invalid BMI format")

    # Validate smoking_status
    valid_smoking = ['formerly smoked', 'never smoked', 'smokes', 'Unknown']
    if data.get('smoking_status') not in valid_smoking:
        errors.append("Invalid smoking status")

    # Validate stroke
    if data.get('stroke') not in valid_binary:
        errors.append("Invalid stroke value")

    return errors


@app.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        email = sanitize_input(request.form.get('email'))
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            logger.warning(f"Registration attempt with missing fields")
            return render_template('register.html')

        if not validate_email(email):
            flash('Invalid email format', 'danger')
            logger.warning(f"Registration attempt with invalid email: {email}")
            return render_template('register.html')

        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        # Check if user already exists
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username or email already exists', 'danger')
            conn.close()
            logger.warning(f"Registration attempt with existing username/email: {username}/{email}")
            return render_template('register.html')

        # Create new user with hashed password
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            conn.close()

            flash('Registration successful! Please log in.', 'success')
            logger.info(f"New user registered: {username}")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            conn.close()
            flash('An error occurred during registration', 'danger')
            logger.error(f"Database error during registration: {str(e)}")
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('login.html')

        # Retrieve user from database
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()

        if user_data and check_password_hash(user_data[3], password):
            # Update last login time
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                         (datetime.now(), user_data[0]))
            conn.commit()
            conn.close()

            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user, remember=remember)

            logger.info(f"User logged in: {username}")
            flash(f'Welcome back, {username}!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            conn.close()
            flash('Invalid username or password', 'danger')
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    try:
        total_patients = patients_collection.count_documents({})
        stroke_patients = patients_collection.count_documents({'stroke': 1})
        male_patients = patients_collection.count_documents({'gender': 'Male'})
        female_patients = patients_collection.count_documents({'gender': 'Female'})

        stats = {
            'total_patients': total_patients,
            'stroke_patients': stroke_patients,
            'no_stroke_patients': total_patients - stroke_patients,
            'male_patients': male_patients,
            'female_patients': female_patients
        }

        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard statistics', 'danger')
        return render_template('dashboard.html', stats={})


@app.route('/patients')
@login_required
def patients_list():
    """List all patients with pagination and search"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = sanitize_input(request.args.get('search', ''))

    try:
        # Build query
        query = {}
        if search_query:
            try:
                # Try to search by ID
                query['id'] = int(search_query)
            except ValueError:
                # Search by gender or other text fields
                query = {
                    '$or': [
                        {'gender': {'$regex': search_query, '$options': 'i'}},
                        {'work_type': {'$regex': search_query, '$options': 'i'}},
                        {'smoking_status': {'$regex': search_query, '$options': 'i'}}
                    ]
                }

        total_patients = patients_collection.count_documents(query)
        patients = list(patients_collection.find(query)
                       .skip((page - 1) * per_page)
                       .limit(per_page))

        total_pages = (total_patients + per_page - 1) // per_page

        return render_template('patients_list.html',
                             patients=patients,
                             page=page,
                             total_pages=total_pages,
                             search_query=search_query)
    except Exception as e:
        logger.error(f"Error loading patients list: {str(e)}")
        flash('Error loading patients list', 'danger')
        return render_template('patients_list.html', patients=[], page=1, total_pages=1)


@app.route('/patient/<patient_id>')
@login_required
def patient_detail(patient_id):
    """View patient details"""
    try:
        patient = patients_collection.find_one({'_id': ObjectId(patient_id)})
        if patient:
            return render_template('patient_detail.html', patient=patient)
        else:
            flash('Patient not found', 'warning')
            return redirect(url_for('patients_list'))
    except Exception as e:
        logger.error(f"Error loading patient detail: {str(e)}")
        flash('Error loading patient details', 'danger')
        return redirect(url_for('patients_list'))


@app.route('/patient/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    """Add new patient"""
    if request.method == 'POST':
        patient_data = {
            'id': sanitize_input(request.form.get('id')),
            'gender': sanitize_input(request.form.get('gender')),
            'age': sanitize_input(request.form.get('age')),
            'hypertension': sanitize_input(request.form.get('hypertension')),
            'heart_disease': sanitize_input(request.form.get('heart_disease')),
            'ever_married': sanitize_input(request.form.get('ever_married')),
            'work_type': sanitize_input(request.form.get('work_type')),
            'Residence_type': sanitize_input(request.form.get('Residence_type')),
            'avg_glucose_level': sanitize_input(request.form.get('avg_glucose_level')),
            'bmi': sanitize_input(request.form.get('bmi')),
            'smoking_status': sanitize_input(request.form.get('smoking_status')),
            'stroke': sanitize_input(request.form.get('stroke'))
        }

        # Validate patient data
        errors = validate_patient_data(patient_data)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('patient_form.html', patient=patient_data, action='Add')

        # Check if patient ID already exists
        try:
            existing = patients_collection.find_one({'id': int(patient_data['id'])})
            if existing:
                flash('Patient ID already exists', 'danger')
                return render_template('patient_form.html', patient=patient_data, action='Add')

            # Convert numeric fields
            patient_data['id'] = int(patient_data['id'])
            patient_data['age'] = float(patient_data['age'])
            patient_data['hypertension'] = int(patient_data['hypertension'])
            patient_data['heart_disease'] = int(patient_data['heart_disease'])
            patient_data['avg_glucose_level'] = float(patient_data['avg_glucose_level'])
            if patient_data['bmi'] != 'N/A':
                patient_data['bmi'] = float(patient_data['bmi'])
            patient_data['stroke'] = int(patient_data['stroke'])
            patient_data['created_by'] = current_user.username
            patient_data['created_at'] = datetime.now()

            patients_collection.insert_one(patient_data)
            flash('Patient added successfully', 'success')
            logger.info(f"Patient added by {current_user.username}: ID {patient_data['id']}")
            return redirect(url_for('patients_list'))
        except Exception as e:
            logger.error(f"Error adding patient: {str(e)}")
            flash('Error adding patient', 'danger')
            return render_template('patient_form.html', patient=patient_data, action='Add')

    return render_template('patient_form.html', patient=None, action='Add')


@app.route('/patient/edit/<patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    """Edit existing patient"""
    try:
        patient = patients_collection.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            flash('Patient not found', 'warning')
            return redirect(url_for('patients_list'))

        if request.method == 'POST':
            patient_data = {
                'id': sanitize_input(request.form.get('id')),
                'gender': sanitize_input(request.form.get('gender')),
                'age': sanitize_input(request.form.get('age')),
                'hypertension': sanitize_input(request.form.get('hypertension')),
                'heart_disease': sanitize_input(request.form.get('heart_disease')),
                'ever_married': sanitize_input(request.form.get('ever_married')),
                'work_type': sanitize_input(request.form.get('work_type')),
                'Residence_type': sanitize_input(request.form.get('Residence_type')),
                'avg_glucose_level': sanitize_input(request.form.get('avg_glucose_level')),
                'bmi': sanitize_input(request.form.get('bmi')),
                'smoking_status': sanitize_input(request.form.get('smoking_status')),
                'stroke': sanitize_input(request.form.get('stroke'))
            }

            # Validate patient data
            errors = validate_patient_data(patient_data)
            if errors:
                for error in errors:
                    flash(error, 'danger')
                patient['_id'] = ObjectId(patient_id)
                return render_template('patient_form.html', patient=patient, action='Edit')

            # Convert numeric fields
            patient_data['id'] = int(patient_data['id'])
            patient_data['age'] = float(patient_data['age'])
            patient_data['hypertension'] = int(patient_data['hypertension'])
            patient_data['heart_disease'] = int(patient_data['heart_disease'])
            patient_data['avg_glucose_level'] = float(patient_data['avg_glucose_level'])
            if patient_data['bmi'] != 'N/A':
                patient_data['bmi'] = float(patient_data['bmi'])
            patient_data['stroke'] = int(patient_data['stroke'])
            patient_data['updated_by'] = current_user.username
            patient_data['updated_at'] = datetime.now()

            patients_collection.update_one(
                {'_id': ObjectId(patient_id)},
                {'$set': patient_data}
            )

            flash('Patient updated successfully', 'success')
            logger.info(f"Patient updated by {current_user.username}: ID {patient_data['id']}")
            return redirect(url_for('patient_detail', patient_id=patient_id))

        return render_template('patient_form.html', patient=patient, action='Edit')
    except Exception as e:
        logger.error(f"Error editing patient: {str(e)}")
        flash('Error editing patient', 'danger')
        return redirect(url_for('patients_list'))


@app.route('/patient/delete/<patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    """Delete patient"""
    try:
        patient = patients_collection.find_one({'_id': ObjectId(patient_id)})
        if patient:
            patients_collection.delete_one({'_id': ObjectId(patient_id)})
            flash('Patient deleted successfully', 'success')
            logger.info(f"Patient deleted by {current_user.username}: ID {patient.get('id')}")
        else:
            flash('Patient not found', 'warning')
    except Exception as e:
        logger.error(f"Error deleting patient: {str(e)}")
        flash('Error deleting patient', 'danger')

    return redirect(url_for('patients_list'))


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {str(error)}")
    return render_template('500.html'), 500


if __name__ == '__main__':
    init_user_db()
    logger.info("Application started")
    app.run(debug=True, host='127.0.0.1', port=5000)
