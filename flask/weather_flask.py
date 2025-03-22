from flask import Flask, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Establishing connection to MySQL database.
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="password123",
    database="local_databaseweather"
)

# Defining the route to fetch weather data from the database.
@app.route('/data', methods=['GET'])
def get_data():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM weather_data")
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)