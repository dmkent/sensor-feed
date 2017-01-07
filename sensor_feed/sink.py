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
        self.logger.warn('%s - %s - %f', timestamp, param_name, value)


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


class BufferedSink(Sink):
    """
        A buffered sink.

        Tracks each sensor-series as a pd.Series. When the series exceeds
        buf_length values it is passed to ``write_buffer``.

        ``write_buffer`` must be implemented in a subclass.
    """
    def __init__(self, max_buffer=100):
        self._buffers = {}
        self.max_buffer = max_buffer

    def process_value(self, param_name, timestamp, value):
        """Handle a single datapoint."""
        if param_name not in self._buffers:
            self._buffers[param_name] = pd.Series()
        self._buffers[param_name].ix[round_datetime(timestamp, 's')] = value

        if len(self._buffers[param_name]) > self.max_buffer:
            self.write_buffer(param_name, self._buffers[param_name])
            del self._buffers[param_name]

    def finalise(self):
        for param_name in self._buffers:
            self.write_buffer(param_name, self._buffers[param_name])


class PrintingBufferSink(BufferedSink):
    def write_buffer(self, param_name, series):
        print(param_name, series)
