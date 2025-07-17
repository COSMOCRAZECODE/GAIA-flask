from flask import Flask
from auth.routes import auth_bp
from auth import db  # ✅ Import your database module

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Use .env later

app.register_blueprint(auth_bp)

# ✅ Initialize the DB before running the app
db.init_db()

if __name__ == "__main__":
    app.run(debug=True)
