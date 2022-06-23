#!/usr/bin/bash

# set to save API response data from wunderground
#export WEATHER_API_RESPONSE_PATH=/home/pi/weather/data
export WEATHER_DEBUG=True

source /home/pi/.weather_keys

cd /home/pi/weather
./test_weather.py && ./weather_station.py

