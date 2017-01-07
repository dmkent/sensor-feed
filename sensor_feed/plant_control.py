"""A controller for watering a plant.

This acts a both a source (current output state) and a sink (receives sensor
data to act on).
"""
import logging
from threading import Lock, Timer

from RPi import GPIO
from sensor_feed.sensor import SleepingSensor
from sensor_feed.sink import Sink


LOGGER = logging.getLogger(__name__)
GPIO.setmode(GPIO.BCM)

class PlantControl(SleepingSensor, Sink):
    """A controller to water a plant."""
    param_name = 'water_input'
    param_id = 'water_input'
    param_unit = 'seconds'

    trigger_param = 'soil'

    def __init__(self, *args, **kwargs):
        super(SleepingSensor, self).__init__(*args, **kwargs)
        super(Sink, self).__init__(*args, **kwargs)
        self._water_input = 0
        self.threshold = 1300
        self.water_period = 20
        self.min_period = self.water_period + 2
        self._watering = Lock()
        self.gpio_pin = 17

        GPIO.setup(self.gpio_pin, GPIO.OUT)

    def get_value(self):
        last_water = self._water_input
        self._water_input = 0
        return last_water

    def process_value(self, param_name, timestamp, value):
        # only interested in one parameter
        if param_name != self.trigger_param:
            return

        if value > self.threshold:
            self.apply_water()

    def apply_water(self):
        LOGGER.critical('Applying water.')
        self._water_input += self.water_period

        if self._watering.locked():
            LOGGER.critical('Already watering.')
            return

        self._watering.acquire()

        # turn on water supply.
        GPIO.output(self.gpio_pin, GPIO.HIGH)

        LOGGER.critical('Tap on.')
        timer = Timer(self.water_period, self._stop)
        timer.start()

    def _stop(self):
        LOGGER.critical('Tap off.')
        GPIO.output(self.gpio_pin, GPIO.LOW)
        self._watering.release()

    def __del__(self):
        GPIO.output(self.gpio_pin, GPIO.LOW)
        LOGGER.critical('Ensure tap off.')
