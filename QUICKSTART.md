# Quick Start Guide

Follow these simple steps to get the Stroke Prediction System running:

## Step 1: Install MongoDB

### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### Ubuntu/Debian Linux
```bash
sudo apt-get update
sudo apt-get install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

### Windows
Download and install from: https://www.mongodb.com/try/download/community

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# The default settings work for local development
# No need to modify unless you have custom MongoDB settings
```

## Step 4: Import Patient Data

```bash
python import_data.py
```

Answer "yes" when prompted. This imports 5110 patient records into MongoDB.

## Step 5: Run the Application

```bash
python app.py
```

## Step 6: Access the Application

Open your browser and navigate to: **http://127.0.0.1:5000**

## Step 7: Create Your Account

1. Click "Register"
2. Fill in:
   - **Username**: Your choice (letters, numbers, underscore)
   - **Email**: Valid email address
   - **Password**: At least 8 characters with uppercase, lowercase, and digit
   - **Confirm Password**: Same as above

3. Click "Register"

## Step 8: Login and Explore

1. Login with your credentials
2. Explore the dashboard
3. View patient records
4. Add/Edit/Delete patients
5. Search and filter data

## Common Issues

### MongoDB not running?
```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongodb

# Windows
net start MongoDB
```

### Port 5000 already in use?
Edit `app.py` line 583 and change:
```python
app.run(debug=True, host='127.0.0.1', port=5001)  # Change to 5001 or any available port
```

### Import script fails?
Make sure:
- MongoDB is running
- File `healthcare-dataset-stroke-data.csv` exists in project directory
- You have write permissions to the database

## Test Credentials

After registration, you can create a test patient with these sample values:

- **Patient ID**: 99999
- **Gender**: Male
- **Age**: 67
- **Hypertension**: Yes
- **Heart Disease**: No
- **Ever Married**: Yes
- **Work Type**: Private
- **Residence**: Urban
- **Glucose Level**: 180
- **BMI**: 28.5
- **Smoking**: formerly smoked
- **Stroke**: No

## Need Help?

Refer to the main [README.md](README.md) for detailed documentation.
