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
from flask import Flask, jsonify, request, make_response



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

# Pull in config
# TODO config error checking is pretty lame
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


# utility used to convert weather time stamps to UTC
def convert_to_utc(date_string, timezone_str):
    # Create a timezone object from the timezone string
    timezone = pytz.timezone(timezone_str)

    # Parse the date string into a datetime object with the specified timezone
    dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")

    # Convert the datetime object to UTC
    utc_dt = dt.astimezone(pytz.utc)

    return utc_dt

# Set up thread to poll weather.gov
tl = Timeloop()

@tl.job(interval=timedelta(minutes=interval_minutes,seconds=interval_seconds))
def weather_scraper_thread():

    thread_conn = sqlite3.connect('mydatabase.db')
    thread_cursor = thread_conn.cursor()
    
    response = requests.get(api_url)
    hourly_api = response.json()["properties"]["forecastHourly"]

    # Get timezone info for conversion to UTC
    time_zone_str = response.json()["properties"]["timeZone"]
    # time_zone = ZoneInfo(time_zone_str)

    hourly_response = requests.get(hourly_api)
   

    for period in hourly_response.json()["properties"]["periods"]:
        if int(period["number"]) < 73: #next 72 hours
            start_time = period["startTime"]
            end_time = period["endTime"]

            utc_start_time = convert_to_utc(start_time, time_zone_str)
            utc_end_time = convert_to_utc(end_time, time_zone_str)
            thread_cursor.execute('''INSERT INTO forecast (latitude, longitude, temperature, start, end) VALUES (?,?,?,?,?)''',
                           (latitude, longitude, period["temperature"], utc_start_time, utc_end_time))

    # Commit changes
    thread_conn.commit()
    thread_conn.close()

    #end of weather_scraper_thread()

# Setup API
    
app = Flask(__name__)

@app.route('/forecast', methods=['GET'])
def get_forecast():
    try: 
        request_lat = request.args['lat']
        request_long = request.args['long']
        request_date_str = request.args['date']
        request_hour_str = request.args['hour']
    except KeyError: 
        return make_response('Missing arguments\n', 400)     
    
    request_date = datetime.strptime(request_date_str, "%Y-%m-%d")
    request_hour = datetime.strptime(request_hour_str, "%H")
    request_datetime = datetime.combine(request_date, datetime.time(request_hour))

# look for data matching these coordinates within this time window
    try:
        my_conn = sqlite3.connect('mydatabase.db')
        my_cursor = my_conn.cursor()

        my_cursor.execute('''SELECT MAX(temperature), MIN(temperature) FROM forecast WHERE latitude=? AND longitude=? AND start < ? AND end > ?''', 
                       (request_lat, request_long, request_datetime, request_datetime))
    except sqlite3.Error as e:
      print('An error occurred:', e)
      return make_response('Internal error querying data\n', 500)

    try:
        result = my_cursor.fetchone()
        max_temp = result[0]
        min_temp = result[1]
    except:
        return make_response('Coordinate date not found\n', 404)

    if max_temp is None or min_temp is None:
        return make_response('Coordinate date not found\n', 404)


    # print("request datetime", request_datetime, "max", max_temp, "min", min_temp)

    return_data = {
        'max': max_temp,
        'min': min_temp
    }
    return(jsonify(return_data))




if __name__ == "__main__":
    
    # prime the pump. thread loop will make its first run AFTER interval
    weather_scraper_thread()
    # start polling thread
    tl.start(block=False)

    # start API service
    app.run(host="0.0.0.0", port=5000, debug=True)
    


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