"""Sinks for the event loop."""
import logging

try:
    import pandas as pd
    import numpy as np
    NO_PANDAS = False
except ImportError:
    NO_PANDAS = True


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


def round_datetime(dtime, freq):
    """Rounds datetime to freq."""
    freq = pd.tseries.frequencies.to_offset(freq).nanos / 1000

    dtime = np.datetime64(dtime)
    return (np.round(dtime.astype('i8') /
                     float(freq)) * freq).astype(
                         'datetime64[us]'
                     ).astype('datetime64[ns]')


class DataFrameSink(Sink):
    """Sink that logs all values."""
    def __init__(self):
        self.df = pd.DataFrame()

    def process_value(self, param_name, timestamp, value):
        """Handle a single datapoint."""
        self.df.ix[round_datetime(timestamp, 's'), param_name] = value

    def finalise(self):
        print(self.df)


def sinks_from_config():
    """Create the sink objects."""
    LOGGER.critical('Starting sinks...')
    sinks = [LoggingSink()]
    if not NO_PANDAS:
        sinks.append(DataFrameSink())
    return sinks
