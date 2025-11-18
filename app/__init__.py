from flask import Flask
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'  # Move to .env file later
    

    # Register blueprints here
    from app.auth.routes import    auth_bp

    app.register_blueprint(auth_bp)

    return app
    

