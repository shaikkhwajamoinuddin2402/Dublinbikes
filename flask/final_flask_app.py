from flask import Flask, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database connection function.
def get_db_connection(database_name):
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="password123",
        database=database_name
    )

# Fetch data from the "availability" table.
@app.route('/availability', methods=['GET'])
def get_availability():
    db = get_db_connection("local_databasejcdecaux")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM availability")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(result)

# Fetch data from the "station" table.
@app.route('/stations', methods=['GET'])
def get_stations():
    db = get_db_connection("local_databasejcdecaux")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM station")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(result)

# Fetch data from the "weather_data" table.
@app.route('/weather', methods=['GET'])
def get_weather():
    db = get_db_connection("local_databaseweather")
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM weather_data")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)