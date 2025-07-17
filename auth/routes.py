import os
import subprocess
import sys
import socket
import psutil
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session
from .db import get_db_connection
from .auth_helpers import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)

SESSION_TOKEN_FILE = "session_token.txt"  # Temporary token file

@auth_bp.route("/")
def index():
    if "username" in session:
        return render_template("home.html", username=session["username"])
    else:
        return render_template("home.html", username=None)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"].strip().lower()
    email = request.form["email"].strip().lower()
    password = hash_password(request.form["password"])

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        existing_user = cursor.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            return "❌ Username already exists."

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        conn.commit()
        conn.close()

        session["username"] = username
        session_token = str(uuid.uuid4())
        session["token"] = session_token
        with open(SESSION_TOKEN_FILE, "w") as f:
            f.write(session_token)

        return redirect(url_for("auth.index"))

    except Exception as e:
        conn.close()
        return f"❌ An error occurred: {str(e)}"

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip().lower()
    password = request.form['password'].strip()

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user:
        stored_password = user['password']
        if verify_password(stored_password, password):
            session["username"] = user["username"]
            session_token = str(uuid.uuid4())
            session["token"] = session_token
            with open(SESSION_TOKEN_FILE, "w") as f:
                f.write(session_token)
            return redirect(url_for("auth.index"))
        else:
            return "❌ Incorrect password"
    else:
        return "❌ Username doesn't exist"

@auth_bp.route("/logout")
def logout():
    session.clear()
    if os.path.exists(SESSION_TOKEN_FILE):
        os.remove(SESSION_TOKEN_FILE)
    return redirect(url_for("auth.index"))

@auth_bp.route("/carbon-calculator")
def launch_streamlit():
    if "username" not in session or "token" not in session:
        return redirect(url_for("auth.login_signup_page"))

    # Pass token in URL to Streamlit app
    return redirect(f"https://your-streamlit-app.onrender.com?token={session['token']}", code=302)

@auth_bp.route("/logout-and-close")
def logout_and_close():
    session.clear()
    if os.path.exists(SESSION_TOKEN_FILE):
        os.remove(SESSION_TOKEN_FILE)

    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if "streamlit" in proc.info["cmdline"]:
                proc.kill()
        except Exception:
            continue

    return redirect("/")

@auth_bp.route("/login-signup")
def login_signup_page():
    return render_template("login_signup.html")
