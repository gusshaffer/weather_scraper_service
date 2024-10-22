import json

# Open the location JSON file
with open('location.json', 'r') as f:
    # Load the JSON data into a Python dictionary
    data = json.load(f)
    
pretty_json = json.dumps(data, indent=4)

print("Starting weather scraper for longitude: ", data["location"]["lon"], " latitude: ", data["location"]["lat"]);
