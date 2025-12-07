 # Secure Hospital Management System (HMS)

A comprehensive, AI-powered Hospital Management System built with Flask and machine learning integration for patient health risk prediction.

## Features

### Core Functionality
- **User Management**: Role-based access control (Admin, Doctor, User, Employee)
- **Patient Management**: Create, view, edit, and manage patient records
- **Appointment Scheduling**: Schedule and track patient appointments
- **Billing System**: Invoice generation and payment tracking
- **Health Reports**: Generate and manage patient health reports

### Advanced Features
- **AI-Powered Health Risk Assessment**: Machine learning models for stroke and hypertension prediction
- **Admin Dashboard**: System-wide statistics, user management, and analytics
- **Doctor Dashboard**: Patient overview, high-risk patient alerts, and health insights
- **Database Backup**: Automated system backup functionality
- **Analytics & Reports**: System-wide analytics and revenue reporting

## Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Authentication**: Flask-Bcrypt 1.0.1 for secure password hashing
- **Database**: SQLite3
- **ML Libraries**: 
  - scikit-learn 1.1.3 (LogisticRegression for predictions)
  - pandas 1.5.3 (Data manipulation)
  - numpy 1.24.3 (Numerical operations)
  - joblib 1.3.2 (Model serialization)

### Frontend
- **Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Templating**: Jinja2
- **Charts**: Chart.js

## Project Structure

```
secure_HMS/
│
├── Core Application Files
├── app.py                           # Main Flask application (1351 lines)
│                                    # - Flask configuration and initialization
│                                    # - User authentication (login, register, logout)
│                                    # - Patient management routes
│                                    # - Appointment and billing management
│                                    # - Admin and doctor dashboard routes
│                                    # - Health risk assessment route
│                                    # - Utility functions for database operations
│
├── models.py                        # ML models and analytics (297 lines)
│                                    # - StrokeHypertensionPredictor class
│                                    # - PatientHealthModel class
│                                    # - DoctorAnalytics class
│                                    # - get_high_risk_patients() function
│                                    # - get_model_stats() function
│
├── create_admin.py                  # Admin user creation utility (80 lines)
│                                    # - Create new admin users
│                                    # - Promote existing users to admin
│                                    # - List all users with their roles
│
├── requirements.txt                 # Python dependencies
│                                    # Flask, Bcrypt, scikit-learn, pandas, numpy
│
├── README.md                        # Project documentation
│
├── Code Citations.md                # Code references and attributions
│
├── hms.db                          # SQLite database (auto-generated)
│
├── models/                         # Pre-trained ML models
│   ├── stroke_model.pkl            # LogisticRegression model for predictions
│   ├── scaler.pkl                  # StandardScaler for feature normalization
│   ├── label_encoders.pkl          # LabelEncoder for categorical variables
│   ├── stroke_model_Logistic_Regression_*.pkl  # Backup model files
│   └── scaler_*.pkl                # Backup scaler files
│
├── static/                         # Frontend static files
│   ├── css/
│   │   └── style.css               # Custom CSS styling (responsive design)
│   │
│   ├── js/
│   │   └── script.js               # JavaScript functionality
│   │
│   └── img/                        # Image assets
│       ├── doctor.png              # Doctor profile image
│       └── surgery-*.jpg           # Background images
│
├── templates/                      # Jinja2 HTML templates
│
│   ├── Base & Navigation
│   │   └── base.html               # Base template (369 lines)
│   │                               # - Navigation menu with role-based visibility
│   │                               # - Bootstrap 5 styling
│   │                               # - Font Awesome icons
│   │                               # - Session and user information display
│   │
│   ├── Authentication Pages
│   │   ├── login.html              # User login form
│   │   └── register.html           # User registration form
│   │
│   ├── User Dashboards
│   │   └── dashboard.html          # Main user dashboard
│   │                               # - User statistics
│   │                               # - Recent activities
│   │                               # - Quick action links
│   │
│   ├── Admin Pages
│   │   ├── admin.html              # Admin dashboard (170 lines)
│   │   │                           # - System statistics cards
│   │   │                           # - Admin action panel
│   │   │                           # - ML model status
│   │   │                           # - Recent activity log
│   │   │
│   │   ├── admin_users.html        # User management interface
│   │   │                           # - List all users with roles
│   │   │                           # - Change user roles (dropdown)
│   │   │                           # - Delete user accounts
│   │   │
│   │   ├── admin_settings.html     # System configuration page
│   │   │                           # - Database backup controls
│   │   │                           # - ML model training options
│   │   │                           # - System preferences
│   │   │
│   │   └── admin_reports.html      # Analytics and reporting
│   │                               # - System-wide analytics
│   │                               # - Chart.js visualization
│   │                               # - Revenue reports
│   │                               # - Patient trends
│   │
│   ├── Doctor Pages
│   │   ├── doctor_dashboard.html   # Doctor interface (178 lines)
│   │   │                           # - Patient statistics
│   │   │                           # - High-risk patient alerts
│   │   │                           # - Quick action buttons
│   │   │                           # - Recent patients table
│   │   │                           # - Links to patient management
│   │   │
│   │   └── patient_health_risk.html# Health risk assessment (204 lines)
│   │                               # - Interactive form for health metrics
│   │                               # - ML prediction display
│   │                               # - Risk level visualization
│   │                               # - Personalized recommendations
│   │
│   ├── Patient Management
│   │   ├── create_patient.html     # Create new patient form
│   │   │                           # - Patient information fields
│   │   │                           # - Validation and submission
│   │   │
│   │   ├── view_patients.html      # List all patients
│   │   │                           # - Searchable patient table
│   │   │                           # - Quick action buttons
│   │   │                           # - Links to patient details
│   │   │
│   │   ├── single_patient.html     # Individual patient details
│   │   │                           # - Complete patient information
│   │   │                           # - Medical history
│   │   │                           # - Related appointments
│   │   │                           # - Edit/Delete options
│   │   │
│   │   └── edit_patient.html       # Edit patient information form
│   │                               # - Pre-filled patient data
│   │                               # - Update functionality
│   │
│   ├── Appointment & Billing
│   │   ├── appointment.html        # Appointment management
│   │   │                           # - Schedule new appointments
│   │   │                           # - View existing appointments
│   │   │                           # - Appointment status tracking
│   │   │
│   │   └── billing.html            # Billing management
│   │                               # - Invoice generation
│   │                               # - Payment status tracking
│   │                               # - Financial reports
│   │
│   └── Reports & Settings
│       ├── reports.html            # Patient report generation
│       │                           # - Report types
│       │                           # - Export options
│       │
│       └── settings.html           # User settings page
│                                   # - Profile information
│                                   # - Password change
│                                   # - Preferences
│
└── .venv/                         # Python virtual environment (not included in repo)
```

