from flask import Blueprint, render_template, request, redirect, url_for, session, flash
# from pymongo import MongoClient
import os
from bson.objectid import ObjectId
from pymongo import MongoClient  # for working with MongoDB _id
# from app.patients import patients_bp


patients_bp = Blueprint('patients', __name__, template_folder='templates')
def get_mongo():
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    client =  MongoClient(uri)
    db = client['secure_app']
    return db['patients']

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper

# =======================
# LIST PATIENTS
# =======================
@patients_bp.route('/list_patients')
@login_required
def list_patients():
    if 'user' not in session:
        return redirect(url_for('login'))
    coll = get_mongo()
    patients = list(coll.find())
    return render_template('patient.html', patients=patients)

# =======================
# ADD NEW PATIENT
# =======================
@patients_bp.route('/add', methods=['GET','POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        doc = {
            "id": request.form.get('id'),
            "gender": request.form.get('gender'),
            "age": float(request.form.get('age')),
            "hypertension": int(request.form.get('hypertension')),
            "ever_married": request.form.get('ever_married'),
            "work_type": request.form.get('work_type'),
            "Residence_type": request.form.get('Residence_type'),
            "avg_glucose_level": float(request.form.get('avg_glucose_level')),
            "bmi": float(request.form.get('bmi')) if request.form.get('bmi') else None,
            "smoking_status": request.form.get('smoking_status'),
            "stroke": int(request.form.get('stroke', 0))
        }
        coll = get_mongo()
        coll.insert_one(doc)
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients.list_patients'))
    return render_template('add_patient_form.html')



# =======================
# EDIT PATIENT
# =======================
@patients_bp.route('/edit/<patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    coll = get_mongo()
    patient = coll.find_one({"_id": ObjectId(patient_id)})

    if request.method == 'POST':
        updated_data = {
            "id": request.form.get('id'),
            "gender": request.form.get('gender'),
            "age": float(request.form.get('age')),
            "hypertension": int(request.form.get('hypertension')),
            "ever_married": request.form.get('ever_married'),
            "work_type": request.form.get('work_type'),
            "Residence_type": request.form.get('Residence_type'),
            "avg_glucose_level": float(request.form.get('avg_glucose_level')),
            "bmi": float(request.form.get('bmi')) if request.form.get('bmi') else None,
            "smoking_status": request.form.get('smoking_status'),
            "stroke": int(request.form.get('stroke', 0))
        }
        coll.update_one({"_id": ObjectId(patient_id)}, {"$set": updated_data})
        flash('Patient updated successfully!', 'info')
        return redirect(url_for('patients.list_patients'))

    return render_template('edit_patient_form.html', patient=patient)

# ===========================
# DELETE PATIENT @@2
# =======================
@patients_bp.route('/delete/<patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    coll = get_mongo()
    coll.delete_one({"_id": ObjectId(patient_id)})
    flash('Patient deleted successfully!', 'danger')
    return redirect(url_for('patients.list_patients'))


