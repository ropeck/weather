from mock import patch
from unittest import TestCase
import weather

class TestWeather(TestCase):
    def setUp(self) -> None:
        super(TestWeather, self).setUp()
        p = patch('weather.sqlite3')
        self.mock_sql = p.start()
        self.addCleanup(p.stop)

# TODO: mock station data API call
# TODO: mock forecast data API call

    def test_update_database(self):
        lat = "36.9"
        lon = "-121.9"
        api_key_weather = "b69ed8db8927bd983bf8388c067c5626"
        w = weather.Weather(lat, lon, api_key_weather)
        w.update_database()
        ex = self.mock_sql.connect().cursor().execute
        self.assertTrue(ex.called)

if __name__ == '__main__':
    unittest.main()