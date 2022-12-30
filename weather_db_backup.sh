#!/usr/bin/bash

 cd /home/pi/weather/db
 sqlite3 ../weather.sqlite3 ".backup weather.$(date -I).bak.sqlite3"
 rm -f $(ls -1 *bak.sqlite3 | head -n -14)

