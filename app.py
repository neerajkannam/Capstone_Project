from flask import Flask, render_template, request, redirect, url_for
import pickle
import pandas as pd
import joblib

app = Flask(__name__)

# Load trained model
model = joblib.load("best_ml_pipeline.pkl")
# ================= HOME PAGE =================
@app.route('/')
def home():
    return render_template("home.html")


# ================= LOGIN PAGE =================
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin":
            return redirect(url_for('predict'))
        else:
            return "Invalid Login"

    return render_template("login.html")


# ================= PREDICTION PAGE =================
@app.route('/predict')
def predict():
    return render_template("predict.html")


# ================= RESULT PAGE =================
@app.route('/result', methods=['POST'])
def result():

    file = request.files['file']

    if file:

        data = pd.read_csv(file)

        prediction = model.predict(data)

        attack_count = (prediction == 1).sum()
        normal_count = (prediction == 0).sum()

        if attack_count > 0:
            result_text = "⚠ Cyber Attack Detected"
        else:
            result_text = "✅ Normal Network Traffic"

        return render_template(
            "result.html",
            prediction=result_text,
            attacks=attack_count,
            normal=normal_count
        )

    return "No file uploaded"


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)