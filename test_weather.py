from mock import patch
from unittest import TestCase
import weather

class TestWeather(TestCase):
    def setUp(self) -> None:
        super(TestWeather, self).setUp()
        p = patch('weather.sqlite3')
        self.mock_sql = p.start()
        self.addCleanup(p.stop)

        p = patch('requests.get')
        self.mock_get = p.start()
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
        self.mock_get.json.return_value = None
        w = weather.Weather(lat, lon, api_key_weather)
        w.update()
        ex = self.mock_sql.connect().cursor().execute
        self.assertTrue(ex.called)

if __name__ == '__main__':
    unittest.main()