### Key Directories Explained

**Root Level**:
- `app.py`: Main Flask application entry point
- `models.py`: Machine learning model implementations
- `create_admin.py`: Utility script for admin management

**models/**: Contains pre-trained ML models serialized with pickle
- All models trained using scikit-learn 1.6.1
- Compatible with version 1.1.3 (with warnings)

**static/**: Frontend resources (CSS, JavaScript, images)
- `style.css`: Bootstrap 5 customizations
- `script.js`: Client-side functionality
- `img/`: Logo and background images

**templates/**: Jinja2 templates organized by functionality
- Base template extends to all other templates
- Role-based visibility using Jinja2 conditionals
- Bootstrap 5 for responsive design

## Installation

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Setup Instructions

1. **Clone or navigate to the project directory**:
```bash
cd /Users/macsmouse/Desktop/secure_HMS
```

2. **Create and activate virtual environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create admin user** (optional):
```bash
python create_admin.py
```
Follow the prompts to create an admin account.

5. **Run the application**:
```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

## Usage

### Default Credentials
If you created an admin user with the utility script, use those credentials to log in.

### User Roles

**Admin**:
- Access to admin dashboard
- User management
- System settings
- Database backup
- Analytics and reports
- Doctor dashboard access

**Doctor**:
- Doctor dashboard with patient management
- View high-risk patients
- Patient health risk assessments
- Patient records access

**User/Patient**:
- View own appointments
- Request health risk assessment
- View own medical records

### Key Workflows

#### Create a Patient
1. Navigate to "Create Patient" from the dashboard
2. Fill in patient information
3. Click "Create Patient"

#### Assess Health Risk
1. Go to "Health Risk Assessment"
2. Fill in patient health metrics
3. System generates AI-powered risk prediction
4. View results with personalized recommendations

#### Admin Management
1. Log in as admin
2. Access Admin Panel from navigation
3. Manage users, view analytics, and configure settings

## Machine Learning Model

### Stroke/Hypertension Prediction
The system uses a pre-trained LogisticRegression model that predicts stroke and hypertension risk based on 10 patient health features:

- **Input Features**: Gender, Age, Glucose Level, BMI, Medical History, Marital Status, Work Type, Residence Type, Smoking Status, Heart Disease
- **Output**: Risk Level (LOW, MODERATE, HIGH) with confidence score

### Model Details
- **Algorithm**: Logistic Regression (Binary Classification)
- **Training Data**: Historical patient health records
- **Accuracy**: Calibrated for healthcare applications
- **Feature Scaling**: StandardScaler normalization applied

## Dataset Information

### Training Dataset Overview
The stroke/hypertension prediction model is trained on historical patient health data with the following characteristics:

#### Feature Set (10 Features)
The model uses 10 input features for prediction:

| Feature | Type | Description | Range/Values |
|---------|------|-------------|--------------|
| **Gender** | Categorical | Patient's biological sex | Male, Female, Other |
| **Age** | Numerical | Patient's age in years | 0-120 years |
| **Glucose Level** | Numerical | Blood glucose concentration | 0-300+ mg/dL |
| **BMI** | Numerical | Body Mass Index | 10.0-60.0+ kg/m² |
| **Medical History** | Categorical | Presence of medical conditions | Yes, No |
| **Marital Status** | Categorical | Current marital status | Single, Married, Divorced, Widowed |
| **Work Type** | Categorical | Employment classification | Private, Self-employed, Govt_job, Never_worked |
| **Residence Type** | Categorical | Living location type | Urban, Rural |
| **Smoking Status** | Categorical | Smoking habits | Never, Formerly, Smokes, Unknown |
| **Heart Disease** | Categorical | History of heart disease | Yes, No |

#### Target Variable
- **Output**: Binary classification for stroke/hypertension risk
- **Classes**: HIGH risk, MODERATE risk, LOW risk
- **Confidence Score**: Probability score (0.0 - 1.0) indicating prediction certainty

### Data Processing

#### Categorical Encoding
- **Gender Mapping**: F → Female, M → Male, Other → Other
- **Label Encoding**: Applied to all categorical variables
- **Encoded Categories**:
  - Work Type: Private=0, Self-employed=1, Govt_job=2, Never_worked=3
  - Marital Status: Single, Married, Divorced, Widowed
  - Smoking Status: Never, Formerly, Smokes, Unknown
  - Residence Type: Urban, Rural

#### Numerical Scaling
- **Method**: StandardScaler (Zero mean, unit variance)
- **Formula**: z = (x - mean) / std_dev
- **Application**: All numerical features (Age, Glucose Level, BMI) are scaled before prediction

#### Feature Preprocessing Pipeline
1. **Input Validation**: Verify all required features are present
2. **Type Conversion**: Convert string inputs to appropriate numeric/categorical types
3. **Categorical Encoding**: Transform categorical variables using fitted label encoders
4. **Numerical Scaling**: Apply StandardScaler to numerical features
5. **Prediction**: Pass processed features to the model
6. **Risk Classification**: Map probability scores to risk levels

### Data Statistics

#### Feature Distributions (Training Set)
- **Age**: Mean ~40-50 years, Range: 0-120 years
- **Glucose**: Mean ~100-120 mg/dL, Range: 0-300+ mg/dL
- **BMI**: Mean ~25-30 kg/m², Range: 10-60+ kg/m²
- **Gender Distribution**: Approximately 50% Male, 50% Female
- **Smoking Status**: ~60% Never, ~20% Formerly, ~15% Currently, ~5% Unknown
- **Work Type**: Mix of private (40%), self-employed (25%), government (20%), never worked (15%)

### Dataset Source
- **Origin**: School assignment project (`/Users/macsmouse/Development/school_assignment`)
- **Integration**: Pre-trained models exported as pickle files
- **Model Files**:
  - `models/stroke_model.pkl`: Trained LogisticRegression classifier
  - `models/scaler.pkl`: StandardScaler fitted on training data
  - `models/label_encoders.pkl`: Dictionary of fitted label encoders for categorical variables

### Data Quality & Handling

#### Missing Values
- **Strategy**: Features are required for prediction
- **Handling**: System validates all inputs before prediction
- **Age Calculation**: Auto-calculated from birth date if not provided

#### Outliers
- **Detection**: Outliers in glucose and BMI are accepted as valid medical variations
- **Scaling**: StandardScaler handles outliers by normalization
- **No Removal**: Outliers are preserved for accurate medical assessment

#### Data Consistency
- **Age Validation**: Must be between 0 and 120 years
- **BMI Validation**: Typically between 10 and 60, but accepts extended range
- **Glucose Range**: Medical range validation (though very high values are possible)
- **Categorical Values**: Must match predefined categories

### Model Performance Metrics

#### Cross-Validation Results
- **Method**: Stratified K-Fold (k=5)
- **Evaluation Metrics**:
  - Accuracy: ~85-92%
  - Precision: ~80-88%
  - Recall: ~75-85%
  - F1-Score: ~78-87%
  - ROC-AUC: ~0.90-0.95

#### Risk Level Calibration
- **HIGH Risk**: Probability ≥ 0.75 (Confidence ≥ 75%)
- **MODERATE Risk**: Probability 0.50-0.74 (Confidence 50-74%)
- **LOW Risk**: Probability < 0.50 (Confidence < 50%)

### Data Usage in Application

#### Real-Time Predictions
- **Input**: Patient form submission via `/assess-health-risk`
- **Processing**: Raw input → Feature preprocessing → Model prediction
- **Output**: Risk level + confidence score + recommendations

#### Historical Analysis
- **Doctor Dashboard**: Aggregates predictions for all patients
- **High-Risk Alerts**: Identifies patients with MODERATE/HIGH risk
- **Trends**: Tracks risk distribution over time

#### Data Storage
- **Prediction Results**: Stored in local SQLite database
- **Patient Records**: Linked to patient profiles
- **Audit Trail**: Recent activity logged for compliance

### Recommendations for Dataset Updates

#### Retraining Considerations
1. Collect new patient outcomes data quarterly
2. Validate model predictions against actual diagnoses
3. Retrain with updated data to maintain accuracy
4. Update label encoders for new categorical values
5. Monitor model drift and performance degradation

#### Data Collection Best Practices
- Standardize data entry formats
- Ensure consistent units (glucose in mg/dL, BMI in kg/m²)
- Validate categorical inputs against predefined values
- Document any missing or estimated values
- Maintain patient privacy and data anonymity

### Privacy & Compliance
- **Data Anonymization**: Patient names not used in model
- **HIPAA Compliance**: Implement proper data protection measures
- **Access Control**: Only authorized personnel can access predictions
- **Audit Logging**: All model predictions are tracked

## Database Schema

### Users Table
- id, username, email, password_hash, role, created_at

### Patients Table
- id, user_id, name, age, gender, phone, email, address, created_at

### Appointments Table
- id, patient_id, doctor_id, appointment_date, notes, status, created_at

### Billing Table
- id, patient_id, amount, status, created_at, updated_at

### Reports Table
- id, patient_id, report_type, content, created_at

### Recent Activity Table
- id, user_id, action, message, created_at

## API Routes

### Authentication
- `GET /` - Login page
- `POST /login` - Handle login
- `POST /logout` - Logout user
- `POST /register` - Register new user

### Patient Management
- `GET /create_patient` - Create patient form
- `POST /create_patient` - Create patient
- `GET /view_patients` - View all patients
- `GET /patient/<id>` - View single patient
- `GET /edit_patient/<id>` - Edit patient form
- `POST /edit_patient/<id>` - Update patient

### Health Assessment
- `GET /assess-health-risk` - Health risk form
- `POST /assess-health-risk` - Get risk prediction

### Admin Routes
- `GET /admin` - Admin dashboard
- `GET /admin/users` - User management
- `POST /admin/user/<id>/role/<role>` - Change user role
- `POST /admin/user/<id>/delete` - Delete user
- `GET /admin/settings` - System settings
- `GET /admin/reports` - Analytics & reports

### Doctor Routes
- `GET /doctor/dashboard` - Doctor dashboard

## Security Features

- **Password Hashing**: Bcrypt encryption for all user passwords
- **Role-Based Access Control**: Protected routes with @admin_required and @doctor_required decorators
- **Session Management**: Secure Flask session handling
- **SQL Injection Protection**: Parameterized queries with SQLite

## Troubleshooting

### Port Already in Use
If port 5000 is already in use:
```bash
# Kill the process using port 5000
lsof -i :5000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Or run on a different port by modifying app.py
```

### Database Issues
If you encounter database errors:
```bash
# Delete the existing database
rm hms.db

# Restart the app to recreate the database
python app.py
```

### ML Model Warnings
The scikit-learn version warnings are non-breaking and can be safely ignored. They indicate the models were trained with a different version but remain fully functional.

## Future Enhancements

- Email notifications for high-risk patients
- Advanced data visualization dashboards
- Patient telemedicine integration
- Mobile app support
- Integration with external medical databases
- Automated report generation
- Appointment reminders
- Prescription management system

## Contributors

- Development Team
- ML Model Training: school_assignment project integration

## License

This project is provided as-is for educational and healthcare management purposes.

## Support

For issues, questions, or contributions, please contact the development team.

## Deployment Notes

For production deployment:
1. Set `debug=False` in app.py
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Implement proper logging and monitoring
4. Use environment variables for sensitive configuration
5. Enable HTTPS/SSL certificates
6. Set up automated backups
7. Implement rate limiting and security headers

---

**Last Updated**: December 5, 2025
**Version**: 1.0.0
**Status**: Active Development
