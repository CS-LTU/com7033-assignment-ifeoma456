from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import sqlite3
import re
import time
import os
import shutil
import logging

from datetime import timedelta, datetime
from functools import wraps
from models import stroke_predictor, get_model_stats, DoctorAnalytics, patient_health_model, DoctorProfile, DoctorActivityLogger, DoctorPatientAssignment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key'
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Context processor to inject csrf_token into all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: csrf.generate_csrf() if hasattr(csrf, 'generate_csrf') else '')

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (int(user_id),))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[3])
    return None

# ============================================
#   AUTO LOGOUT AFTER 3 MINUTES INACTIVITY
# ============================================
app.permanent_session_lifetime = timedelta(minutes=3)


# ============================================
#   INITIALIZING SQLITE DATABASE
# ============================================
def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # USERS TABLE
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

    # PATIENTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            emergency_contact TEXT,
            medical_history TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # APPOINTMENTS TABLE
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Scheduled',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    

    # BILLING TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'Unpaid',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # REPORTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            details TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # RECENT ACTIVITY LOG TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # HEALTH RISK ASSESSMENT HISTORY TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            gender TEXT,
            age INTEGER,
            hypertension BOOLEAN,
            heart_disease BOOLEAN,
            ever_married TEXT,
            work_type TEXT,
            residence_type TEXT,
            avg_glucose_level REAL,
            bmi REAL,
            smoking_status TEXT,
            risk_level TEXT,
            risk_score REAL,
            confidence REAL,
            probability_no_condition REAL,
            probability_has_condition REAL,
            assessment_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')

    # DOCTORS TABLE (NEW - Option C Doctor System)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            specialization TEXT NOT NULL,
            contact_number TEXT,
            license_number TEXT NOT NULL UNIQUE,
            qualification TEXT,
            experience_years INTEGER,
            consultation_fee REAL,
            availability_status TEXT DEFAULT 'available',
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # DOCTOR ACTIVITY LOG TABLE (NEW - Option C Doctor System)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            details TEXT,
            patient_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')

    # DOCTOR-PATIENT ASSIGNMENT TABLE (NEW - Option C Doctor System)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_patient_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            UNIQUE(doctor_id, patient_id)
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# ============================================
#   DB CONNECTION
# ============================================
def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn


# ============================================
#   LOGIN REQUIRED DECORATOR
# ============================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ============================================
#   PASSWORD VALIDATION
# ============================================
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase"
    if not re.search(r"\d", password):
        return False, "Password must contain a number"
    if not re.search(r"[!@#$%^&*()_+{}\[\]:;<>,.?/\\-]", password):
        return False, "Password must contain a special character"
    return True, "OK"


# ============================================
#   INDEX → LOGIN REDIRECT
# ============================================
@app.route("/")
def index():
    return redirect(url_for("login"))


# ============================================
#   LOGIN WITH BRUTE-FORCE PROTECTION
# ============================================
@app.route("/login", methods=["GET", "POST"])
def login():
    session.permanent = True

    lockout_time = session.get("lockout_time")
    failed_attempts = session.get("failed_attempts", 0)

    # If locked out
    if lockout_time:
        remaining = int(lockout_time - time.time())
        if remaining > 0:
            flash(f"Too many attempts. Try again in {remaining}s", "danger")
            return render_template("login.html", lockout_remaining=remaining)
        else:
            session["failed_attempts"] = 0
            session["lockout_time"] = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        selected_role = request.form.get("role", "").strip()

        # Validate role selection
        if not selected_role:
            flash("Please select a role", "danger")
            return render_template("login.html", lockout_remaining=0)

        valid_roles = ["admin", "doctor", "employee", "user", "patient"]
        if selected_role not in valid_roles:
            flash("Invalid role selected", "danger")
            return render_template("login.html", lockout_remaining=0)

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user["password"], password):
            # Check if selected role matches user's actual role
            if user["role"] != selected_role:
                failed_attempts += 1
                session["failed_attempts"] = failed_attempts
                
                if failed_attempts >= 3:
                    session["lockout_time"] = time.time() + 60
                    flash("Locked out for 60 seconds", "danger")
                    return render_template("login.html", lockout_remaining=60)
                
                flash(f"Role mismatch! Your role is '{user['role']}'", "danger")
                return render_template("login.html", lockout_remaining=0)

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            session["failed_attempts"] = 0
            session["lockout_time"] = None

            flash("Login successful!", "success")
            
            # Role-based redirect
            user_role = user["role"]
            if user_role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user_role == "doctor":
                return redirect(url_for("doctor_profile"))
            else:  # user/employee/patient
                return redirect(url_for("dashboard"))
        else:
            failed_attempts += 1
            session["failed_attempts"] = failed_attempts

            if failed_attempts >= 3:
                session["lockout_time"] = time.time() + 60
                flash("Locked out for 60 seconds", "danger")
                return render_template("login.html", lockout_remaining=60)

            flash("Invalid username or password", "danger")

    return render_template("login.html", lockout_remaining=0)


