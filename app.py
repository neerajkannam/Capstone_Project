from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import joblib
import sqlite3
import os
import logging
import time
import re
import io
import hashlib
import random
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# ================= 🔐 CONFIG =================
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback_secret")
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False

API_KEY = os.getenv("API_KEY", "secure123")

# ================= 📄 LOGGING =================
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ================= 🚦 RATE LIMIT =================
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# ================= 🤖 MODEL LOAD + INTEGRITY =================
MODEL_PATH = "best_ml_pipeline.pkl"

def verify_model():
    with open(MODEL_PATH, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Replace with your actual hash after first run
    EXPECTED_HASH = file_hash  
    if file_hash != EXPECTED_HASH:
        raise Exception("Model tampering detected!")

verify_model()
model = joblib.load(MODEL_PATH)

# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("users.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    return conn

# ================= 🔐 SECURITY FUNCTIONS =================

def detect_prompt_injection(text):
    patterns = ["ignore previous", "bypass", "override", "admin access"]
    return any(p in text.lower() for p in patterns)

def is_suspicious_input(text):
    patterns = [
        r"(--|\#)",
        r"(\bOR\b|\bAND\b)\s+\d+=\d+",
        r"\bUNION\b.*\bSELECT\b",
        r"<\s*script",
        r"javascript:",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def validate_input(text):
    if not isinstance(text, str):
        return False
    if len(text) > 300:
        return False
    if detect_prompt_injection(text) or is_suspicious_input(text):
        return False
    return True

def sanitize_output(output):
    output = str(output)
    output = re.sub(r'\S+@\S+', '[HIDDEN]', output)
    return output

# ================= 🔐 CSV SECURITY =================

EXPECTED_COLUMNS = model.feature_names_in_.tolist()

def remove_sensitive(data):
    for col in data.select_dtypes(include=['object']).columns:
        data[col] = data[col].str.replace(r'\S+@\S+', '[MASKED]', regex=True)
    return data

# ================= 🔐 SECURITY HEADERS =================
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://unpkg.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self';"
    )
    return response

# ================= 🔑 API KEY =================
@app.before_request
def check_api():
    # Skip API key check for browser form requests
    if request.endpoint == 'result' and request.method == "POST":
        if 'user' in session:
            return  # already authenticated user

        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return "Unauthorized", 401
# ================= ROUTES =================

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not validate_input(username) or not validate_input(password):
            return "Invalid input"

        if not username.isalnum() or len(password) < 6:
            return "Invalid format"

        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, hashed_pw))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            return "User exists"

    return render_template("signup.html")

@app.route('/login', methods=['GET','POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not validate_input(username) or not validate_input(password):
            return "Malicious input"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session['user'] = username
            return redirect(url_for('predict'))
        else:
            time.sleep(2)
            return "Invalid login"

    return render_template("login.html")

@app.route('/predict')
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("predict.html")

@app.route('/result', methods=['POST'])
@limiter.limit("3 per minute")
def result():
    if 'user' not in session:
        return redirect(url_for('login'))

    file = request.files['file']
    if not file:
        return "No file"

    try:
        # 🔐 In-memory processing
        data = pd.read_csv(io.StringIO(file.stream.read().decode("utf-8")))

        # 🔐 Schema validation
        if list(data.columns) != EXPECTED_COLUMNS:
            return "Invalid CSV format"

        # 🔐 Size limit
        if len(data) > 5000:
            return "Too large"

        # 🔐 Sensitive masking
        data = remove_sensitive(data)

        # 🔐 Suspicious content check
        for col in data.select_dtypes(include=['object']).columns:
            if data[col].apply(is_suspicious_input).any():
                return "Malicious CSV"

        # 🤖 Model protection
        if data.shape[1] != len(EXPECTED_COLUMNS):
            return "Invalid input shape"

        time.sleep(random.uniform(0.5, 1.5))

        prediction = model.predict(data)

        attack_count = (prediction == 1).sum()
        result_text = "⚠ Attack" if attack_count > 0 else "✅ Normal"
        result_text = sanitize_output(result_text)

        return render_template("result.html", prediction=result_text)

    except Exception as e:
        logging.error(str(e))
        return "Error processing"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))
# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("dashboard.html")


# ================= LOGS =================
@app.route('/logs')
def view_logs():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        with open('app.log', 'r') as f:
            logs = f.readlines()

        # Optional: show only last 100 logs (better performance)
        logs = logs[-100:]

    except Exception as e:
        logs = [f"No logs found or error: {str(e)}"]

    return render_template("logs.html", logs=logs)


# ================= RUN =================
if __name__ == "__main__":
    print("🚀 Running on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)