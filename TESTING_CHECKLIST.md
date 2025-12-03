# Testing Checklist

Use this checklist to verify all functionality before submission.

## Pre-Testing Setup

- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt
- [ ] MongoDB is running
- [ ] .env file created from .env.example
- [ ] Dataset imported using import_data.py
- [ ] Application starts without errors

## 1. Authentication & Authorization Testing

### Registration
- [ ] Navigate to registration page
- [ ] Try registering with weak password (< 8 chars) - Should FAIL
- [ ] Try registering without uppercase letter - Should FAIL
- [ ] Try registering without lowercase letter - Should FAIL
- [ ] Try registering without digit - Should FAIL
- [ ] Try registering with invalid email format - Should FAIL
- [ ] Register successfully with valid credentials
- [ ] Try registering with same username - Should FAIL
- [ ] Try registering with same email - Should FAIL

### Login
- [ ] Login with correct credentials - Should SUCCEED
- [ ] Verify redirect to dashboard
- [ ] Login with wrong password - Should FAIL
- [ ] Login with non-existent user - Should FAIL
- [ ] Verify error messages are displayed
- [ ] Test "Remember Me" checkbox

### Session Management
- [ ] Verify logged-in user can access dashboard
- [ ] Try accessing /patients without login - Should redirect to login
- [ ] Try accessing /dashboard without login - Should redirect to login
- [ ] Logout and verify redirect to home page
- [ ] Verify cannot access protected pages after logout

## 2. Dashboard Testing

- [ ] Dashboard displays correct statistics
- [ ] Total patients count is accurate
- [ ] Stroke patients count is correct
- [ ] No stroke patients count is correct
- [ ] Gender distribution is accurate
- [ ] Quick action links work
- [ ] Navigation links in dashboard work

## 3. Patient List Testing

### Basic Functionality
- [ ] Patient list displays correctly
- [ ] Pagination works (if more than 20 patients)
- [ ] Each patient row shows correct data
- [ ] Icons display properly (gender, badges)
- [ ] Action buttons are visible

### Search Functionality
- [ ] Search by patient ID works
- [ ] Search by gender works (e.g., "Male")
- [ ] Search by work type works (e.g., "Private")
- [ ] Search by smoking status works (e.g., "smokes")
- [ ] Search with no results shows appropriate message
- [ ] Clear search returns to full list

### Navigation
- [ ] Page numbers work correctly
- [ ] Previous/Next buttons work
- [ ] Can navigate to first and last page
- [ ] Page numbers update correctly

## 4. Add Patient Testing

### Valid Input
- [ ] Click "Add Patient" button
- [ ] Fill all required fields with valid data
- [ ] Submit form - Should SUCCEED
- [ ] Verify patient appears in list
- [ ] Verify success message displays

### Invalid Input Testing
- [ ] Try adding patient with duplicate ID - Should FAIL
- [ ] Try adding patient with age > 120 - Should FAIL
- [ ] Try adding patient with age < 0 - Should FAIL
- [ ] Try adding patient with invalid gender - Should FAIL
- [ ] Try adding patient with glucose > 500 - Should FAIL
- [ ] Try adding patient with BMI > 100 - Should FAIL
- [ ] Try adding patient with invalid work type - Should FAIL
- [ ] Submit form with missing required fields - Should FAIL
- [ ] Verify error messages are clear and helpful

### Sample Valid Patient Data
```
Patient ID: 99999
Gender: Male
Age: 67
Hypertension: Yes (1)
Heart Disease: No (0)
Ever Married: Yes
Work Type: Private
Residence Type: Urban
Avg Glucose Level: 180.5
BMI: 28.5
Smoking Status: formerly smoked
Stroke: No (0)
```

## 5. View Patient Detail Testing

- [ ] Click eye icon on any patient
- [ ] Verify all patient information displays
- [ ] Verify medical information displays correctly
- [ ] Check risk assessment section
- [ ] Verify risk factors are calculated correctly
- [ ] Verify risk score (LOW/MODERATE/HIGH) is accurate
- [ ] Check "Back to List" button works
- [ ] Check "Edit" button navigates to edit page

### Risk Assessment Verification
Risk factors include:
- Hypertension = Yes
- Heart Disease = Yes
- Age >= 65
- Smoking Status = smokes
- Glucose Level > 140

Count the factors and verify:
- 0-1 factors = LOW risk
- 2-3 factors = MODERATE risk
- 4-5 factors = HIGH risk

## 6. Edit Patient Testing

- [ ] Click pencil icon on any patient
- [ ] Verify form pre-fills with current data
- [ ] Patient ID field is read-only (cannot be changed)
- [ ] Modify some fields
- [ ] Submit form - Should SUCCEED
- [ ] Verify changes appear in patient detail
- [ ] Verify success message displays
- [ ] Check "updated_by" field in detail page

### Invalid Edit Testing
- [ ] Try changing age to invalid value - Should FAIL
- [ ] Try changing glucose to > 500 - Should FAIL
- [ ] Try changing BMI to invalid value - Should FAIL
- [ ] Verify validation errors display

## 7. Delete Patient Testing

- [ ] Click trash icon on any patient
- [ ] Verify confirmation dialog appears
- [ ] Click Cancel - Should NOT delete
- [ ] Click trash icon again
- [ ] Click OK/Confirm - Should delete
- [ ] Verify patient no longer in list
- [ ] Verify success message displays

## 8. Security Testing

### CSRF Protection
- [ ] Inspect any form in browser dev tools
- [ ] Verify CSRF token hidden input exists
- [ ] Verify token has a value
- [ ] Check all forms have CSRF tokens:
  - [ ] Registration form
  - [ ] Login form
  - [ ] Add patient form
  - [ ] Edit patient form
  - [ ] Delete form

