#!/usr/bin/python3
import json
import os
import re
import unittest

import mock

import weather


def _requests_get_response(caller):
    caller.datafileindex = {}

    def wrapper(arg):
        class MockResponse:
            def __init__(self, text, status_code=200):
                self.text = text
                self.status_code = status_code

            def json(self):
                return self.text

        url_arg = re.sub("\?.*$", "", arg).split("/")[2:]
        datafile_path = "_".join(url_arg)
        files = [x for x in os.listdir("data") if x.startswith(f"{datafile_path}_")]
        files.sort()
        if len(files) == 0:
            return MockResponse(
                {"error": f"no datafiles found for {arg} path {datafile_path}, found {files}, {os.getcwd()}"},
                status_code=401)
        if len(files) == 1:
            path = files[0]
        else:
            ix = caller.datafileindex.get(datafile_path, 0)
            path = files[ix]
            caller.datafileindex[datafile_path] = min(ix + 1, len(files)-1)

        with open(f"data/{path}") as fh:
            resp = json.load(fh)
        print(f"mock api {datafile_path} {path}")
        return MockResponse(resp)

    return wrapper


class TestWeather(unittest.TestCase):
    def setUp(self) -> None:
        super(TestWeather, self).setUp()
        p = mock.patch('weather.sqlite3')
        self.mock_sql = p.start()
        self.addCleanup(p.stop)
        self.mock_sql.connect().cursor().fetchall.return_value = []
        self.datafileindex = {}
        p = mock.patch('requests.get', side_effect=_requests_get_response(self))
        self.mock_requests = p.start()
        self.addCleanup(p.stop)

        lat = "36.9"
        lon = "-121.9"
        api_key_weather = "forecastapikey"
        self.weather = weather.Weather(lat, lon, "stationid", api_key_weather, "wundergroundapikey")

        self.mock_sql.connect().cursor().fetchall.return_value = [(1640740178,)]

    # TODO: collect station data for 5minute and hourly updates and save to databases
    # TODO: add testing for all that too

    def test_update_database(self):
        self.weather.update()
        ex = self.mock_sql.connect().cursor().execute

        self.assertEqual(1, sum('INSERT INTO weather' in args[0] for (args, _) in ex.call_args_list),
                         "Should be only one new db record")
        insert_found = False
        for call in ex.call_args_list:
            args, kwargs = call
            if 'INSERT INTO weather' not in args[0]:
                continue
            insert_found = True
            self.assertEqual(args[0],
                             ('INSERT INTO weather (epoch,obsTimeLocal,dewpt,heatIndex,humidity,precipRate,'
                              'precipTotal,pressure,solarRadiation,temp,uv,windChill,windGust,windSpeed,winddir) '
                              'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'))
            self.assertEqual(
                ['1641618811', '2022-01-07 21:13:31', '48.6', '49.6', '96.0', '0.0', '0.0', '29.67', '0.0', '49.6',
                 '0.0', '49.6', '0.0', '0.0', '318'], args[1])
        self.assertTrue(insert_found)
        self.assertEqual(("CREATE TABLE weather (epoch INTEGER, obsTimeLocal STRING , dewpt FLOAT, heatIndex FLOAT, "
                          "humidity FLOAT, precipRate FLOAT, precipTotal FLOAT, pressure FLOAT, solarRadiation FLOAT, "
                          "temp FLOAT, uv FLOAT, windChill FLOAT, windGust FLOAT, windSpeed FLOAT, winddir FLOAT);"),
                         self.weather.db_create_statement("weather", self.weather.flatten_wunderground_data(
                             self.weather.station_data_api_call()["observations"][0])))

    def test_weather_api_json_bad_method_path(self):
        with self.assertRaises(ValueError):
            self.weather.weather_api_json("foo/bar")

# can add tide and noaa weather info to display
# https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions&application=NOS.COOPS.TAC.WL&begin_date=20220108&end_date=20220209&datum=MLLW&station=9414290&time_zone=lst_ldt&units=english&interval=hilo&format=json
# https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/9414290.json


if __name__ == '__main__':
    unittest.main()
