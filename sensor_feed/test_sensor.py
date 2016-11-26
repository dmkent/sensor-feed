"""Tests for sensor_feed.sensor."""
from queue import Queue
import unittest
import time

from sensor_feed.sensor import DummySensor


class SensorTestCase(unittest.TestCase):
    def test_sensor(self):
        sens = DummySensor()
        queue = Queue()
        sens.start(queue, 0.5)
        time.sleep(4)
        sens.stop()
        self.assertTrue(queue.qsize() >= 6)
        self.assertTrue(queue.qsize() <= 10)
