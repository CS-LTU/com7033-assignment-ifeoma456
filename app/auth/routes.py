from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
# from pymongo import MongoClient
import os

# from app.patients import login_required, patients_bp


auth_bp = Blueprint('auth', __name__)


def get_mongo():
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    client = MongoClient(uri)
    db =    client['secure_app']
    return db['users']
@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    coll = get_mongo()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = coll.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['user'] = username
            flash('Login successful', 'success')
            return redirect(url_for('patients.list_patients'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    coll = get_mongo()
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if coll.find_one({'username': username}):
            flash('User already exists', 'warning')
        else:
            coll.insert_one({'username': username, 'password': password})
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))



# @patients_bp.route('/edit/<patient_id>', methods=['GET', 'POST'])
# @login_required
# def edit_patient(patient_id):
#     coll = get_mongo()
#     patient = coll.find_one({'id': patient_id})

#     if not patient:
#         flash('Patient not found.', 'danger')
#         return redirect(url_for('patients.list_patients'))

#     if request.method == 'POST':
#         updated_doc = {
#             "id": request.form.get('id'),
#             "gender": request.form.get('gender'),
#             "age": float(request.form.get('age')),
#             "hypertension": int(request.form.get('hypertension')),
#             "ever_married": request.form.get('ever_married'),
#             "work_type": request.form.get('work_type'),
#             "Residence_type": request.form.get('Residence_type'),
#             "avg_glucose_level": float(request.form.get('avg_glucose_level')),
#             "bmi": float(request.form.get('bmi')) if request.form.get('bmi') else None,
#             "smoking_status": request.form.get('smoking_status'),
#             "stroke": int(request.form.get('stroke', 0))
#         }

#         coll.update_one({'id': patient_id}, {'$set': updated_doc})
#         flash('Patient details updated successfully.', 'success')
#         return redirect(url_for('patients.list_patients'))

#     return render_template('patient_form.html', patient=patient, edit_mode=True)


# @patients_bp.route('/delete/<patient_id>')
# @login_required
# def delete_patient(patient_id):
#     coll = get_mongo()
#     coll.delete_one({'id': patient_id})
#     flash('Patient deleted successfully.', 'info')
#     return redirect(url_for('patients.list_patients'))