from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import pandas as pd
import pickle
from datetime import datetime
import requests

# Loading environment variables from .env file.
load_dotenv()

# Initialising Flask app.
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialising SQLAlchemy.
db = SQLAlchemy(app)

# User model for storing login credentials.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Decorator to enforce login on certain routes.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access that page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Home page.
@app.route("/")
def home():
    return render_template("index.html")

# Map page (requires login).
@app.route("/map")
@login_required
def map_page():
    return render_template("map.html")

# Weather page (requires login).
@app.route("/weather")
@login_required
def weather_page():
    return render_template("weather.html")

# Review page (requires login).
@app.route("/review")
@login_required
def review_page():
    return render_template("review.html")

# Contact form submission and email handling.
@app.route("/submit_contact", methods=["POST"])
@login_required
def submit_contact():
    first = request.form.get('first')
    last = request.form.get('last')
    name = f"{first} {last}"
    email = request.form.get('email')
    message = request.form.get('message')

    msg_to_team = EmailMessage()
    msg_to_team['Subject'] = 'New Contact Form Submission'
    msg_to_team['From'] = os.getenv('EMAIL_ADDRESS')
    msg_to_team['To'] = os.getenv('EMAIL_ADDRESS')
    msg_to_team.set_content(f"Name: {name}\nEmail: {email}\nMessage:\n{message}")

    thank_you_msg = EmailMessage()
    thank_you_msg['Subject'] = 'Thanks for contacting us!'
    thank_you_msg['From'] = os.getenv('EMAIL_ADDRESS')
    thank_you_msg['To'] = email
    thank_you_msg.set_content(
        f"Hi {name},\n\n"
        "Thank you for reaching out to us. We’ve received your message and our team will get back to you shortly.\n\n"
        "Best regards,\n"
        "The Team"
    )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
            smtp.send_message(msg_to_team)
            smtp.send_message(thank_you_msg)
        flash('Message sent successfully!')
    except Exception as e:
        print(e)
        flash('There was an error sending your message. Please try again later.')

    return redirect(url_for("review_page"))

# Signup route to create a new user.
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Please fill out all fields.")
            return redirect(url_for("signup"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please pick another.")
            return redirect(url_for("signup"))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful! Please log in.")
        return redirect(url_for("login"))
    return render_template("signup.html")

# Login route for existing users.
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Please fill out all fields.")
            return redirect(url_for("login"))
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Incorrect username or password. Please try again.")
            return redirect(url_for("login"))
        session["user_id"] = user.id
        flash("Login successful!")
        return redirect(url_for("home"))
    return render_template("login.html")

# Logout route to clear session.
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.")
    return redirect(url_for("home"))

# Bike Prediction Backend.
avg_usage_df = pd.read_csv("static/station_avg_usage.csv")

# Load the machine learning model for a specific station.
def load_station_model(station_id):
    model_path = os.path.join("station_models", f"station_{station_id}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Station ID {station_id} does not exist.")
    with open(model_path, "rb") as file:
        return pickle.load(file)

# Get weather forecast for Dublin on a specific date.
def get_weather_forecast_dublin(date):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    lat, lon = 53.3498, -6.2603
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    target_date = datetime.strptime(date, "%Y-%m-%d")
    closest = min(
        data["list"],
        key=lambda x: abs(datetime.fromtimestamp(x["dt"]) - target_date)
    )

    return {
        "temperature": closest["main"]["temp"],
        "humidity": closest["main"]["humidity"],
    }

# Fetch live bike data for all stations in Dublin.
def fetch_live_bike_data_dublin():
    api_key = os.getenv("JCDECAUX_API_KEY")
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract=Dublin&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code}")
    return response.json()

# Extract available docks for a specific station from live data.
def get_station_available_docks(station_id, bike_data):
    for station in bike_data:
        if station['number'] == station_id:
            return station['available_bike_stands']
    return 0

# Get historical average docks for a station given day and hour.
def get_historical_average_docks(station_id, day_name, hour):
    row = avg_usage_df[
        (avg_usage_df['station_id'] == station_id) &
        (avg_usage_df['day_name'] == day_name) &
        (avg_usage_df['hour'] == hour)
    ]
    if not row.empty:
        return int(row['avg_docks'].values[0])
    return 0

# Predict bike availability for a specific station, date, and time.
def predict_bike_availability(station_id, date_str, time_str):
    model = load_station_model(station_id)

    try:
        date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    now = datetime.now()
    time_diff = date_time - now

    # Get weather features for input.
    weather_features = get_weather_forecast_dublin(date_str)

    # Use live data if prediction is within next 6 hours otherwise use average dock data.
    if time_diff.total_seconds() < 6 * 3600:
        bike_data = fetch_live_bike_data_dublin()
        available_docks = get_station_available_docks(station_id, bike_data)
    else:
        available_docks = get_historical_average_docks(
            station_id, date_time.weekday(), date_time.hour
        )

    # Prepare input data for model prediction.
    input_data = pd.DataFrame([{
        'num_docks_available': available_docks,
        'day': date_time.day,
        'hour': date_time.hour,
        'avg_air_temp': weather_features['temperature'],
        'avg_humidity': weather_features['humidity'],
        'day_name': date_time.weekday()
    }])

    # Predict available bikes.
    prediction = model.predict(input_data)
    return int(prediction[0])

# API endpoint to get predicted bike availability.
@app.route("/predict", methods=["GET"])
@login_required
def predict():
    try:
        station_id = request.args.get('station_id')
        date_str = request.args.get('date')
        time_str = request.args.get('time')

        if not all([station_id, date_str, time_str]):
            return {"error": "Missing required parameters"}, 400

        prediction = predict_bike_availability(int(station_id), date_str, time_str)
        return jsonify({"predicted_available_bikes": prediction})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to fetch live station list.
@app.route("/stations", methods=["GET"])
@login_required
def get_stations():
    try:
        data = fetch_live_bike_data_dublin()
        station_list = [
            {
                "name": s["name"],
                "id": s["number"],
                "status": s["status"]
            }
            for s in data]
        return jsonify(station_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app.
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
