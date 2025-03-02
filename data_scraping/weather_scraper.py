import requests
import json
import datetime
import time
import mysql.connector
import dbinfo_weather           # dbinfo_weather contains important and sensitive information such as host, database, user, password, and API key.

# Connect to MySQL database
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=dbinfo_weather.DB_HOST,
            database=dbinfo_weather.DB_NAME,
            user=dbinfo_weather.DB_USER,
            password=dbinfo_weather.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print("Database connection error: {}".format(e))
        return None

# Ensures required tables exist
def ensure_tables():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()

        # Create the table for weather data if it doesn't already exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                city VARCHAR(100),
                temperature FLOAT,
                feels_like FLOAT,
                humidity INT,
                wind_speed FLOAT,
                description VARCHAR(255),
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("Weather table checked/created successfully.")

# Store weather data in the database
def store_weather_data(data):
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # Insert new weather data
        cur.execute("""
            INSERT INTO weather_data (city, temperature, feels_like, humidity, wind_speed, description)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            data["city"],
            data["temperature"],
            data["feels_like"],
            data["humidity"],
            data["wind_speed"],
            data["description"]
        ))

        conn.commit()
        cur.close()
        conn.close()
        
        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Weather data for {data['city']} stored at {current_timestamp}.")
    except Exception as e:
        print(f"Error storing weather data: {e}")

# Fetch weather data from OpenWeatherMap API
def get_weather():
    try:
        params = {
            "lat": dbinfo_weather.LAT,
            "lon": dbinfo_weather.LONG,
            "appid": dbinfo_weather.API_KEY,
            "units": "metric"
        }
        response = requests.get(dbinfo_weather.WEATHER_API_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"],
                "city": data["name"]
            }
        else:
            print("API Error: {}".format(response.status_code))
            return None
    except requests.exceptions.RequestException as e:
        print("Request failed: {}".format(e))
        return None

# Main loop to fetch and store weather data every hour
def main():
    ensure_tables()

    while True:
        try:
            print("Fetching weather data at {}.".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            weather_data = get_weather()
            if weather_data:
                store_weather_data(weather_data)

            # Wait 1 hour before fetching again
            time.sleep(3600)
        except requests.exceptions.RequestException as e:
            print("Request failed: {}".format(e))
        except Exception as e:
            print("Unexpected error: {}".format(e))

# Run the script (CTRL + C) to stop it
if __name__ == "__main__":
    main()