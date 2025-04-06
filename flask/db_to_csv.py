from flask import Flask, jsonify, Response
import mysql.connector
import csv
import io
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Function to connect to database.
def get_db_connection(database_name):
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="password123",
        database=database_name
    )

# Function to convert tables to CSV.
def generate_csv(database_name, table_name):
    db = get_db_connection(database_name)
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    cursor.close()
    db.close()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(column_names)
    writer.writerows(rows)
    
    output.seek(0)
    return output

# Availability table as CSV.
@app.route('/export/availability', methods=['GET'])
def export_availability():
    output = generate_csv("local_databasejcdecaux", "availability")
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=availability.csv"})

# Stations table as CSV.
@app.route('/export/stations', methods=['GET'])
def export_stations():
    output = generate_csv("local_databasejcdecaux", "station")
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=stations.csv"})

# Weather data table as CSV.
@app.route('/export/weather', methods=['GET'])
def export_weather():
    output = generate_csv("local_databaseweather", "weather_data")
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=weather_data.csv"})

if __name__ == '__main__':
    app.run(debug=True)
