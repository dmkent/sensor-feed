"""Sensor definitions."""
from datetime import datetime
import logging
from threading import Event, Thread
import time


LOGGER = logging.getLogger(__name__)


class Sensor:
    """
        A sensor is a basic event source.

        Each sensor is started in its own thread and is free
        to what ever it needs to return data at the frequency
        requested. It returns data by adding (timestamp, value)
        tuples to the provided Queue object.
    """
    #: Name of the sensed parameter
    param_name = ''
    #: Identifier to use to refer to this sensor.
    param_id = ''
    #: Units for the parameter.
    param_unit = ''
    #: Shortest period beteen readings (in seconds)
    min_period = None
    #: Longest possible period between readings (in seconds)
    max_period = None
    #: Data type of parameter data.
    dtype = float


    def __init__(self):
        self.current_thread = None
        self.shutdown_event = None

    def start(self, queue, period):
        """
            Start collecting data.

            Should set self up to add data to ``queue`` every ``period``
            seconds.
        """
        if self.min_period is not None and period < self.min_period:
            raise ValueError("Requested period is too short " +
                             "for %s sensor. " % self.param_name +
                             "Must be greater than {} seconds".format(
                                 self.min_period
                             ))
        if self.max_period is not None and period > self.max_period:
            raise ValueError("Requested period is too long. " +
                             "Must be less than {} seconds".format(
                                 self.max_period
                             ))

        if self.current_thread is not None:
            raise RuntimeError("Sensor already running.")

        self.shutdown_event = Event()
        self.current_thread = self.get_thread(queue, period, self.shutdown_event)
        self.current_thread.start()


    def stop(self, join=True):
        """Stop collecting data."""
        if self.current_thread is None:
            return
        self.shutdown_event.set()
        if join:
            self.current_thread.join()
            self.shutdown_event = None
            self.current_thread = None
        return

    def get_thread(self, queue, period, shutdown_event):
        """Create a Thread object that will do the work."""
        raise NotImplementedError("Subclasses must implement.")


class SleepingSensor(Sensor):
    """A simple dummy sensor for testing."""
    def get_value(self):
        """Get sensor value."""
        raise NotImplementedError("Subclasses must implement.")


    def get_thread(self, queue, period, shutdown_event):
        def run():
            keep_going = True
            while keep_going:
                trigger_time = time.time()
                next_trigger = trigger_time + period

                if shutdown_event.is_set():
                    keep_going = False
                    continue

                # We allow for get_value taking some time to get
                # the value.
                # This is done by only sleeping by period - get_value time.
                queue.put((datetime.fromtimestamp(trigger_time),
                           self.get_value()))

                finished_time = time.time()
                sleep_time = next_trigger - finished_time
                LOGGER.debug('Sensor thread for %s: sleep=%f', self.param_name, sleep_time)
                if sleep_time < 0:
                    raise RuntimeError("Sensor too slow. Unable to get " +
                                       "reading in configured period of "
                                       "%f seconds." % period)
                time.sleep(sleep_time)
        thread = Thread(target=run)
        return thread


class ConstantSensor(SleepingSensor):
    """A simple constant value sensor for testing."""
    param_name = 'contstant'
    param_id = 'constant'
    param_unit = '1'

    def __init__(self, *args, value=1.0, name='constant', **kwargs):
        super(ConstantSensor, self).__init__(*args, **kwargs)
        self.value = value
        self.param_name = name


    def get_value(self):
        return self.value


def load_average():
    with open("/proc/stat") as stat:
        a = [float(val) for val in stat.readline().split()[1:5]]
    time.sleep(1)

    with open("/proc/stat") as stat:
        b = [float(val) for val in stat.readline().split()[1:5]]

    loadavg = (((b[0] + b[1] + b[2]) - (a[0] + a[1] + a[2])) /
               ((b[0] + b[1] + b[2] + b[3]) - (a[0] + a[1] + a[2] + a[3])))
    return loadavg


class CpuLoadAverage(SleepingSensor):
    param_name = 'cpu'
    param_id = 'cpu'
    param_unit = '%'
    min_period = 1.1

    def get_value(self):
        return load_average()


class RiseAndFallSensor(SleepingSensor):
    """A simple constant value sensor for testing."""
    param_name = 'dummy_soil'
    param_id = 'dummy_soil'
    param_unit = '1'

    def __init__(self, *args, **kwargs):
        super(RiseAndFallSensor, self).__init__(*args, **kwargs)
        self._value = 0.0
        self.max_val = 20.0
        self._delta = 2.0


    def get_value(self):
        cur = self._value
        newval = cur + self._delta
        if newval > self.max_val or newval < 0:
            self._delta *= -1
            newval += (2 * self._delta)
        self._value = newval
        return cur
