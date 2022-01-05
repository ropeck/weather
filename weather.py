# -*- coding:utf-8 -*-
import json
import locale
import os
import re
import sqlite3
import time

import requests

locale.setlocale(locale.LC_TIME, '')


class Weather:
    DBPATHNAME = "/home/pi/weather/weather.sqlite3"

    def __init__(self, station_id, latitude, longitude, weather_api_key, wunderground_api_key):
        self.station_id = station_id
        self.known_tables = []
        self.latitude = latitude
        self.longitude = longitude
        self.weather_api_key = weather_api_key
        self.api_key_wunderground = wunderground_api_key
        self.update()
        self.forecast = [0, [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]]
        self.forecast[0] = self.data["daily"][0]["dt"]
        self.forecast[1][6] = [self.data["daily"][0]["pressure"],
                               round(self.data["daily"][0]["temp"]["day"], 0)]

    def station_daily_rain(self):
        return round(self.station_data["observations"][0]["imperial"]["precipTotal"], 2)

    def station_temp(self):
        return round(self.station_data["observations"][0]["imperial"]["temp"], 2)

    def update(self) -> object:
        self.station_data = self.station_data_api_call()
        for sd in self.station_data["observations"]:
            self.update_database("weather", sd)

        for sd in self.station_daily_historic_data()["summaries"]:
                self.update_database("daily", sd)

        for sd in self.station_hourly_historic_data()["observations"]:
            self.update_database("hourly", sd)

        for sd in self.station_rapid_historic_data()["observations"]:
            self.update_database("rapid", sd)

        obs = self.station_data["observations"][0]
        self.lat = obs["lat"]
        self.longitude = obs["lon"]
        self.data = self.forecast_api_call(self.lat, self.longitude, self.weather_api_key)
        return self.data

    def weather_api_json(self, api_path):

        api_url = (f"https://api.weather.com/v2/pws/{api_path}?"
                   f"stationId={self.station_id}&format=json&units=e&apiKey={self.api_key_wunderground}")
        json_dict = requests.get(api_url).json()
        data_path = os.getenv("WEATHER_API_RESPONSE_PATH")

        if data_path:
            api_path_str = re.sub("/", "_", api_path)
            pathname = f'{data_path}/{api_path_str}_{int(time.time())}.json'
            with open(pathname, "w") as fh:
                json.dump(json_dict, fh)
            print(f"logged {pathname}")

        return json_dict

    def station_daily_historic_data(self):
        # https://docs.google.com/document/d/1OlAIqLb8kSfNV_Uz1_3je2CGqSnynV24qGHHrLWn7O8/edit
        return self.weather_api_json("dailysummary/7day")

    def station_hourly_historic_data(self):
        # https://docs.google.com/document/d/1OlAIqLb8kSfNV_Uz1_3je2CGqSnynV24qGHHrLWn7O8/edit
        return self.weather_api_json("observations/hourly/7day")

    def station_rapid_historic_data(self):
        # https://docs.google.com/document/d/1OlAIqLb8kSfNV_Uz1_3je2CGqSnynV24qGHHrLWn7O8/edit
        return self.weather_api_json("observations/all/1day")

    # hourly historic
    # https://docs.google.com/document/d/1wzejRIUONpdGv0P3WypGEqvSmtD5RAsNOOucvdNRi6k/edit
    # https://api.weather.com/v2/pws/observations/all/1day?stationId=KMAHANOV10&format=json&units=e&apiKey=yourApiKey
    # https://api.weather.com/v2/pws/observations/hourly/7day?stationId=KCAAPTOS92&format=json&units=e&apiKey=5bb5ecb88c674ef9b5ecb88c67def9fb&numericPrecision=decimal
    # https://api.weather.com/v2/pws/dailysummary/7day?stationId=KCAAPTOS92&format=json&units=e&apiKey=5bb5ecb88c674ef9b5ecb88c67def9fb&numericPrecision=decimal

    def forecast_api_call(self, lat, lon, api_key):
        forecast_api = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        return requests.get(forecast_api).json()

    def station_data_api_call(self):
        return requests.get(
            "https://api.weather.com/v2/pws/observations/current?stationId=KCAAPTOS92&format=json&units=e&apiKey=5bb5ecb88c674ef9b5ecb88c67def9fb&numericPrecision=decimal"
        ).json()

    def update_database(self, table, sd):
        data = self.flatten_wunderground_data(sd)
        self.insert_if_new(table, self.db_col_names(data), data)

    def flatten_wunderground_data(self, sd):
        data = {}
        for k, v in list(sd.items()) + list(sd["imperial"].items()):
            if k in data.keys():
                raise Exception('duplicate key: {}', k)
            data[k] = v
        return data

    def db_col_names(self, data):
        self.col_blocklist = ("epoch, country, elev, imperial, lat, lon, neighborhood, obsTimeLocal, "
                              "obsTimeUtc, qcStatus, realtimeFrequency, softwareType, stationID").split(", ")

        names = [n for n in data.keys() if n not in self.col_blocklist]
        names.sort()
        return ["epoch", "obsTimeLocal"] + names

    def db_create_statement(self, table, data):
        # first two columns are integer and string, the rest are float
        cols = self.db_col_names(data)[2:]
        col_types = ''.join([f", {n} FLOAT" for n in cols])
        cmd = "CREATE TABLE {} (epoch INTEGER, obsTimeLocal STRING {});".format(
            table, col_types)
        return cmd

    def insert_if_new(self, table, col_names, data):
        columns = [str(data[k]) for k in col_names]
        query = "INSERT INTO {} ({}) VALUES ({});".format(
            table, ",".join(col_names), "?" + ",?" * (len(columns) - 1))
        db = sqlite3.connect(self.DBPATHNAME)
        cur = db.cursor()
        if self.known_tables == []:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            ret = cur.fetchall()
            if ret:
                self.known_tables = [a[0] for a in ret]
        if table not in self.known_tables:
            cur.execute(self.db_create_statement(table, data))
            self.known_tables.append(table)
        cur.execute("SELECT epoch FROM {} WHERE epoch = ?".format(table),
                    [(data["epoch"]), ])
        if cur.fetchall():
            return
        print(query, str(columns))
        cur.execute(query, columns)
        cur.close()
        db.commit()
        db.close()

    #  CREATE TABLE weather (epoch INTEGER, solarRadiation FLOAT, uv FLOAT,
    #          winddir FLOAT, humidity FLOAT, temp FLOAT, windSpeed FLOAT,
    #          windGust FLOAT, pressure FLOAT, precipRate FLOAT, precipTotal FLOAT);
    #
    def current_time(self):
        return time.strftime("%d/%m/%Y %H:%M", time.localtime(self.data["current"]["dt"]))

    def current_temp(self):
        return "{:.0f}".format(self.data["current"]["temp"]) + "F"

    def current_hum(self):
        return "{:.0f}".format(self.data["current"]["humidity"]) + "%"

    def current_cloud_cov(self):
        return "{:.0f}".format(self.data["current"]["clouds"]) + "%"

    def current_sunrise(self):
        return time.strftime("%H:%M", time.localtime(self.data["current"]["sunrise"]))

    def current_sunset(self):
        return time.strftime("%H:%M", time.localtime(self.data["current"]["sunset"]))

    def current_wind(self):
        deg = self.data["current"]["wind_deg"]
        if deg < 30 or deg >= 330:
            direction = "N"
        elif 30 <= deg < 60:
            direction = "NE"
        elif 60 <= deg < 120:
            direction = "E"
        elif 120 <= deg < 150:
            direction = "SE"
        elif 150 <= deg < 210:
            direction = "S"
        elif 210 <= deg < 240:
            direction = "SO"
        elif 240 <= deg < 300:
            direction = "O"
        elif 300 <= deg < 330:
            direction = "NO"
        else:
            direction = "N/A"
        return "{:.0f}".format(self.data["current"]["wind_speed"] * 3.6) + "km/h", direction

    def current_weather(self):
        description = self.data["current"]["weather"][0]["id"]
        return description

    def rain_next_hour(self):
        input_minutely = self.data["minutely"]
        rain = []
        rain_next_hour = [["+10'", 0], ["+20'", 0], ["+30'", 0], ["+40'", 0], ["+50'", 0], ["+1h", 0]]
        for i in range(len(input_minutely)):
            rain.append(input_minutely[i]["precipitation"])
        for i in range(6):
            rain_next_hour[i][1] = sum(rain[i * 10 + 1:i * 10 + 10])
        return rain_next_hour

    def hourly_forecast(self):
        hourly = {"+3h": {"temp": "", "pop": "", "id": ""}, "+6h": {"temp": "", "pop": "", "id": ""},
                  "+12h": {"temp": "", "pop": "", "id": ""}}
        # Forecast +3h
        hourly["+3h"]["temp"] = "{:.0f}".format(self.data["hourly"][3]["temp"]) + "F"
        hourly["+3h"]["pop"] = "{:.0f}".format(self.data["hourly"][3]["pop"] * 100) + "%"
        hourly["+3h"]["id"] = self.data["hourly"][3]["weather"][0]["id"]
        # Forecast +3h
        hourly["+6h"]["temp"] = "{:.0f}".format(self.data["hourly"][6]["temp"]) + "F"
        hourly["+6h"]["pop"] = "{:.0f}".format(self.data["hourly"][6]["pop"] * 100) + "%"
        hourly["+6h"]["id"] = self.data["hourly"][6]["weather"][0]["id"]
        # Forecast +3h
        hourly["+12h"]["temp"] = "{:.0f}".format(self.data["hourly"][12]["temp"]) + "F"
        hourly["+12h"]["pop"] = "{:.0f}".format(self.data["hourly"][12]["pop"] * 100) + "%"
        hourly["+12h"]["id"] = self.data["hourly"][12]["weather"][0]["id"]

        return hourly

    def daily_forecast(self):
        daily = {"+24h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
                 "+48h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
                 "+72h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
                 "+96h": {"date": "", "min": "", "max": "", "pop": "", "id": ""}}
        i = 1
        for key in daily.keys():
            daily[key]["date"] = time.strftime("%A", time.localtime(self.data["daily"][i]["dt"]))
            daily[key]["min"] = "{:.0f}".format(self.data["daily"][i]["temp"]["min"]) + "F"
            daily[key]["max"] = "{:.0f}".format(self.data["daily"][i]["temp"]["max"]) + "F"
            daily[key]["pop"] = "{:.0f}".format(self.data["daily"][i]["pop"] * 100) + "%"
            daily[key]["id"] = self.data["daily"][i]["weather"][0]["id"]
            # daily[key]["main"] = self.data["daily"][i]["main"]
            # daily[key]["icon"] = self.data["daily"][i]["icon"]
            i += 1

        return daily

    def graph_p_t(self):
        if self.forecast[0] != self.data["daily"][0]["dt"]:
            self.forecast[0] = self.data["daily"][0]["dt"]
            self.forecast = [self.forecast[0], self.forecast[1][1:]]
            self.forecast[1].append(
                [self.data["daily"][0]["pressure"], round(self.data["daily"][0]["temp"]["day"], 0)])

    def weather_description(self, id):
        icon = "sun"
        weather_detail = "Sunny"
        if id // 100 != 8:
            id = id // 100
            if id == 2:
                icon = "thunder"
                weather_detail = "Orage"
            elif id == 3:
                icon = "drizzle"
                weather_detail = "Bruine"
            elif id == 5:
                icon = "rain"
                weather_detail = "Pluie"
            elif id == 6:
                icon = "snow"
                weather_detail = "Neige"
            elif id == 7:
                icon = "atm"
                weather_detail = "Brouillard"
            else:
                weather_detail = "Erreur"
        else:
            if id == 801:
                icon = "25_clouds"
                weather_detail = "Partly Cloudy"
            elif id == 802:
                icon = "50_clouds"
                weather_detail = "Cloudy"
            elif id == 803 or id == 804:
                icon = "100_clouds"
                weather_detail = "Overcast"

        return icon, weather_detail

    def alert(self):
        try:
            alert_descrip = self.data["alerts"][0]["event"]
        except:
            alert_descrip = 0
        return alert_descrip


class Pollution:
    def __init__(self):
        self.max_lvl_pollution = {"co": 10000, "no": 30, "no2": 40, "o3": 120, "so2": 50, "pm2_5": 20, "pm10": 30,
                                  "nh3": 100}
        pass

    def update(self, lattitude, longitude, api_id):
        self.data = requests.get(
            f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lattitude}&lon={longitude}&appid={api_id}").json()
        return self.data

    def co(self):
        return self.data["list"][0]["components"]["co"]

    def no(self):
        return self.data["list"][0]["components"]["no"]

    def no2(self):
        return self.data["list"][0]["components"]["no2"]

    def o3(self):
        return self.data["list"][0]["components"]["o3"]

    def so2(self):
        return self.data["list"][0]["components"]["so2"]

    def pm2_5(self):
        return self.data["list"][0]["components"]["pm2_5"]

    def pm10(self):
        return self.data["list"][0]["components"]["pm10"]

    def nh3(self):
        return self.data["list"][0]["components"]["nh3"]
