# Stroke Prediction Patient Data Management System

A secure web-based Flask application for managing patient stroke prediction data for healthcare professionals. This system demonstrates professional secure software development practices including authentication, encryption, input validation, and comprehensive error handling.

## Overview

According to the World Health Organization (WHO), stroke is the second leading cause of death globally. This application helps healthcare professionals record, manage, and analyze patient data covering demographics, medical history, and lifestyle factors to predict stroke likelihood and assist in preventive healthcare.

## Features

### Core Functionality
- **Complete CRUD Operations**: Create, Read, Update, and Delete patient records
- **User Authentication**: Secure registration and login system
- **Patient Search**: Search and filter patient records
- **Dashboard Analytics**: Visual statistics and data insights
- **Risk Assessment**: Automatic calculation of stroke risk factors

### Security Features
- **Password Hashing**: Using Werkzeug's PBKDF2-SHA256 algorithm
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Input Validation**: Server-side validation for all user inputs
- **Input Sanitization**: XSS prevention through input sanitization
- **SQL Injection Prevention**: Parameterized queries for SQLite
- **NoSQL Injection Prevention**: Input validation for MongoDB operations
- **Secure Session Handling**: HTTPOnly, SameSite cookies
- **Error Logging**: Comprehensive application logging

## Technology Stack

### Backend
- **Flask 3.0.0**: Web framework
- **SQLite**: User authentication database
- **MongoDB**: Patient records database
- **Flask-Login**: Session management
- **Flask-WTF**: Form handling and CSRF protection
- **Bcrypt**: Password hashing
- **Pandas**: Data processing

### Frontend
- **Bootstrap 5.3.0**: Responsive UI framework
- **Bootstrap Icons**: Icon library
- **Jinja2 Templates**: Server-side templating

## Database Architecture

### SQLite (User Authentication)
```
users table:
- id (PRIMARY KEY)
- username (UNIQUE)
- email (UNIQUE)
- password_hash
- created_at
- last_login
```

### MongoDB (Patient Records)
```
patients collection:
- _id (ObjectId)
- id (patient ID)
- gender
- age
- hypertension
- heart_disease
- ever_married
- work_type
- Residence_type
- avg_glucose_level
- bmi
- smoking_status
- stroke
- created_by (username)
- created_at
- updated_by (username)
- updated_at
```

## Installation

### Prerequisites
- Python 3.8 or higher
- MongoDB installed and running locally
- pip (Python package manager)

### Setup Instructions

1. **Clone or navigate to the project directory**
```bash
cd /Users/kennethnwankwo/Documents/ifeoma
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
```

3. **Activate the virtual environment**
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

4. **Install required packages**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables**
```bash
cp .env.example .env
```

Edit the `.env` file and set your configurations:
```
SECRET_KEY=your-secret-key-here-change-this-in-production
MONGO_URI=mongodb://localhost:27017/
SESSION_COOKIE_SECURE=False
```

6. **Start MongoDB**
```bash
# On macOS with Homebrew:
brew services start mongodb-community

# On Linux:
sudo systemctl start mongod

# On Windows:
# MongoDB should start automatically as a service
# Or run: net start MongoDB
```

7. **Import the dataset into MongoDB**
```bash
python import_data.py
```

This will import all patient records from the CSV file into MongoDB.

8. **Run the application**
```bash
python app.py
```

The application will be available at: `http://127.0.0.1:5000`

## Usage

### First Time Setup

1. **Register a new account**
   - Navigate to `http://127.0.0.1:5000`
   - Click "Register"
   - Create an account with:
     - Username (3-50 characters, alphanumeric and underscores)
     - Valid email address
     - Strong password (min 8 chars, uppercase, lowercase, digit)

2. **Login**
   - Use your credentials to log in
   - You'll be redirected to the dashboard

### Managing Patients

#### View Patients
- Click "Patients" in the navigation bar
- Browse through paginated patient records (20 per page)
- Use the search bar to find specific patients

#### Add New Patient
- Click "Add Patient" or the "+" button
- Fill in all required fields:
  - **Personal Info**: ID, gender, age, marital status, work type, residence
  - **Medical Info**: Hypertension, heart disease, glucose level, BMI, smoking status, stroke
- Click "Add Patient" to save

#### View Patient Details
- Click the eye icon on any patient row
- View complete patient information
- See calculated risk assessment based on factors:
  - Hypertension
  - Heart disease
  - Age 65+
  - Current smoking
  - High glucose level (>140 mg/dL)

#### Edit Patient
- Click the pencil icon on any patient row
- Modify the necessary fields
- Click "Edit Patient" to save changes

#### Delete Patient
- Click the trash icon on any patient row
- Confirm deletion in the popup dialog
- Patient will be permanently removed

### Dashboard
The dashboard provides:
- Total patient count
- Stroke case statistics
- Gender distribution
- Quick action links
- Security features checklist

## Security Implementation

### 1. Authentication Security
- **Password Hashing**: All passwords are hashed using `pbkdf2:sha256` before storage
- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, and digits
- **Session Management**: Secure session cookies with 30-minute timeout
- **Login Protection**: Failed login attempts are logged

### 2. Input Validation
- **Server-Side Validation**: All inputs validated before processing
- **Type Checking**: Numeric fields verified for correct types and ranges
- **Enum Validation**: Categorical fields checked against allowed values
- **Email Validation**: Regex pattern matching for email format

