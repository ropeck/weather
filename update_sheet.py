#!/usr/bin/python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3



DBPATHNAME = "/home/pi/weather/weather.sqlite3"
db = sqlite3.connect(DBPATHNAME)
cur = db.cursor()
cur.execute("SELECT * FROM hourly ORDER BY epoch DESC LIMIT 1")
weather_data = cur.fetchall()



scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("/home/pi/weather/creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("fogcat5 weather history").sheet1  # Open the spreadhseet

sheet.append_row(weather_data[0])
print(weather_data[0])
