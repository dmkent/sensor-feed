"""
Adafruit BME280 temp/press/hum
"""
from datetime import datetime
import logging
from threading import Event, Thread
import time

import Adafruit_BME280

from sensor_feed.sensor_multi import MultiSensorDevice, ChildSensor


LOGGER = logging.getLogger(__name__)


class BME280Sensor(MultiSensorDevice):
    """Adafruit BME280 I2C Temp/press/hum."""
    device_name = 'bem280'

    def __init__(self, *args, **kwargs):
        super(BME280Sensor, self).__init__(*args, **kwargs)
        self._children = [
            ChildSensor(self, 'temp', 'temp', 'degC'),
            ChildSensor(self, 'relative humidity', 'rhum', '%'),
            ChildSensor(self, 'baromatric pressure', 'pressure', 'Pa'),
        ]

        self._device = Adafruit_BME280.BME280()

    def enqueue_values(self, timestamp):
        """Just map some data from a list to child sensors..."""
        data = [
            self._device.read_temperature(),
            self._device.read_humidity(),
            self._device.read_pressure(),
        ]
        for sensor, value in zip(self._children, data):
            try:
                queue = self.queues[sensor]
            except KeyError:
                # not running, skip.
                continue
            queue.put((timestamp, value))
