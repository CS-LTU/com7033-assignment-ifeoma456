from app import create_app
from flask import Flask
import os

app = create_app()

print(app)
# =======================
# RUN THE APP
# =======================
if __name__ == '__main__':
    app.run(debug=True)


# bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# @bp.route('/')
# def dashboard():
#     return render_template(
#         'dashboard.html',
#         total_patients=25,
#         new_patients=5,
#         upcoming_appointments=3,
#         recent_patients=[
#             {"name": "John Doe", "age": 45, "gender": "Male", "created_at": "2024-01-10"},
#             {"name": "Jane Smith", "age": 32, "gender": "Female", "created_at": "2024-01-12"}
#         ]
#     )
# if __name__ == '__main__':
#     app.run(debug=True)