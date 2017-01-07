"""Sensor that polls a GPIO pin"""
import Adafruit_ADS1x15

from sensor_feed.sensor import SleepingSensor


class AdcPollSensor(SleepingSensor):
    """A sensor that polls a GPIO pin."""
    def __init__(self, param_name, param_id, param_unit,
                 dtype, channel):
        self.param_name = param_name
        self.param_id = param_id
        self.param_unit = param_unit
        self.dtype = dtype

        super(AdcPollSensor, self).__init__()

        self.channel = channel
        self.adc = Adafruit_ADS1x15.ADS1015()

    def get_value(self):
        """Read value from input."""
        return self.adc.read_adc(self.channel)
