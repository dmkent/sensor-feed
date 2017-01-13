"""
Adafruit BME280 temp/press/hum
"""
from datetime import datetime
import logging
from threading import Event, Thread
import time

from SI1145 import SI1145

from sensor_feed.sensor_multi import MultiSensorDevice, ChildSensor


LOGGER = logging.getLogger(__name__)


class SI1145Sensor(MultiSensorDevice):
    """Adafruit SI1145 I2C UV."""
    device_name = 'bem280'

    def __init__(self, *args, **kwargs):
        super(SI1145Sensor, self).__init__(*args, **kwargs)
        self._children = [
            ChildSensor(self, 'infrared', 'infrared', '1'),
            ChildSensor(self, 'visible light', 'vis', '1'),
            ChildSensor(self, 'uv', 'uv', '1'),
        ]

        self._device = SI1145.SI1145()


    def enqueue_values(self, timestamp):
        """Just map some data from a list to child sensors..."""
        data = [
            self._device.readIR(),
            self._device.readVisible(),
            self._device.readUV(),
        ]
        for sensor, value in zip(self._children, data):
            try:
                queue = self.queues[sensor]
            except KeyError:
                # not running, skip.
                continue
            queue.put((timestamp, value))