# ============================================
#   REGISTER
# ============================================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        role = request.form.get("role", "user")  # Get role from form, default to 'user'

        errors = []

        if password != confirm:
            errors.append("Passwords do not match")

        valid, msg = validate_password(password)
        if not valid:
            errors.append(msg)

        # Validate role
        valid_roles = ['user', 'doctor', 'admin', 'patient']
        if role not in valid_roles:
            errors.append("Invalid role selected")

        conn = get_db()

        exists_user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        exists_email = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()

        if exists_user:
            errors.append("Username already exists")
        if exists_email:
            errors.append("Email already exists")

        if errors:
            for e in errors:
                flash(e, "danger")
            conn.close()
            return render_template("register.html")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        conn.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)", (username, email, hashed, role))
        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================
#   DASHBOARD (DYNAMIC DATA)
# ============================================
@app.route("/dashboard")
@login_required
def dashboard():
    # Patients should not see the full dashboard
    if session.get('role') == 'patient':
        flash("Access restricted. Patients can only view Appointments and Settings.", "info")
        return redirect(url_for('appointments'))
    
    conn = get_db()

    # ---- METRIC CARDS ----
    total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    total_appointments = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]

    todays_appointments = conn.execute(
        "SELECT COUNT(*) FROM appointments WHERE appointment_date = DATE('now')"
    ).fetchone()[0]

    pending_bills = conn.execute(
        "SELECT COUNT(*) FROM billing WHERE status = 'Unpaid'"
    ).fetchone()[0]

    # -----------------------------------------
    # 1️⃣ PATIENTS PER MONTH (12-MONTH LINE CHART)
    # -----------------------------------------
    patients_monthly = []
    for m in range(1, 13):
        count = conn.execute(
            """
            SELECT COUNT(*) FROM patients
            WHERE strftime('%m', created_at) = ?
            """,
            (f"{m:02}",)
        ).fetchone()[0]
        patients_monthly.append(count)

    # --------------------------------------------------
    # 2️⃣ APPOINTMENTS PER DAY (LAST 7 DAYS LINE CHART)
    # --------------------------------------------------
    appointments_daily = []
    labels_daily = []

    rows = conn.execute("""
        SELECT appointment_date, COUNT(*) 
        FROM appointments 
        GROUP BY appointment_date
        ORDER BY appointment_date DESC
        LIMIT 7
    """).fetchall()

    rows = list(rows)[::-1]  # reverse to chronological

    for row in rows:
        labels_daily.append(row['appointment_date'])
        appointments_daily.append(row[1])

    # -----------------------------------------
    # 3️⃣ BILLING STATUS (DOUGHNUT CHART)
    # -----------------------------------------
    billing_status = {
        "paid": conn.execute("SELECT COUNT(*) FROM billing WHERE status='Paid'").fetchone()[0],
        "unpaid": conn.execute("SELECT COUNT(*) FROM billing WHERE status='Unpaid'").fetchone()[0],
        "cancelled": conn.execute("SELECT COUNT(*) FROM billing WHERE status='Cancelled'").fetchone()[0]
    }

    conn.close()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_appointments=total_appointments,
        todays_appointments=todays_appointments,
        pending_bills=pending_bills,
        patients_monthly=patients_monthly,
        labels_daily=labels_daily,
        appointments_daily=appointments_daily,
        billing_status=billing_status
    )


