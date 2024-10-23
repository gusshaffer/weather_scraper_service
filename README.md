# weather_scraper_service
A service to scrape weather data from weather.gov and serve it via and API

## Operations
To run this service:

```
docker compose up
```

By default, this service will poll weather.gov every 60 minutes for forecast data for `Latitude 39.7456, Longitude -97.0892`. To chance this behavior modify `config.json`

To test this serivce

```
% curl 'http://localhost:8080/forecast?lat=39.7456&long=-97.0892&date=2024-10-23&hour=10'
```

Replacing `2024-10-23&hour=10` with a date and hour in the next 72 hours.

## Assumptions
* All temperatures stored and recorded in Fahrenheit
* Location and interval configured in a single JSON file
* Lack of location in config is invalid
* Return 404 for all incoming API requests for locations other than specified in the config
* Coordinates in incoming API requests must match configured coordinates **exactly**

## Caveats
* Exception handling is inconsistent
* I would like to make the coordinate matching more robust, but I prioritized other things with my time
* I'm not wiping out the SQLite DB between runs, so entries will pile up over time. 
    * Didn't seem like the highest priority for this test app
