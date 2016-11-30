"""A controller for watering a plant.

This acts a both a source (current output state) and a sink (receives sensor
data to act on).
"""
import logging
from threading import Lock, Timer

from sensor_feed.sensor import SleepingSensor
from sensor_feed.sink import Sink


LOGGER = logging.getLogger(__name__)


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
        self.threshold = 6
        self.water_period = 3
        self.min_period = self.water_period + 2
        self._watering = Lock()

    def get_value(self):
        last_water = self._water_input
        self._water_input = 0
        return last_water

    def process_value(self, param_name, timestamp, value):
        # only interested in one parameter
        if param_name != self.trigger_param:
            return

        if value < self.threshold:
            self.apply_water()

    def apply_water(self):
        LOGGER.critical('Applying water.')
        self._water_input += self.water_period

        # Do something to turn on water supply.
        # probably need to schedule something to turn it off again too...
        if self._watering.locked():
            LOGGER.critical('Already watering.')
            return

        self._watering.acquire()
        LOGGER.critical('Tap on.')
        timer = Timer(self.water_period, self._stop)
        timer.start()

    def _stop(self):
        LOGGER.critical('Tap off.')
        self._watering.release()

    def __del__(self):
        LOGGER.critical('Ensure tap off.')
