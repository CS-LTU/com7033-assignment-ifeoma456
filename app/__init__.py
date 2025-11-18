from flask import Flask, render_template, request, redirect, url_for,session


from flask import Flask, render_template, request
def create_app():
    app = Flask(_name_)

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/patient')
    def patient_form():
        return render_template('patient.html')

    @app.route('/submit', methods=['POST'])
    def submit():
        name = request.form['name']
        age = request.form['age']
        condition = request.form['condition']
        return render_template('result.html', name=name, age=age, condition=condition)

    return app

@app.route('/patients')
def view_patients():
    csv_file = os.path.join(os.path.dirname(__file__), '..', 'patients.csv')

    patients = []
    if os.path.exists(csv_file):
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    patients.append(row)

   return render_template('patients.html', patients=patients)
@app.route('/patients')
 def view_patients():
        csv_file = os.path.join(os.path.dirname(_file_), '..', 'patients.csv')

        patients = []
        if os.path.exists(csv_file):
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    patients.append(row)

        return render_template('patients.html', patients=patients)
app.secret_key = 'your_secret_key'
