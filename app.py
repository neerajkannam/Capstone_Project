from flask import Flask, render_template, request, redirect, url_for
import pickle
import pandas as pd

app = Flask(__name__)

# Load trained model
model = pickle.load(open("model2.pkl", "rb"))

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

    data = {
        "creation_time": request.form['creation_time'],
        "end_time": request.form['end_time'],
        "src_ip": request.form['src_ip'],
        "src_ip_country_code": request.form['src_ip_country_code'],
        "protocol": request.form['protocol'],
        "dst_ip": request.form['dst_ip'],
        "rule_names": request.form['rule_names'],
        "observation_name": request.form['observation_name'],
        "source.meta": request.form['source_meta'],
        "source.name": request.form['source_name'],
        "time": request.form['time'],
        "traffic_intensity_log": float(request.form['traffic_intensity_log']),
        "bytes_in_log": float(request.form['bytes_in_log']),
        "src_ip_encoded": int(request.form['src_ip_encoded']),
        "src_ip_country_code_encoded": int(request.form['src_ip_country_code_encoded'])
    }

    df = pd.DataFrame([data])

    prediction = model.predict(df)

    result_text = prediction[0]

    return render_template("result.html", prediction=result_text)


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)