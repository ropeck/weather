#!/bin/bash

# set to save API response data from wunderground
#export WEATHER_API_RESPONSE_PATH=/home/pi/weather/data
#export WEATHER_DEBUG=True
export WEATHER_WUNDERGROUND_API_KEY=5bb5ecb88c674ef9b5ecb88c67def9fb
export WEATHER_STATION_ID=KCAAPTOS92
export WEATHER_LAT=36.9
export WEATHER_LONG=-121.9
export WEATHER_FORECAST_API_KEY=b69ed8db8927bd983bf8388c067c5626
export WEATHER_NEWS_API_KEY=72064d803ca1466ca192b1031038cbbc

python3 weather_station.py

