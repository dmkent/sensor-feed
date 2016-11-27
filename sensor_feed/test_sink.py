"""Tests for the sinks code."""
from datetime import datetime
import unittest

from sensor_feed import sink


class SinkTestCase(unittest.TestCase):
    @unittest.skipIf(sink.NO_PANDAS, 'pandas/numpy not installed')
    def test_round_datetime(self):
        dt1 = datetime(2016, 3, 5, 4, 53, 43, 32)
        expected = sink.np.datetime64('2016-03-05T04:53:43.0')
        self.assertEqual(sink.round_datetime(dt1, 's'), expected)

        dt1 = datetime(2016, 3, 5, 4, 53, 43, 500000)
        expected = sink.np.datetime64('2016-03-05T04:53:44.0')
        self.assertEqual(sink.round_datetime(dt1, 's'), expected)

        dt1 = datetime(2016, 3, 5, 4, 53, 43, 500001)
        expected = sink.np.datetime64('2016-03-05T04:53:44.0')
        self.assertEqual(sink.round_datetime(dt1, 's'), expected)

        expected = sink.np.datetime64('2016-03-05T04:54:00.0')
        self.assertEqual(sink.round_datetime(dt1, 'Min'), expected)

        expected = sink.np.datetime64('2016-03-05T05:00:00.0')
        self.assertEqual(sink.round_datetime(dt1, 'H'), expected)

        expected = sink.np.datetime64('2016-03-05T00:00:00.0')
        self.assertEqual(sink.round_datetime(dt1, 'D'), expected)
