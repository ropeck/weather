#!/usr/bin/bash

 cd /home/pi/weather; sqlite3 weather.sqlite3 ".backup weather.bak.sqlite3"