### XSS Prevention
- [ ] Try entering `<script>alert('XSS')</script>` in username field
- [ ] Try entering `<b>Bold</b>` in search field
- [ ] Try entering `'"><img src=x onerror=alert(1)>` in any text field
- [ ] Verify script tags are removed/escaped
- [ ] Verify no alerts execute

### SQL Injection Prevention
- [ ] Try username: `admin' OR '1'='1`
- [ ] Try username: `admin'--`
- [ ] Try username: `'; DROP TABLE users--`
- [ ] Verify login fails (no SQL injection)
- [ ] Check app.log for no database errors

### Session Security
- [ ] Login successfully
- [ ] Check browser cookies (Dev Tools > Application > Cookies)
- [ ] Verify session cookie exists
- [ ] Verify session cookie has HTTPOnly flag
- [ ] Copy session cookie value
- [ ] Logout
- [ ] Try to manually set old cookie value
- [ ] Access protected page - Should redirect to login

### Password Security
- [ ] Inspect page source on login/register pages
- [ ] Verify password field type="password"
- [ ] Open SQLite database: `sqlite3 users.db`
- [ ] Run: `SELECT password_hash FROM users LIMIT 1;`
- [ ] Verify password is hashed (not plain text)
- [ ] Verify hash starts with method (e.g., pbkdf2:sha256)

## 9. Error Handling Testing

### 404 Error
- [ ] Navigate to non-existent page (e.g., /nonexistent)
- [ ] Verify custom 404 page displays
- [ ] Verify "Go Home" button works
- [ ] Check app.log for 404 entry

### 500 Error
This is harder to test, but you can:
- [ ] Temporarily break database connection
- [ ] Trigger an error
- [ ] Verify custom 500 page displays
- [ ] Check app.log for error details
- [ ] Fix database connection

### Form Validation Errors
- [ ] Submit forms with invalid data
- [ ] Verify error messages display
- [ ] Verify errors are user-friendly
- [ ] Verify form retains entered data (doesn't clear)

## 10. Logging Verification

- [ ] Open app.log file
- [ ] Verify application startup is logged
- [ ] Perform various actions (login, add patient, etc.)
- [ ] Check log for:
  - [ ] Successful login entries
  - [ ] Failed login attempts
  - [ ] Patient additions
  - [ ] Patient updates
  - [ ] Patient deletions
  - [ ] Timestamps are present
  - [ ] Log format is consistent

### Sample Log Check
```bash
tail -20 app.log
```

Should show recent activities with timestamps.

## 11. UI/UX Testing

### Responsiveness
- [ ] Resize browser window
- [ ] Test on mobile view (DevTools > Toggle Device Toolbar)
- [ ] Verify layout adjusts properly
- [ ] Verify navigation collapses on mobile
- [ ] Test on tablet view
- [ ] Verify all buttons are clickable

### Visual Elements
- [ ] All icons display correctly
- [ ] Color coding makes sense (green=good, red=danger)
- [ ] Badges display properly
- [ ] Cards have proper shadows
- [ ] Hover effects work on buttons
- [ ] Forms are well-aligned
- [ ] Error messages are visible

### Navigation
- [ ] All navbar links work
- [ ] Dropdown menus work
- [ ] Breadcrumb trails (if any) work
- [ ] Footer links work
- [ ] Back buttons work

## 12. Database Testing

### SQLite (User Database)
```bash
# Check database
sqlite3 users.db

# Run queries
SELECT COUNT(*) FROM users;
SELECT username, email, created_at FROM users;
SELECT username, last_login FROM users WHERE last_login IS NOT NULL;

# Exit
.quit
```

### MongoDB (Patient Database)
```bash
# Connect to MongoDB
mongosh

# Use database
use stroke_prediction

# Check collections
show collections

# Count patients
db.patients.countDocuments()

# Check recent patients
db.patients.find().limit(5).pretty()

# Count stroke cases
db.patients.countDocuments({stroke: 1})

# Exit
exit
```

## 13. Performance Testing

- [ ] Page load times are reasonable (< 2 seconds)
- [ ] Search results appear quickly
- [ ] Pagination is smooth
- [ ] No lag when adding/editing patients
- [ ] Dashboard statistics load quickly

## 14. Documentation Testing

- [ ] README.md is complete and accurate
- [ ] QUICKSTART.md instructions work
- [ ] SECURITY.md accurately describes features
- [ ] PROJECT_SUMMARY.md is comprehensive
- [ ] All code has appropriate comments
- [ ] Requirements.txt has all dependencies

## 15. Data Import Testing

- [ ] Run `python import_data.py`
- [ ] Verify all 5110 records imported
- [ ] Check statistics displayed after import
- [ ] Verify no duplicate records
- [ ] Verify data types are correct (no strings in number fields)

## Final Pre-Submission Checklist

- [ ] All tests passed
- [ ] No console errors in browser
- [ ] No Python errors in terminal
- [ ] All security features working
- [ ] All CRUD operations functional
- [ ] Documentation is complete
- [ ] Code is clean and commented
- [ ] .env file not in git (check .gitignore)
- [ ] All required files present
- [ ] Application runs without errors

## Test Results Summary

Date Tested: _______________
Tested By: _______________
Total Tests: _____
Passed: _____
Failed: _____

### Failed Tests (if any):
1.
2.
3.

### Notes:


---

**Testing Complete**: [ ] YES / [ ] NO
**Ready for Submission**: [ ] YES / [ ] NO
