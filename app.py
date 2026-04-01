from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import joblib
import sqlite3
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import time
import re

app = Flask(__name__)

# 🔐 App Config
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # True in production (HTTPS)

# 📄 Logging Setup
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🤖 Load ML Model
print("Loading ML model...")
model = joblib.load("best_ml_pipeline.pkl")
print("ML model loaded successfully.")

# 📁 Create uploads folder
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# 🚫 Brute force tracking
login_attempts = {}
lock_time = {}

# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("users.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    return conn

# ================= 🔐 RULE-BASED SECURITY =================
def is_suspicious_input(text):
    if not isinstance(text, str):
        return False

    patterns = [
        r"(--|\#)",                     # SQL comments
        r"(\bOR\b|\bAND\b)\s+\d+=\d+",  # SQL injection like OR 1=1
        r"\bUNION\b.*\bSELECT\b",       # UNION SELECT attack
        r"<\s*script",                 # XSS
        r"javascript:",                # JS injection
        r"onerror\s*=",                # XSS event
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# ================= HOME =================
@app.route('/')
def home():
    return render_template("home.html")

# ================= SIGNUP =================
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Input validation
        if not username.isalnum() or len(password) < 6:
            return "Invalid input (username must be alphanumeric & password >= 6 chars)"

        # 🔐 Rule-based check
        if is_suspicious_input(username) or is_suspicious_input(password):
            return "Suspicious input detected"

        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, hashed_pw))
            conn.commit()
            conn.close()
            logging.info(f"New user registered: {username}")
            return redirect(url_for('login'))
        except:
            return "User already exists"

    return render_template("signup.html")

# ================= LOGIN =================
@app.route('/login', methods=['GET','POST'])
def login():
    ip = request.remote_addr

    # ⏳ Lock check
    if ip in lock_time and time.time() - lock_time[ip] < 60:
        return "Too many attempts. Try after 1 minute."

    # 🚫 Attempt limit
    if ip in login_attempts and login_attempts[ip] >= 5:
        lock_time[ip] = time.time()
        return "Too many attempts. Try later."

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # 🔐 Rule-based detection
        if is_suspicious_input(username) or is_suspicious_input(password):
            logging.warning(f"Injection attempt from {ip}: {username}")
            return "Suspicious input detected"

        conn = get_db()
        cursor = conn.cursor()

        # ✅ Parameterized query (safe)
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session['user'] = username
            login_attempts[ip] = 0
            logging.info(f"Login success: {username} from {ip}")
            return redirect(url_for('predict'))
        else:
            login_attempts[ip] = login_attempts.get(ip, 0) + 1
            time.sleep(2)
            logging.warning(f"Failed login: {username} from {ip}")
            return "Invalid Login"

    return render_template("login.html")

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    user = session.get('user')
    session.pop('user', None)
    logging.info(f"User logged out: {user}")
    return redirect(url_for('login'))

# ================= PREDICT =================
@app.route('/predict')
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("predict.html")

# ================= RESULT =================
@app.route('/result', methods=['POST'])
def result():
    if 'user' not in session:
        return redirect(url_for('login'))

    file = request.files['file']

    if not file:
        return "No file uploaded"

    # 🔐 File type check
    if not file.filename.lower().endswith('.csv'):
        return "Only CSV files allowed"

    if file.content_type != 'text/csv':
        return "Invalid file type"

    filename = secure_filename(file.filename)

    # 🔐 Filename attack prevention
    if ".." in filename or filename.startswith("/"):
        return "Invalid file name"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        data = pd.read_csv(filepath)

        if data.empty:
            return "Empty CSV file"

        # 🔐 Smart CSV scan
        for col in data.select_dtypes(include=['object']).columns:
           if data[col].apply(is_suspicious_input).any():
              logging.warning(f"Malicious CSV uploaded in column: {col}")
              return "🚫 Malicious content detected in file"
        # 🤖 ML Prediction
        prediction = model.predict(data)

        attack_count = (prediction == 1).sum()
        normal_count = (prediction == 0).sum()

        result_text = "⚠ Cyber Attack Detected" if attack_count > 0 else "✅ Normal Network Traffic"

        logging.info(f"{session['user']} uploaded file {filename}")

        return render_template("result.html",
                               prediction=result_text,
                               attacks=attack_count,
                               normal=normal_count)

    except Exception as e:
        logging.error(f"CSV processing error: {str(e)}")
        return "Error processing file"

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

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
    except:
        logs = ["No logs found"]

    return render_template("logs.html", logs=logs)

# ================= RUN =================
if __name__ == "__main__":
    print("\n🚀 Application is running at:")
    print("👉 http://127.0.0.1:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)