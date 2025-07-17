from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    from .routes import auth_bp
    app.register_blueprint(auth_bp)

    return app