# ============================================
#   CREATE PATIENT
# ============================================
@app.route('/create_patient', methods=['GET', 'POST'])
@login_required
def create_patient():
    # Restrict patient access
    if session.get('role') == 'patient':
        flash("Access denied. Patients cannot create patient records.", "danger")
        return redirect(url_for('appointments'))
    
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        emergency_contact = request.form['emergency_contact']
        medical_history = request.form['medical_history']

        # Required field validation
        if not all([patient_id, first_name, last_name, date_of_birth, gender]):
            flash("Please fill in all required fields.", "danger")
            return render_template("create_patient.html")

        conn = get_db()

        # Checking for duplicate Patient ID
        existing = conn.execute(
            "SELECT id FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()

        if existing:
            flash("Patient ID already exists.", "danger")
            conn.close()
            return render_template("create_patient.html")

        # Insert into database
        conn.execute('''
            INSERT INTO patients (
                patient_id, first_name, last_name, date_of_birth, gender,
                phone, email, address, emergency_contact, medical_history, created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, first_name, last_name, date_of_birth, gender,
            phone, email, address, emergency_contact, medical_history, session['user_id']
        ))

        # Log in recent activity
        conn.execute(
            "INSERT INTO recent_activity (message) VALUES (?)",
            (f"New patient created: {first_name} {last_name}",)
        )

        # Get new patient ID for logging
        patient_id_from_db = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Log doctor activity if current user is a doctor
        if session.get('role') == 'doctor':
            try:
                doctor_id_result = conn.execute('SELECT id FROM doctors WHERE user_id = ?', (session['user_id'],)).fetchone()
                if doctor_id_result:
                    activity_logger = DoctorActivityLogger()
                    activity_logger.log_activity(
                        doctor_id_result[0],
                        'patient_created',
                        f'Created patient: {first_name} {last_name}',
                        patient_id_from_db
                    )
            except Exception as e:
                logger.error(f"Error logging doctor activity: {str(e)}")

        conn.commit()
        conn.close()

        flash("Patient created successfully!", "success")
        return redirect(url_for("view_patients"))

    return render_template("create_patient.html")


# ============================================
#   VIEW PATIENTS
# ============================================

@app.route('/view_patients')
@login_required
def view_patients():
    # Restrict patient access
    if session.get('role') == 'patient':
        flash("Access denied. Patients cannot view patient records.", "danger")
        return redirect(url_for('appointments'))
    
    conn = get_db()
    patients = conn.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("view_patients.html", patients=patients)



# ============================================
#   CREATE APPOINTMENT
# ============================================
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    conn = get_db()

    # ============================
    # FETCH PATIENTS
    # ============================
    patients = conn.execute("""
        SELECT id, first_name, last_name, patient_id 
        FROM patients
        ORDER BY first_name
    """).fetchall()

    # ============================
    # FETCH DOCTORS
    # ============================
    doctors = conn.execute("""
        SELECT id, username 
        FROM users 
        WHERE role='user'
        ORDER BY username
    """).fetchall()

    # ============================
    # HANDLE APPOINTMENT CREATION
    # ============================
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        date = request.form['appointment_date']
        time_ = request.form['appointment_time']
        reason = request.form.get('reason', '')

        # Save appointment
        conn.execute("""
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id, doctor_id, date, time_, reason, session['user_id']))

        # Log activity
        conn.execute(
            "INSERT INTO recent_activity (message) VALUES (?)",
            (f"New appointment scheduled for patient ID {patient_id}",)
        )

        conn.commit()
        conn.close()

        flash("Appointment created successfully!", "success")
        return redirect(url_for("appointments"))

    # ============================
    # FETCH BOOKED APPOINTMENTS (FOR CALENDAR)
    # ============================
    booked_rows = conn.execute("""
        SELECT 
            appointments.id,
            appointments.appointment_date AS date,
            appointments.appointment_time AS time,
            users.username AS doctor
        FROM appointments
        JOIN users ON users.id = appointments.doctor_id
        ORDER BY appointment_date
    """).fetchall()

    # Convert to FullCalendar format
    booked_events = [
        {
            "title": f"Dr. {row['doctor']} - {row['time']}",
            "start": f"{row['date']}T{row['time']}",
            "color": "#55B4AF"
        }
        for row in booked_rows
    ]

    conn.close()

    # RENDER TEMPLATE
    return render_template(
        "appointment.html",
        patients=patients,
        doctors=doctors,
        booked_appointments=booked_events
    )




# ============================================
#   VIEW APPOINTMENTS
# ============================================
@app.route('/appointments_list')
@login_required
def appointments_list():
    conn = get_db()

    appts = conn.execute('''
        SELECT a.*, p.first_name, p.last_name
        FROM appointments a
        JOIN patients p ON p.id = a.patient_id
        ORDER BY a.created_at DESC
    ''').fetchall()

    conn.close()
    return render_template("appointments_list.html", appts=appts)



# ============================================
#   BILLING (CREATE + VIEW LIST)
# ============================================
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    # Restrict patient access to billing
    if session.get('role') == 'patient':
        flash("Access restricted. Patients cannot access billing.", "danger")
        return redirect(url_for('appointments'))
    
    conn = get_db()

    # Fetch patients for dropdown
    patients = conn.execute("""
        SELECT id, first_name, last_name FROM patients ORDER BY first_name
    """).fetchall()

    # Fetch all billing items
    bills = conn.execute("""
        SELECT b.*, p.first_name, p.last_name
        FROM billing b
        JOIN patients p ON p.id = b.patient_id
        ORDER BY b.created_at DESC
    """).fetchall()

    # Handle create bill
    if request.method == "POST":
        patient_id = request.form["patient_id"]
        description = request.form["description"]
        amount = request.form["amount"]

        conn.execute("""
            INSERT INTO billing (patient_id, description, amount, status, created_by)
            VALUES (?, ?, ?, 'Unpaid', ?)
        """, (patient_id, description, amount, session["user_id"]))

        conn.commit()
        conn.close()

        flash("Billing record added successfully!", "success")
        return redirect(url_for("billing"))

    conn.close()
    return render_template("billing.html", patients=patients, bills=bills)


# ============================================
#   UPDATE BILL STATUS (Paid / Unpaid / Cancelled)
# ============================================
@app.route("/billing/<int:id>/status/<string:new_status>")
@login_required
def update_bill_status(id, new_status):
    if new_status not in ["Paid", "Unpaid", "Cancelled"]:
        flash("Invalid billing status.", "danger")
        return redirect(url_for("billing"))

    conn = get_db()
    conn.execute(
        "UPDATE billing SET status = ? WHERE id = ?",
        (new_status, id)
    )
    conn.commit()
    conn.close()

    flash(f"Billing status updated to {new_status}!", "success")
    return redirect(url_for("billing"))


# ============================================
#   DELETE BILL
# ============================================
@app.route("/billing/<int:id>/delete")
@login_required
def delete_bill(id):
    conn = get_db()
    conn.execute("DELETE FROM billing WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Billing record deleted successfully!", "success")
    return redirect(url_for("billing"))


# ============================================
#   BILLING LIST
# ============================================
@app.route('/billing_list')
@login_required
def billing_list():
    conn = get_db()

    bills = conn.execute('''
        SELECT b.*, p.first_name, p.last_name
        FROM billing b
        JOIN patients p ON p.id = b.patient_id
        ORDER BY b.created_at DESC
    ''').fetchall()

    conn.close()
    return render_template("billing_list.html", bills=bills)



# ============================================
#   REPORTS ROUTE FOR(APPOINTMENT | PATIENT | BILLING)
# ============================================
@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    # Restrict patient access to reports
    if session.get('role') == 'patient':
        flash("Access restricted. Patients cannot access reports.", "danger")
        return redirect(url_for('appointments'))
    
    conn = get_db()

    # Load patients for dropdown
    patients = conn.execute("""
        SELECT id, first_name, last_name
        FROM patients
        ORDER BY first_name
    """).fetchall()

    # If first time loading page → no report yet
    if request.method == 'GET':
        return render_template(
            "reports.html",
            patients=patients,
            columns=[],
            data=[],
            chart_dates=[],
            chart_appts=[],
            billing_summary=[]
        )

    # --------------------------------------------
    # EXTRACT FORM FILTERS
    # --------------------------------------------
    report_type = request.form.get("report_type")
    patient_id = request.form.get("patient_id")
    start = request.form.get("start_date")
    end = request.form.get("end_date")

    where_clauses = []
    params = []

    # Filtering by selected patient
    if patient_id:
        where_clauses.append("patient_id = ?")
        params.append(patient_id)

    # Date range filter
    if start:
        where_clauses.append("DATE(created_at) >= DATE(?)")
        params.append(start)

    if end:
        where_clauses.append("DATE(created_at) <= DATE(?)")
        params.append(end)

    # Build WHERE SQL
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    data = []
    columns = []

    # ============================================
    #   1️⃣ APPOINTMENT REPORT
    # ============================================
    if report_type == "appointments":
        query = f"""
            SELECT 
                a.id,
                p.first_name || ' ' || p.last_name AS patient,
                a.appointment_date,
                a.appointment_time,
                a.reason,
                a.status,
                a.created_at
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            {where_sql}
            ORDER BY a.created_at DESC
        """

        rows = conn.execute(query, params).fetchall()

        columns = ["ID", "Patient", "Date", "Time", "Reason", "Status", "Created At"]
        data = [
            {
                "ID": r["id"],
                "Patient": r["patient"],
                "Date": r["appointment_date"],
                "Time": r["appointment_time"],
                "Reason": r["reason"],
                "Status": r["status"],
                "Created At": r["created_at"]
            }
            for r in rows
        ]

        # ---------- Chart Data (Appointments per Date) ----------
        chart_query = """
            SELECT appointment_date, COUNT(*)
            FROM appointments
            GROUP BY appointment_date
            ORDER BY appointment_date ASC
        """
        chart_rows = conn.execute(chart_query).fetchall()

        chart_dates = [row[0] for row in chart_rows]
        chart_appts = [row[1] for row in chart_rows]

        billing_summary = []

    # ============================================
    #   2️⃣ PATIENT REPORT
    # ============================================
    elif report_type == "patients":
        query = f"""
            SELECT 
                id,
                patient_id,
                first_name,
                last_name,
                gender,
                phone,
                created_at
            FROM patients
            {where_sql}
            ORDER BY created_at DESC
        """

        rows = conn.execute(query, params).fetchall()

        columns = ["ID", "Patient ID", "First Name", "Last Name", "Gender", "Phone", "Created At"]

        data = [
            {
                "ID": r["id"],
                "Patient ID": r["patient_id"],
                "First Name": r["first_name"],
                "Last Name": r["last_name"],
                "Gender": r["gender"],
                "Phone": r["phone"],
                "Created At": r["created_at"]
            }
            for r in rows
        ]

        # Patient report has no charts
        chart_dates = []
        chart_appts = []

        # Billing summary still needed for second chart
        billing_summary = [
            conn.execute("SELECT COUNT(*) FROM billing WHERE status='Paid'").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM billing WHERE status='Unpaid'").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM billing WHERE status='Cancelled'").fetchone()[0]
        ]

    # ============================================
    #   3️⃣ BILLING REPORT
    # ============================================
    elif report_type == "billing":
        query = f"""
            SELECT 
                b.id,
                p.first_name || ' ' || p.last_name AS patient,
                b.amount,
                b.description,
                b.status,
                b.created_at
            FROM billing b
            JOIN patients p ON p.id = b.patient_id
            {where_sql}
            ORDER BY b.created_at DESC
        """

        rows = conn.execute(query, params).fetchall()

        columns = ["ID", "Patient", "Amount", "Description", "Status", "Created At"]

        data = [
            {
                "ID": r["id"],
                "Patient": r["patient"],
                "Amount": r["amount"],
                "Description": r["description"],
                "Status": r["status"],
                "Created At": r["created_at"]
            }
            for r in rows
        ]

        # Chart for billing
        chart_dates = []
        chart_appts = []

        billing_summary = [
            conn.execute("SELECT COUNT(*) FROM billing WHERE status='Paid'").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM billing WHERE status='Unpaid'").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM billing WHERE status='Cancelled'").fetchone()[0]
        ]

    conn.close()

    return render_template(
        "reports.html",
        patients=patients,
        columns=columns,
        data=data,
        chart_dates=chart_dates,
        chart_appts=chart_appts,
        billing_summary=billing_summary
    )

# ============================================
#   USER SETTINGS (PROFILE UPDATE)
# ============================================
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session['user_id'],)
    ).fetchone()

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # ================================
        # 1️⃣ PROFILE UPDATE FORM
        # ================================
        if form_type == "profile":
            new_username = request.form.get("username")
            new_email = request.form.get("email")

            errors = []

            # Username check
            existing_user = conn.execute(
                "SELECT id FROM users WHERE username = ? AND id != ?",
                (new_username, session['user_id'])
            ).fetchone()

            if existing_user:
                errors.append("Username already taken by another user.")

            # Email check
            existing_email = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?",
                (new_email, session['user_id'])
            ).fetchone()

            if existing_email:
                errors.append("Email already taken.")

            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template("settings.html", user=user)

            # Save data
            conn.execute(
                "UPDATE users SET username = ?, email = ? WHERE id = ?",
                (new_username, new_email, session['user_id'])
            )

            conn.execute(
                "INSERT INTO recent_activity (message) VALUES (?)",
                (f"User '{session['username']}' updated profile information",)
            )

            conn.commit()
            conn.close()

            session["username"] = new_username

            flash("Profile updated successfully!", "success")
            return redirect(url_for("settings"))


        # ================================
        # 2️⃣ PASSWORD UPDATE FORM
        # ================================
        if form_type == "password":
            new_password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            errors = []

            if not new_password:
                errors.append("Password cannot be empty.")

            if new_password != confirm_password:
                errors.append("Passwords do not match.")

            valid, msg = validate_password(new_password)
            if not valid:
                errors.append(msg)

            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template("settings.html", user=user)

            hashed = bcrypt.generate_password_hash(new_password).decode("utf-8")

            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed, session['user_id'])
            )

            conn.execute(
                "INSERT INTO recent_activity (message) VALUES (?)",
                (f"User '{session['username']}' updated password",)
            )

            conn.commit()
            conn.close()

            flash("Password updated successfully!", "success")
            return redirect(url_for("settings"))

    conn.close()
    return render_template("settings.html", user=user)




# ============================================
#   VIEW SINGLE PATIENT
# ============================================

@app.route("/patient/<int:id>")
@login_required
def view_patient(id):
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
    conn.close()

    if not patient:
        flash("Patient not found!", "danger")
        return redirect(url_for("view_patients"))

    return render_template("single_patient.html", patient=patient)



# ============================================
#   EDIT PATIENT
# ============================================


@app.route("/patient/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_patient(id):
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()

    if not patient:
        flash("Patient not found!", "danger")
        conn.close()
        return redirect(url_for("view_patients"))

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]
        gender = request.form["gender"]
        medical_history = request.form["medical_history"]

        conn.execute("""
            UPDATE patients SET first_name=?, last_name=?, phone=?, email=?, 
            address=?, gender=?, medical_history=? WHERE id=?
        """, (first_name, last_name, phone, email, address, gender, medical_history, id))

        conn.commit()
        conn.close()
        flash("Patient updated successfully!", "success")
        return redirect(url_for("view_patients"))

    conn.close()
    return render_template("edit_patient.html", patient=patient)


# ============================================
#   DELETE PATIENT
# ============================================


@app.route("/patient/<int:id>/delete")
@login_required
def delete_patient(id):
    conn = get_db()
    conn.execute("DELETE FROM patients WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Patient deleted successfully!", "success")
    return redirect(url_for("view_patients"))



# ============================================
#   LOGOUT
# ============================================
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ============================================
#   ADMIN REQUIRED DECORATOR
# ============================================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "danger")
            return redirect(url_for("login"))
        
        conn = get_db()
        user = conn.execute("SELECT role FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        
        if user and user['role'] == 'admin':
            return f(*args, **kwargs)
        else:
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
    return wrapper


# ============================================
#   DOCTOR REQUIRED DECORATOR
# ============================================
def doctor_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "danger")
            return redirect(url_for("login"))
        
        conn = get_db()
        user = conn.execute("SELECT role FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        conn.close()
        
        if user and user['role'] in ['admin', 'doctor']:
            return f(*args, **kwargs)
        else:
            flash("Doctor access required.", "danger")
            return redirect(url_for("dashboard"))
    return wrapper


# ============================================
#   ADMIN DASHBOARD
# ============================================
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    
    # Get statistics
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    total_appointments = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    total_revenue = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM billing WHERE status='Paid'").fetchone()[0]
    
    # Recent activities - handle if table doesn't have created_at
    try:
        recent_activities = conn.execute("""
            SELECT * FROM recent_activity ORDER BY ROWID DESC LIMIT 10
        """).fetchall()
    except:
        recent_activities = []
    
    # System stats
    model_stats = get_model_stats()
    
    conn.close()
    
    return render_template(
        'admin.html',
        total_users=total_users,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_revenue=total_revenue,
        recent_activities=recent_activities,
        model_stats=model_stats
    )


# ============================================
#   ADMIN - MANAGE USERS
# ============================================
@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    
    return render_template('admin_users.html', users=users)


# ============================================
#   ADMIN - UPDATE USER ROLE
# ============================================
@app.route('/admin/user/<int:user_id>/role/<string:new_role>')
@admin_required
def admin_update_user_role(user_id, new_role):
    if new_role not in ['admin', 'user', 'doctor']:
        flash("Invalid role.", "danger")
        return redirect(url_for("admin_users"))
    
    conn = get_db()
    
    # Prevent changing own role
    if user_id == session['user_id']:
        flash("Cannot change your own role.", "danger")
    else:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.execute(
            "INSERT INTO recent_activity (message) VALUES (?)",
            (f"User role updated to {new_role}",)
        )
        conn.commit()
        flash(f"User role updated to {new_role}!", "success")
    
    conn.close()
    return redirect(url_for("admin_users"))


# ============================================
#   ADMIN - DELETE USER
# ============================================
@app.route('/admin/user/<int:user_id>/delete')
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user_id']:
        flash("Cannot delete your own account.", "danger")
        return redirect(url_for("admin_users"))
    
    conn = get_db()
    username = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()[0]
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.execute(
        "INSERT INTO recent_activity (message) VALUES (?)",
        (f"User '{username}' deleted",)
    )
    conn.commit()
    conn.close()
    
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin_users"))


# ============================================
#   ADMIN - SYSTEM SETTINGS
# ============================================
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'backup':
            try:
                os.makedirs('backups', exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"hospital_backup_{timestamp}.db"
                shutil.copy('hospital.db', f'backups/{backup_name}')
                
                conn = get_db()
                conn.execute(
                    "INSERT INTO recent_activity (message) VALUES (?)",
                    (f"Database backup created: {backup_name}",)
                )
                conn.commit()
                conn.close()
                
                flash("Database backed up successfully!", "success")
            except Exception as e:
                flash(f"Backup failed: {str(e)}", "danger")
        
        elif action == 'train_model':
            try:
                # Train the model
                success = stroke_predictor.train_model() if hasattr(stroke_predictor, 'train_model') else False
                conn = get_db()
                conn.execute(
                    "INSERT INTO recent_activity (message) VALUES (?)",
                    (f"ML model training {'completed' if success else 'failed'}",)
                )
                conn.commit()
                conn.close()
                
                if success:
                    flash("Machine Learning model trained successfully!", "success")
                else:
                    flash("Model is already trained and ready.", "info")
            except Exception as e:
                flash(f"Model training error: {str(e)}", "danger")
        
        return redirect(url_for("admin_settings"))
    
    model_stats = get_model_stats()
    return render_template('admin_settings.html', model_stats=model_stats)


# ============================================
#   ADMIN - SYSTEM REPORTS
# ============================================
@app.route('/admin/reports')
@admin_required
def admin_reports():
    conn = get_db()
    
    # System analytics
    users_by_role = conn.execute("""
        SELECT role, COUNT(*) as count FROM users GROUP BY role
    """).fetchall()
    
    patients_monthly = []
    for m in range(1, 13):
        count = conn.execute(
            "SELECT COUNT(*) FROM patients WHERE strftime('%m', created_at) = ?",
            (f"{m:02}",)
        ).fetchone()[0]
        patients_monthly.append(count)
    
    revenue_status = {
        'paid': conn.execute("SELECT COALESCE(SUM(amount), 0) FROM billing WHERE status='Paid'").fetchone()[0],
        'unpaid': conn.execute("SELECT COALESCE(SUM(amount), 0) FROM billing WHERE status='Unpaid'").fetchone()[0],
        'cancelled': conn.execute("SELECT COALESCE(SUM(amount), 0) FROM billing WHERE status='Cancelled'").fetchone()[0]
    }
    
    conn.close()
    
    return render_template(
        'admin_reports.html',
        users_by_role=users_by_role,
        patients_monthly=patients_monthly,
        revenue_status=revenue_status
    )


# ============================================
#   DOCTOR DASHBOARD
# ============================================
@app.route('/doctor/dashboard')
@doctor_required
def doctor_dashboard():
    conn = get_db()
    
    # Get statistics
    stats = DoctorAnalytics.get_doctor_dashboard_stats()
    
    # Get recent patients
    recent_patients = conn.execute("""
        SELECT * FROM patients ORDER BY created_at DESC LIMIT 10
    """).fetchall()
    
    # Get high risk patients
    high_risk_patients = DoctorAnalytics.get_high_risk_patients()
    
    conn.close()
    
    return render_template(
        'doctor_dashboard.html',
        stats=stats,
        recent_patients=recent_patients,
        high_risk_patients=high_risk_patients
    )


# ============================================
#   HEALTH RISK ASSESSMENT
# ============================================
@app.route('/assess-health-risk', methods=['GET', 'POST'])
def assess_health_risk():
    # Restrict patient access to health risk assessment
    if session.get('role') == 'patient':
        flash("Access restricted. Patients cannot access health risk assessment.", "danger")
        return redirect(url_for('appointments'))
    
    result = None
    patient_history = None
    assessment_history = []
    risk_trend = None
    patient_id = None
    patient_info = None
    
    # Get patient_id from query parameter if available
    if request.method == 'GET':
        patient_id = request.args.get('patient_id')
        if patient_id:
            try:
                patient_id = int(patient_id)
                patient_info = stroke_predictor.get_patient_health_history(patient_id)
                assessment_history = stroke_predictor.get_patient_assessment_history(patient_id)
                risk_trend = stroke_predictor.get_risk_trend(patient_id)
            except:
                patient_id = None
    
    if request.method == 'POST':
        try:
            # Get patient_id from form
            patient_id = request.form.get('patient_id', '').strip()
            patient_id = int(patient_id) if patient_id else None
            
            # Prepare patient data from form (user input)
            form_data = {
                'gender': request.form.get('gender', 'Male'),
                'age': float(request.form.get('age', 30)),
                'hypertension': 1 if request.form.get('hypertension') else 0,
                'heart_disease': 1 if request.form.get('heart_disease') else 0,
                'ever_married': request.form.get('ever_married', 'Yes'),
                'work_type': request.form.get('work_type', 'Private'),
                'Residence_type': request.form.get('Residence_type', 'Urban'),
                'avg_glucose_level': float(request.form.get('avg_glucose_level', 100)),
                'bmi': float(request.form.get('bmi', 25)) if request.form.get('bmi') else 25,
                'smoking_status': request.form.get('smoking_status', 'never smoked')
            }
            
            # Get patient history from database if patient_id provided
            if patient_id:
                logger.info(f"Loading history for patient_id: {patient_id}")
                patient_info = stroke_predictor.get_patient_health_history(patient_id)
                assessment_history = stroke_predictor.get_patient_assessment_history(patient_id)
                risk_trend = stroke_predictor.get_risk_trend(patient_id)
                logger.info(f"Patient info: {patient_info}, Assessments: {len(assessment_history)}")
            
            # ENHANCED: Combine form data with patient database history
            combined_data = stroke_predictor.get_combined_patient_data(form_data, patient_id)
            logger.info(f"Combined data keys: {combined_data.keys()}")
            
            # Make prediction with COMBINED data (form + database history)
            result = stroke_predictor.predict(combined_data)
            logger.info(f"Prediction result: {result}")
            
            if result and patient_id:
                # Save assessment to database for history tracking
                stroke_predictor.save_assessment(patient_id, form_data, result)
                
                # Refresh assessment history and trend after saving
                assessment_history = stroke_predictor.get_patient_assessment_history(patient_id)
                risk_trend = stroke_predictor.get_risk_trend(patient_id)
                
                # Log doctor activity if current user is a doctor
                if session.get('role') == 'doctor':
                    try:
                        conn = get_db()
                        doctor_id_result = conn.execute('SELECT id FROM doctors WHERE user_id = ?', (session['user_id'],)).fetchone()
                        conn.close()
                        if doctor_id_result:
                            activity_logger = DoctorActivityLogger()
                            activity_logger.log_activity(
                                doctor_id_result[0],
                                'health_assessment',
                                f'Assessed health risk - Risk Level: {result.get("risk_level", "Unknown")}',
                                patient_id
                            )
                    except Exception as e:
                        logger.error(f"Error logging doctor activity: {str(e)}")
            
            if result:
                result['now'] = datetime.now()
        
        except Exception as e:
            logger.error(f"Error in assessment: {str(e)}", exc_info=True)
            flash(f"Error in assessment: {str(e)}", "danger")
    
    # Get all patients for dropdown
    try:
        conn = get_db()
        patients = conn.execute("SELECT id, first_name, last_name FROM patients ORDER BY first_name").fetchall()
        conn.close()
    except:
        patients = []
    
    return render_template(
        'patient_health_risk.html',
        result=result,
        now=datetime.now(),
        patient_id=patient_id,
        patient_info=patient_info,
        assessment_history=assessment_history,
        risk_trend=risk_trend,
        patients=patients
    )


# ============================================================================
# OPTION C: DOCTOR SYSTEM ROUTES
# ============================================================================

@app.route('/doctor/profile')
@login_required
def doctor_profile():
    """Display doctor profile and statistics"""
    if session.get('role') != 'doctor' and session.get('role') != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user_id = session.get('user_id')
        doctor_profile_mgr = DoctorProfile()
        activity_logger = DoctorActivityLogger()
        
        # Get or create doctor profile
        profile = doctor_profile_mgr.get_or_create_profile(user_id)
        
        if not profile:
            profile = doctor_profile_mgr.get_or_create_profile(user_id)
        
        # Get doctor ID
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (user_id,))
        doctor_row = cursor.fetchone()
        conn.close()
        
        if not doctor_row:
            flash('Doctor profile not found', 'error')
            return redirect(url_for('dashboard'))
        
        doctor_id = doctor_row['id']
        
        # Get full profile with stats
        profile = doctor_profile_mgr.get_profile_by_id(doctor_id)
        
        # Get recent activities
        recent_activities = activity_logger.get_doctor_activities(doctor_id, limit=10)
        
        # Get activity summary
        activity_summary = activity_logger.get_activity_summary(doctor_id)
        
        return render_template(
            'doctor_profile.html',
            profile=profile,
            recent_activities=recent_activities,
            activity_summary=activity_summary,
            now=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in doctor_profile: {str(e)}")
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/doctor/my-patients')
@login_required
def doctor_my_patients():
    """Display patients assigned to current doctor"""
    if session.get('role') != 'doctor' and session.get('role') != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user_id = session.get('user_id')
        
        # Get doctor ID
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (user_id,))
        doctor_row = cursor.fetchone()
        conn.close()
        
        if not doctor_row:
            flash('Doctor profile not found', 'error')
            return redirect(url_for('dashboard'))
        
        doctor_id = doctor_row['id']
        
        # Get assigned patients
        assignment_mgr = DoctorPatientAssignment()
        patients = assignment_mgr.get_doctor_patients(doctor_id)
        
        # Get activity logger
        activity_logger = DoctorActivityLogger()
        
        return render_template(
            'doctor_dashboard.html',
            patients=patients,
            doctor_id=doctor_id,
            now=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in doctor_my_patients: {str(e)}")
        flash(f'Error loading patients: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/doctor/my-activities')
@login_required
def doctor_my_activities():
    """Display activity log for current doctor"""
    if session.get('role') != 'doctor' and session.get('role') != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user_id = session.get('user_id')
        
        # Get doctor ID
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM doctors WHERE user_id = ?', (user_id,))
        doctor_row = cursor.fetchone()
        conn.close()
        
        if not doctor_row:
            flash('Doctor profile not found', 'error')
            return redirect(url_for('dashboard'))
        
        doctor_id = doctor_row['id']
        
        # Get activities
        activity_logger = DoctorActivityLogger()
        activities = activity_logger.get_doctor_activities(doctor_id, limit=100)
        activity_summary = activity_logger.get_activity_summary(doctor_id)
        
        return render_template(
            'doctor_activities.html',
            activities=activities,
            activity_summary=activity_summary,
            now=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in doctor_my_activities: {str(e)}")
        flash(f'Error loading activities: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/admin/doctors')
@login_required
@admin_required
def admin_doctors():
    """Admin view: manage all doctors"""
    try:
        doctor_profile_mgr = DoctorProfile()
        activity_logger = DoctorActivityLogger()
        
        # Get all doctors
        doctors = doctor_profile_mgr.get_all_doctors()
        
        # Get overall activity statistics
        total_activities = activity_logger.get_all_activities(limit=1000)
        
        # Calculate system stats
        stats = {
            'total_doctors': len(doctors),
            'total_patients': sum(d.get('patient_count', 0) for d in doctors),
            'total_activities': len(total_activities),
            'active_doctors': sum(1 for d in doctors if d.get('availability_status') == 'available'),
        }
        
        # Get recent system activities
        recent_activities = activity_logger.get_all_activities(limit=20)
        
        return render_template(
            'admin_doctors.html',
            doctors=doctors,
            stats=stats,
            recent_activities=recent_activities,
            now=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in admin_doctors: {str(e)}")
        flash(f'Error loading doctors: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))


@app.route('/admin/doctor/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_doctor(doctor_id):
    """Admin: edit doctor profile"""
    doctor_profile_mgr = DoctorProfile()
    
    if request.method == 'POST':
        try:
            updates = {
                'specialization': request.form.get('specialization'),
                'contact_number': request.form.get('contact_number'),
                'qualification': request.form.get('qualification'),
                'experience_years': request.form.get('experience_years', type=int),
                'consultation_fee': request.form.get('consultation_fee', type=float),
                'bio': request.form.get('bio'),
                'availability_status': request.form.get('availability_status'),
            }
            
            if doctor_profile_mgr.update_profile(doctor_id, **updates):
                flash('Doctor profile updated successfully', 'success')
            else:
                flash('Error updating doctor profile', 'error')
        except Exception as e:
            logger.error(f"Error updating doctor: {str(e)}")
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('admin_doctors'))
    
    # GET request - show edit form
    profile = doctor_profile_mgr.get_profile_by_id(doctor_id)
    
    if not profile:
        flash('Doctor not found', 'error')
        return redirect(url_for('admin_doctors'))
    
    return render_template('doctor_edit.html', doctor=profile, now=datetime.now())


@app.route('/api/doctor/<int:doctor_id>/assign-patient', methods=['POST'])
@login_required
def api_assign_patient(doctor_id):
    """API: Assign patient to doctor"""
    if session.get('role') != 'admin' and session.get('role') != 'doctor':
        return {'error': 'Unauthorized'}, 403
    
    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        notes = data.get('notes', '')
        
        assignment_mgr = DoctorPatientAssignment()
        if assignment_mgr.assign_patient(doctor_id, patient_id, notes):
            # Log the activity
            activity_logger = DoctorActivityLogger()
            activity_logger.log_activity(doctor_id, 'patient_assigned', f'Assigned patient ID: {patient_id}', patient_id)
            
            return {'success': True, 'message': 'Patient assigned'}, 200
        else:
            return {'error': 'Assignment failed'}, 400
    except Exception as e:
        logger.error(f"Error assigning patient: {str(e)}")
        return {'error': str(e)}, 500


# ============================================
#   RUN APP
# ============================================
if __name__ == "__main__":
    app.run(debug=True)
