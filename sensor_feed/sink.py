"""Sinks for the event loop."""
import logging


LOGGER = logging.getLogger(__name__)


class Sink:
    def process_value(self, param_name, timestamp, value):
        """Handle a single datapoint."""
        raise NotImplementedError('subclass to implement.')

    def finalise(self):
        """Tidy-up, handle any needed serialisation, etc."""
        pass


class PrintingSink(Sink):
    """Sink that prints all values."""
    def process_value(self, param_name, timestamp, value):
        """Handle a single datapoint."""
        print(param_name, timestamp, value)


class LoggingSink(Sink):
    """Sink that logs all values."""
    def __init__(self):
        self.logger = logging.getLogger('sink')

    def process_value(self, param_name, timestamp, value):
        """Handle a single datapoint."""
        self.logger.warn('%s - %s - %f', param_name, timestamp, value)


def sinks_from_config():
    """Create the sink objects."""
    LOGGER.critical('Starting sinks...')
    sinks = [LoggingSink()]
    return sinks


