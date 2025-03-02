import requests
import json
import datetime
import time
import mysql.connector
import dbinfo               # dbinfo contains important and sensitive information such as host, database, user, password, and API key.

# Connect to MySQL database
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=dbinfo.DB_HOST,
            database=dbinfo.DB_NAME,
            user=dbinfo.DB_USER,
            password=dbinfo.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Ensures required tables exist
def ensure_tables():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()

        # Create the table for stations if it doesn't already exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS station (
                number INT PRIMARY KEY,
                contract_name VARCHAR(50),
                name VARCHAR(100),
                address VARCHAR(255),
                banking BOOLEAN,
                bonus BOOLEAN,
                bike_stands INT,
                lat FLOAT,
                lng FLOAT,
                status VARCHAR(20)
            );
        """)

        # Create the table for availability if it doesn't already exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS availability (
                id INT AUTO_INCREMENT PRIMARY KEY,
                number INT,
                available_bikes INT,
                available_bike_stands INT,
                status VARCHAR(20),
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (number) REFERENCES station(number)
            );
        """)

        conn.commit()
        cur.close()
        conn.close()

        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Tables checked/created at {current_timestamp}.")

# Store station data
def store_station_metadata(station):
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # Insert/update station data
        cur.execute("""
            INSERT INTO station (number, contract_name, name, address, banking, bonus, bike_stands, lat, lng, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            contract_name = VALUES(contract_name),
            name = VALUES(name),
            address = VALUES(address),
            banking = VALUES(banking),
            bonus = VALUES(bonus),
            bike_stands = VALUES(bike_stands),
            lat = VALUES(lat),
            lng = VALUES(lng),
            status = VALUES(status);
        """, (
            station["number"],
            dbinfo.NAME,
            station["name"],
            station["address"],
            station["banking"],
            station["bonus"],
            station["bike_stands"],
            station["position"]["lat"],
            station["position"]["lng"],
            station["status"]
        ))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error storing station metadata: {e}")

# Store real time availability data
def store_availability(station):
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()

        # Current timestamp
        current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert availability data with timestamp
        cur.execute("""
            INSERT INTO availability (number, available_bikes, available_bike_stands, status, last_update)
            VALUES (%s, %s, %s, %s, %s);
        """, (
            station["number"],
            station["available_bikes"],
            station["available_bike_stands"],
            station["status"],
            current_timestamp
        ))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error storing availability data: {e}")

# Fetch and store data every 5 minutes
def main():
    ensure_tables()

    while True:
        try:
            
            response = requests.get(dbinfo.STATIONS_URI, params={"apiKey": dbinfo.JCKEY, "contract": dbinfo.NAME})

            if response.status_code == 200:
                stations = json.loads(response.text)

                for station in stations:
                    store_station_metadata(station)  # Store station data
                    store_availability(station)  # Store availability data

            else:
                print(f"API Error: {response.status_code}")

            # Wait 5 minutes before fetching again
            time.sleep(5 * 60)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

# Run the script (CTRL + C) to stop it
if __name__ == "__main__":
    main()