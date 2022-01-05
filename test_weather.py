import json
import re
import unittest

from mock import patch

import weather

def _requests_get_response(caller):
    def wrapper(arg):
        class MockResponse:
            def __init__(self, data):
                self.data = data
                self.caller = caller
            def json(self):
                return self.data
        p = re.compile(r'https://api.weather.com/v2/pws/(\S+)/(\S+)\?stationId=.*&format=json&units=e&apiKey=.*')
        m = p.match(arg)
        if not m:
            raise ValueError(f"request api format incorrect: {arg}")
        api_method=m[1]
        api_args=m[2]
        if api_method == "dailysummary":
            return MockResponse({"summaries": []})
        else:
            return MockResponse({"observations": []})
    return wrapper

class TestWeather(unittest.TestCase):
    def setUp(self) -> None:
        super(TestWeather, self).setUp()
        p = patch('weather.sqlite3')
        self.mock_sql = p.start()
        self.addCleanup(p.stop)
        self.mock_sql.connect().cursor().fetchall.return_value = []
        # patch Weather.weather_api_json(path) to return example calls for each API
        # or patch requests.get() to return the data for the URL request for an example call
        # like this https://api.weather.com/v2/pws/observations/hourly/7day?stationId=KCAAPTOS92&format=json&units=e&apiKey=5bb5ecb88c674ef9b5ecb88c67def9fb&numericPrecision=decimal
        # ... save the results to file to return named after the path "observations_hourly_7day.json" for example here

        p = patch('weather.Weather.station_data_api_call', return_value={
            'observations': [
                {'stationID': 'KCAAPTOS92', 'obsTimeUtc': '2021-12-29T01:09:38Z', 'obsTimeLocal': '2021-12-28 17:09:38',
                 'neighborhood': 'Seacliff Beach, Aptos', 'softwareType': 'WS-1002 V2.4.5', 'country': 'US',
                 'solarRadiation': 0.0, 'lon': -121.908257, 'realtimeFrequency': None, 'epoch': 1640740178,
                 'lat': 36.973396, 'uv': 0.0, 'winddir': 347, 'humidity': 89.0, 'qcStatus': 1,
                 'imperial': {'temp': 47.8, 'heatIndex': 47.8, 'dewpt': 44.8, 'windChill': 45.7, 'windSpeed': 4.9,
                              'windGust': 4.9, 'pressure': 29.5, 'precipRate': 0.0, 'precipTotal': 0.01,
                              'elev': 115.0}}]})
        p.start()
        self.addCleanup(p.stop)

        with open("data/forecast.json") as fh:
            p = patch('weather.Weather.forecast_api_call', return_value=json.load(fh))
            p.start()
            self.addCleanup(p.stop)

        p = patch('requests.get', side_effect=_requests_get_response(self))
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
            self.assertEqual(args[1], ['1640740178', '2021-12-28 17:09:38', '44.8', '47.8', '89.0', '0.0', '0.01',
                                       '29.5', '0.0', '47.8', '0.0', '45.7', '4.9', '4.9', '347'])
        self.assertTrue(insert_found)
        self.assertEqual(("CREATE TABLE weather (epoch INTEGER, obsTimeLocal STRING , dewpt FLOAT, heatIndex FLOAT, "
                          "humidity FLOAT, precipRate FLOAT, precipTotal FLOAT, pressure FLOAT, solarRadiation FLOAT, "
                          "temp FLOAT, uv FLOAT, windChill FLOAT, windGust FLOAT, windSpeed FLOAT, winddir FLOAT);"),
                         self.weather.db_create_statement("weather", self.weather.flatten_wunderground_data(
                             self.weather.station_data_api_call()["observations"][0])))

    def test_weather_api_json(self):
        self.assertEqual(self.weather.weather_api_json("foo/bar"), {'observations': []})

if __name__ == '__main__':
    unittest.main()
