"""Sensor definitions."""
from datetime import datetime
from threading import Event, Thread
import time


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
            raise ValueError("Requested period is too short. " +
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


    def stop(self):
        """Stop collecting data."""
        if self.current_thread is None:
            return
        self.shutdown_event.set()
        self.current_thread.join()
        self.shutdown_event = None
        self.current_thread = None
        return

    def get_thread(self, queue, period, shutdown_event):
        """Create a Thread object that will do the work."""
        raise NotImplementedError("Subclasses must implement.")


class DummySensor(Sensor):
    """A simple dummy sensor for testing."""
    param_name = 'Ones'
    param_id = 'dummy'
    param_unit = '1'

    def get_thread(self, queue, period, shutdown_event):
        def run():
            keep_going = True
            while keep_going:
                time.sleep(period)
                if shutdown_event.is_set():
                    keep_going = False
                    continue

                queue.put((datetime.utcnow(), 1.0))
        thread = Thread(target=run)
        return thread
