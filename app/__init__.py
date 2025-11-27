from flask import Flask
import os

from app.utils.sqlite_db import close_db, init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'  # Move to .env file later
        # ensure DB tables exist on startup
    with app.app_context():
        init_db()

    # close DB connection on teardown
    app.teardown_appcontext(close_db)

    # Register blueprints here
    from app.auth.routes import    auth_bp
    from app.patients import patients_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)

    return app
    