### 3. Input Sanitization
- **XSS Prevention**: HTML/script tags removed from text inputs
- **Special Character Filtering**: Dangerous characters escaped
- **Query Parameterization**: All database queries use parameters

### 4. CSRF Protection
- **Token-Based Protection**: CSRF tokens on all forms
- **Flask-WTF Integration**: Automatic token validation
- **Session-Based Tokens**: Tokens tied to user sessions

### 5. Error Handling
- **Comprehensive Logging**: All errors logged with timestamps
- **User-Friendly Messages**: Generic error messages to users
- **Detailed Logs**: Technical details in log files only
- **Custom Error Pages**: 404 and 500 error handlers

### 6. Database Security
- **Parameterized Queries**: SQL injection prevention
- **Input Validation**: NoSQL injection prevention for MongoDB
- **Separate Databases**: User auth and patient data separated
- **Indexed Queries**: Efficient and secure data retrieval

## Ethical Considerations

This application handles sensitive healthcare data and implements several ethical safeguards:

1. **Data Confidentiality**: All patient data is protected with authentication
2. **Access Control**: Only authenticated users can view/modify data
3. **Audit Trail**: All data modifications are logged with user information
4. **Secure Storage**: Passwords hashed, sessions encrypted
5. **HIPAA Awareness**: While not fully HIPAA compliant, follows privacy best practices
6. **Data Integrity**: Input validation ensures data accuracy

## Project Structure

```
ifeoma/
├── app.py                              # Main Flask application
├── import_data.py                      # CSV data import script
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
├── healthcare-dataset-stroke-data.csv  # Patient dataset
├── users.db                            # SQLite database (created on first run)
├── app.log                             # Application logs (created on first run)
├── templates/                          # HTML templates
│   ├── base.html                       # Base template
│   ├── index.html                      # Home page
│   ├── login.html                      # Login page
│   ├── register.html                   # Registration page
│   ├── dashboard.html                  # Dashboard
│   ├── patients_list.html              # Patient list
│   ├── patient_detail.html             # Patient details
│   ├── patient_form.html               # Add/Edit patient form
│   ├── 404.html                        # 404 error page
│   └── 500.html                        # 500 error page
└── static/
    └── css/
        └── style.css                   # Custom styles
```

## Dataset Information

**Source**: Kaggle Stroke Prediction Dataset
**Link**: https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset

### Attributes
- `id`: Unique patient identifier
- `gender`: Male, Female, or Other
- `age`: Age of the patient
- `hypertension`: 0 = No, 1 = Yes
- `heart_disease`: 0 = No, 1 = Yes
- `ever_married`: No or Yes
- `work_type`: Children, Govt_job, Never_worked, Private, Self-employed
- `Residence_type`: Rural or Urban
- `avg_glucose_level`: Average glucose level in blood (mg/dL)
- `bmi`: Body Mass Index
- `smoking_status`: formerly smoked, never smoked, smokes, Unknown
- `stroke`: 1 = Had stroke, 0 = No stroke

## Testing

### Manual Testing Checklist

#### Authentication
- [ ] Register with valid credentials
- [ ] Register with weak password (should fail)
- [ ] Register with existing username (should fail)
- [ ] Login with correct credentials
- [ ] Login with incorrect credentials (should fail)
- [ ] Session timeout after 30 minutes
- [ ] Logout functionality

#### Patient Management
- [ ] Add new patient with valid data
- [ ] Add patient with invalid data (should show errors)
- [ ] View patient list with pagination
- [ ] Search patients by various criteria
- [ ] View patient details
- [ ] Edit patient information
- [ ] Delete patient
- [ ] Attempt to add duplicate patient ID (should fail)

#### Security
- [ ] CSRF token present on all forms
- [ ] SQL injection attempts blocked
- [ ] XSS attempts sanitized
- [ ] Unauthorized access redirects to login
- [ ] Password displayed as asterisks
- [ ] Errors logged to app.log

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
brew services list  # macOS
sudo systemctl status mongod  # Linux

# Start MongoDB if not running
brew services start mongodb-community  # macOS
sudo systemctl start mongod  # Linux
```

### Import Data Issues
- Ensure `healthcare-dataset-stroke-data.csv` is in the project root
- Verify MongoDB is running
- Check MongoDB connection string in `.env`

### Application Won't Start
- Verify virtual environment is activated
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check port 5000 is not already in use

## Production Deployment Considerations

For production deployment, make sure to:

1. **Set a strong SECRET_KEY** in environment variables
2. **Enable HTTPS** and set `SESSION_COOKIE_SECURE=True`
3. **Use a production WSGI server** (gunicorn, uWSGI)
4. **Configure MongoDB authentication** and use connection string with credentials
5. **Set up proper logging** with rotation
6. **Implement rate limiting** for login attempts
7. **Regular security audits** and dependency updates
8. **Backup strategy** for both databases
9. **Set DEBUG=False** in production
10. **Configure proper firewall rules**

## License

This project is created for educational purposes as part of a secure programming assessment.

## Author

Ifeoma

## Acknowledgments

- World Health Organization (WHO) for stroke statistics
- Kaggle for the stroke prediction dataset
- Flask and Python communities for excellent documentation
# project-view
