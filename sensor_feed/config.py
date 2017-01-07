"""Sensor definitions."""
import importlib
import logging

import yaml


LOGGER = logging.getLogger(__name__)


DEFAULTS = {
    'sensors': [
        {'class': 'RiseAndFallSensor'},
        {'class': 'CpuLoadAverage'},
        {'class': 'ConstantSensor'},
        {'class': 'ConstantSensor', 'kwargs': {'value': 5, 'name': 'Norwegian Blue'}},
    ],
    'sinks': [
        {'class': 'LoggingSink'},
    ],
}

class SensorConfig:
    def __init__(self, fname=None):
        self._raw = dict(DEFAULTS)
        if fname:
            self._raw = yaml.load(open(fname))

    def _objects_from_config(self, objs_config, def_mod):
        objs = []
        for obj_config in objs_config:
            if '.' in obj_config['class']:
                obj_mod, cls_name = obj_config['class'].rsplit('.', 1)
            else:
                obj_mod = def_mod
                cls_name = obj_config['class']
            mod = importlib.import_module(obj_mod)
            SensorClass = getattr(mod, cls_name)

            kwargs = obj_config.get('kwargs', {})

            obj = SensorClass(**kwargs)
            if hasattr(obj, 'get_objs'):
                objs += obj.get_objs()
            else:
                objs.append(obj)

        return objs

    def sensors(self):
        """Create the sensor objects."""
        return self._objects_from_config(self._raw['sensors'], 'sensor_feed.sensor')

    def sinks(self):
        """Create the sink objects."""
        LOGGER.critical('Starting sinks...')
        return self._objects_from_config(self._raw['sinks'], 'sensor_feed.sink')
