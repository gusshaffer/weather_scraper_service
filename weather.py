import sys
import json
import time
from timeloop import Timeloop
from datetime import timedelta

# Open the location JSON file
with open('config.json', 'r') as f:
    # Load the JSON config into a Python dictionary
    config = json.load(f)
    
pretty_json = json.dumps(config, indent=4)

if not "location" in config:
    print("Missing location!")
    sys.exit(1)

if "interval" in config:
    interval_minutes = int(config["interval"]["minutes"])
    interval_seconds = int(config["interval"]["seconds"])
else:
    interval_minutes = 60
    interval_seconds = 0


print("Starting weather scraper for "
      "longitude:", config["location"]["lon"], 
      "latitude:", config["location"]["lat"], 
      "every", interval_minutes, "minutes",
      interval_seconds, "seconds");


tl = Timeloop()

@tl.job(interval=timedelta(minutes=interval_minutes,seconds=interval_seconds))
def weather_scraper_thread():
    print(time.ctime())

if __name__ == "__main__":
    tl.start(block=True)



