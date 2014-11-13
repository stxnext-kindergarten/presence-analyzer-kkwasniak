# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_mean_time_weekday_view(self):
        """
        Test mean time weekday.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(data[:2], [[u'Mon', 0], [u'Tue', 30047.0]])

    def test_api_presence_weekday_view(self):
        """
        Test presence weekday view.
        """
        resp = self.client.get('/api/v1/presence_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(
            data,
            [
                [u'Weekday', u'Presence (s)'],
                [u'Mon', 24123],
                [u'Tue', 16564],
                [u'Wed', 25321],
                [u'Thu', 45968],
                [u'Fri', 6426],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    def test_api_presence_start_end_view(self):
        """
        Test presence start end view.
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(
            data,
            [
                [u'Mon', [0, 0, 0], [0, 0, 0]],
                [u'Tue', [9, 39, 5], [17, 59, 52]],
                [u'Wed', [9, 19, 52], [16, 7, 37]],
                [u'Thu', [10, 48, 46], [17, 23, 51]],
                [u'Fri', [0, 0, 0], [0, 0, 0]],
                [u'Sat', [0, 0, 0], [0, 0, 0]],
                [u'Sun', [0, 0, 0], [0, 0, 0]]
            ]
        )

    def test_not_existing_template(self):
        """
        Test for not existing template/url.
        """
        resp = self.client.get('/end_of_internet')
        self.assertEqual(resp.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test groups presence entries by weekday.
        """
        data = {
            datetime.date(2012, 7, 5):
                {
                    'start': datetime.time(9, 8, 37),
                    'end': datetime.time(18, 17, 4)
                }
        }
        tmp = utils.group_by_weekday(data)
        self.assertIsInstance(tmp, list)
        self.assertEqual(tmp, [[], [], [], [32907], [], [], []])

        data[datetime.date(2012, 6, 27)] = {
            'start': datetime.time(8, 31, 6),
            'end': datetime.time(15, 15, 27)
        }
        tmp = utils.group_by_weekday(data)
        self.assertEqual(tmp, [[], [], [24261], [32907], [], [], []])

        data[datetime.date(2012, 12, 12)] = {
            'start': datetime.time(12, 12, 12),
            'end': datetime.time(12, 12, 13)
        }
        tmp = utils.group_by_weekday(data)
        self.assertEqual(tmp, [[], [], [24261, 1], [32907], [], [], []])

    def test_seconds_since_midnight(self):
        """
        Test calculates amount of seconds since midnight.
        """
        sample_date = datetime.datetime(2014, 11, 4, 15, 28, 28, 864311)
        self.assertEqual(utils.seconds_since_midnight(sample_date), 55708)

        sample_date = datetime.datetime(2014, 11, 1, 0, 0, 2, 0)
        self.assertEqual(utils.seconds_since_midnight(sample_date), 2)

    def test_interval(self):
        """
        Test calculates inverval in seconds between two datetime.time objects.
        """
        start_date = datetime.datetime(2014, 11, 4, 15, 28, 28, 864311)
        end_date = datetime.datetime(2014, 11, 4, 15, 33, 47, 872419)
        self.assertEqual(utils.interval(start_date, end_date), 319)

        start_date = datetime.datetime(2014, 11, 5, 10, 25, 27, 10916)
        end_date = datetime.datetime(2014, 12, 7, 12, 59, 22, 164251)
        self.assertEqual(utils.interval(start_date, end_date), 9235)

    def test_mean(self):
        """
        Test calculates arithmetic mean. Returns zero for empty lists.
        """
        self.assertEqual(utils.mean([30927, 25197, 29931]), 28685.0)
        self.assertEqual(utils.mean([0]), 0.0)
        self.assertEqual(utils.mean([1337, .1337]), 668.56685)
        self.assertEqual(
            utils.mean([911.997, 14536.456456, 123123.5678]), 46190.673752
        )

    def test_seconds_to_hour(self):
        """
        Test converting from seconds to hour.
        """
        self.assertEqual(utils.seconds_to_hour(30927), (8, 35, 27))
        self.assertEqual(utils.seconds_to_hour(0), (0, 0, 0))


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
