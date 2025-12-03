# Security Implementation Documentation

This document details all security measures implemented in the Stroke Prediction Patient Data Management System.

## Table of Contents
1. [Authentication & Authorization](#authentication--authorization)
2. [Data Encryption](#data-encryption)
3. [Input Validation & Sanitization](#input-validation--sanitization)
4. [CSRF Protection](#csrf-protection)
5. [Injection Attack Prevention](#injection-attack-prevention)
6. [Session Management](#session-management)
7. [Error Handling & Logging](#error-handling--logging)
8. [Ethical Considerations](#ethical-considerations)

---

## Authentication & Authorization

### Password Security
**Implementation**: Lines 66-71 in [app.py](app.py#L66-L71)

```python
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
```

**Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Password Hashing
**Implementation**: Lines 211, 242 in [app.py](app.py#L211)

```python
# Registration (Line 211)
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# Login verification (Line 242)
check_password_hash(user_data[3], password)
```

**Algorithm**: PBKDF2-SHA256
- Industry-standard password hashing
- Salt automatically generated
- Computationally expensive to prevent brute force

### User Authentication Flow
**Implementation**: Lines 49-61 in [app.py](app.py#L49-L61)

1. User class for Flask-Login session management
2. Secure user loader from database
3. Login required decorator on protected routes

```python
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
```

---

## Data Encryption

### Password Storage
- **Never** stored in plain text
- Hashed using Werkzeug's `generate_password_hash()`
- Uses PBKDF2-SHA256 with automatic salt
- Implementation: [app.py:211](app.py#L211)

### Session Encryption
**Implementation**: Lines 27-31 in [app.py](app.py#L27-L31)

```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

**Features**:
- Secret key for session encryption
- 30-minute session timeout
- HTTPOnly cookies (prevents XSS access)
- SameSite=Lax (CSRF protection)

---

## Input Validation & Sanitization

### Input Sanitization Function
**Implementation**: Lines 74-80 in [app.py](app.py#L74-L80)

```python
def sanitize_input(input_string):
    """Sanitize user input to prevent XSS attacks"""
    if input_string is None:
        return None
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(input_string))
    return sanitized.strip()
```

**Protection Against**:
- XSS (Cross-Site Scripting)
- HTML injection
- Script tag injection

### Patient Data Validation
**Implementation**: Lines 83-138 in [app.py](app.py#L83-L138)

Validates:
1. **Gender**: Must be Male, Female, or Other
2. **Age**: 0-120 years
3. **Hypertension/Heart Disease**: Binary (0 or 1)
4. **Marital Status**: Yes or No
5. **Work Type**: Enum validation (Children, Govt_job, etc.)
6. **Residence**: Rural or Urban
7. **Glucose Level**: 0-500 mg/dL
8. **BMI**: 10-100 or N/A
9. **Smoking Status**: Enum validation
10. **Stroke**: Binary (0 or 1)

### Email Validation
**Implementation**: Lines 63-66 in [app.py](app.py#L63-L66)

```python
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

---

## CSRF Protection

### Implementation
**Library**: Flask-WTF
**Setup**: Lines 33-34 in [app.py](app.py#L33-L34)

```python
csrf = CSRFProtect(app)
```

### Usage in Templates
All forms include CSRF tokens:

```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- Form fields -->
</form>
```

**Protected Forms**:
- Registration ([register.html:13](templates/register.html#L13))
- Login ([login.html:13](templates/login.html#L13))
- Add Patient ([patient_form.html:18](templates/patient_form.html#L18))
- Edit Patient ([patient_form.html:18](templates/patient_form.html#L18))
- Delete Patient ([patients_list.html:119](templates/patients_list.html#L119))

---

## Injection Attack Prevention

### SQL Injection Prevention
**Method**: Parameterized queries
**Database**: SQLite (user authentication)

**Example** (Line 206):
```python
cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
```

**All SQL queries use**:
- Parameterized placeholders (`?`)
- Tuple parameter passing
- Never string concatenation

**Protected Operations**:
- User registration
- User login
- User retrieval
- Last login update

### NoSQL Injection Prevention
**Method**: Input validation + type conversion
**Database**: MongoDB (patient records)

**Example** (Lines 396-403):
```python
# Convert and validate types
patient_data['id'] = int(patient_data['id'])
patient_data['age'] = float(patient_data['age'])
patient_data['hypertension'] = int(patient_data['hypertension'])
# ... etc
```

**Protection Layers**:
1. Input sanitization before processing
2. Type conversion with try/except
3. Validation against allowed values
4. MongoDB driver's built-in protections

---

## Session Management

### Configuration
**Implementation**: Lines 27-31 in [app.py](app.py#L27-L31)

```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### Security Features

1. **Session Timeout**: 30 minutes of inactivity
2. **HTTPOnly Cookies**: JavaScript cannot access session cookies
3. **SameSite Protection**: Prevents CSRF via cross-site requests
4. **Secure Flag**: Should be enabled with HTTPS in production
5. **Secret Key**: Cryptographically random session encryption key

### Login Tracking
**Implementation**: Lines 245-247 in [app.py](app.py#L245-L247)

```python
cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
             (datetime.now(), user_data[0]))
```

Tracks:
- Last successful login timestamp
- Helps identify unauthorized access

---

## Error Handling & Logging

### Logging Configuration
**Implementation**: Lines 21-26 in [app.py](app.py#L21-L26)

```python
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### What Gets Logged

**INFO Level**:
- Application startup
- User registration (username only)
- Successful logins
- User logouts
- Patient record creation
- Patient record updates
- Patient record deletions

**WARNING Level**:
- Failed registration attempts
- Failed login attempts
- Invalid email formats
- 404 errors

**ERROR Level**:
- Database errors
- Unexpected exceptions
- 500 errors

### Error Pages
- **404 Page**: [404.html](templates/404.html) - File not found
- **500 Page**: [500.html](templates/500.html) - Server error

**Implementation**: Lines 513-526 in [app.py](app.py#L513-L526)

```python
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return render_template('500.html'), 500
```

### Security Through Obscurity
- Generic error messages to users
- Detailed technical errors only in logs
- No stack traces exposed to users

---

## Ethical Considerations

### Data Privacy
1. **Authentication Required**: All patient data requires login
2. **Access Control**: Only authenticated users can view/modify
3. **Audit Trail**: All modifications tracked with username and timestamp
4. **No Data Sharing**: No external API calls or data sharing

### Data Integrity
1. **Input Validation**: Ensures data accuracy
2. **Type Safety**: Numeric fields properly typed
3. **Range Checks**: Medical values within realistic ranges
4. **Audit Logging**: Changes tracked for accountability

### Compliance Considerations
While not fully HIPAA-compliant, the system follows privacy best practices:
- Encryption of passwords
- Secure session handling
- Access controls
- Audit logging
- Error logging without exposing PHI

### Professional Standards
1. **Secure Coding**: OWASP Top 10 awareness
2. **Defense in Depth**: Multiple security layers
3. **Principle of Least Privilege**: Minimal necessary access
4. **Fail Securely**: Errors don't expose sensitive data

---

## Security Checklist

- [x] Password hashing (PBKDF2-SHA256)
- [x] Password strength requirements
- [x] CSRF protection on all forms
- [x] Input validation (server-side)
- [x] Input sanitization (XSS prevention)
- [x] SQL injection prevention (parameterized queries)
- [x] NoSQL injection prevention (type validation)
- [x] Secure session management
- [x] Session timeout (30 minutes)
- [x] HTTPOnly cookies
- [x] SameSite cookie policy
- [x] Comprehensive error logging
- [x] User-friendly error pages
- [x] Authentication required for data access
- [x] Audit trail for data modifications
- [x] Email format validation
- [x] Failed login logging
- [x] Separate databases (auth vs data)
- [x] Environment variable configuration
- [x] .gitignore for sensitive files

---

## Production Deployment Security

Additional measures for production:

1. **Enable HTTPS** and set `SESSION_COOKIE_SECURE=True`
2. **Strong SECRET_KEY** (not default)
3. **MongoDB Authentication** enabled
4. **Rate Limiting** on login endpoints
5. **Database Backups** automated
6. **Firewall Rules** properly configured
7. **Regular Updates** of dependencies
8. **Security Audits** periodic reviews
9. **Monitoring** for suspicious activity
10. **SSL/TLS** certificates properly configured

---

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/en/3.0.x/security/
- PBKDF2 Standard: RFC 2898
- CSRF Prevention: https://owasp.org/www-community/attacks/csrf
- Input Validation: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

---

**Last Updated**: November 2025
**Security Review**: Completed
**Compliance**: Educational / Development Environment
