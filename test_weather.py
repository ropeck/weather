import json
from unittest import TestCase

from mock import patch

import weather


class TestWeather(TestCase):
    def setUp(self) -> None:
        super(TestWeather, self).setUp()
        p = patch('weather.sqlite3')
        self.mock_sql = p.start()
        self.addCleanup(p.stop)

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

    # TODO: mock station data API call
    # TODO: mock forecast data API call
    # TODO: only update database if new data
    # TODO: collect station data for 5minute and hourly updates and save to databases
    # TODO: add testing for all that too

    def test_update_database(self):
        lat = "36.9"
        lon = "-121.9"
        api_key_weather = "apikey"
        w = weather.Weather(lat, lon, api_key_weather)
        w.update()
        ex = self.mock_sql.connect().cursor().execute

        self.assertEqual(1, sum('INSERT' in args[0] for (args, _) in ex.call_args_list),
                         "Should be only one new db record")
        args, kwargs = ex.call_args
        self.assertEqual(args[0],
                         ('INSERT INTO weather (epoch,solarRadiation,uv,winddir,humidity,temp,windSpeed,'
                          'windGust,pressure,precipRate,precipTotal) VALUES (?,?,?,?,?,?,?,?,?,?,?);'))
        self.assertEqual(args[1], ['1640740178',
                                   '0.0',
                                   '0.0',
                                   '347',
                                   '89.0',
                                   '47.8',
                                   '4.9',
                                   '4.9',
                                   '29.5',
                                   '0.0',
                                   '0.01'])

        if __name__ == '__main__':
            unittest.main()
