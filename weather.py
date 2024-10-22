import sys
import json
import time
import requests
from timeloop import Timeloop
from datetime import timedelta
from datetime import datetime
import pytz
import sqlite3
from zoneinfo import ZoneInfo


def convert_to_utc(date_string, timezone_str):

    # Create a timezone object from the timezone string
    timezone = pytz.timezone(timezone_str)

    # Parse the date string into a datetime object with the specified timezone
    dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")

    # Convert the datetime object to UTC
    utc_dt = dt.astimezone(pytz.utc)

    return utc_dt


# Open the location JSON file
with open('config.json', 'r') as f:
    # Load the JSON config into a Python dictionary
    config = json.load(f)


# Initialize DB connection and create table if it doesn't exist
conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS forecast (latitude INT, 
                                                        longitude INT, 
                                                        temperature INT, 
                                                        start DATETIME, 
                                                        end DATETIME)''')


    
pretty_json = json.dumps(config, indent=4)

if not "location" in config:
    print("Missing location!")
    sys.exit(1)
else:
    longitude = config["location"]["lon"]
    latitude = config["location"]["lat"]


if "interval" in config:
    interval_minutes = int(config["interval"]["minutes"])
    interval_seconds = int(config["interval"]["seconds"])
else:
    interval_minutes = 60
    interval_seconds = 0

api_url="https://api.weather.gov/points/" + latitude + "," + longitude


print("Starting weather scraper for "
      "longitude:", longitude,
      "latitude:", latitude,
      "every", interval_minutes, "minutes",
      interval_seconds, "seconds",
	  "at URL:", api_url);


tl = Timeloop()

@tl.job(interval=timedelta(minutes=interval_minutes,seconds=interval_seconds))
def weather_scraper_thread():

    thread_conn = sqlite3.connect('mydatabase.db')
    thread_cursor = thread_conn.cursor()
    
    print(time.ctime())
    response = requests.get(api_url)
    hourly_api = response.json()["properties"]["forecastHourly"]

    # Get timezone info for conversion to UTC
    time_zone_str = response.json()["properties"]["timeZone"]
    # time_zone = ZoneInfo(time_zone_str)

    hourly_response = requests.get(hourly_api)
   

    for period in hourly_response.json()["properties"]["periods"]:
        if int(period["number"]) < 73: #next 72 hours
   #         print("period", period["number"], "start time", period["startTime"]) 
            start_time = period["startTime"]
            end_time = period["endTime"]

            utc_start_time = convert_to_utc(start_time, time_zone_str)
            utc_end_time = convert_to_utc(end_time, time_zone_str)
            thread_cursor.execute('''INSERT INTO forecast (latitude, longitude, temperature, start, end) VALUES (?,?,?,?,?)''',
                           (latitude, longitude, period["temperature"], utc_start_time, utc_end_time))

    # Commit changes
    thread_conn.commit()
    thread_conn.close()

    

if __name__ == "__main__":
    tl.start(block=True)

def print_table_schema(conn, table_name):
    """Prints the schema of a given table in an SQLite database."""

    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()

    print(f"Schema for table '{table_name}':")
    for column in schema:
        print(f" - {column[1]} ({column[2]})")


print_table_schema(conn, "forecast")


# Execute a query to fetch the data
cursor.execute("SELECT * FROM forecast")

# Fetch all the rows
rows = cursor.fetchall()

# Print the table
for row in rows:
    print(row)

conn.close()