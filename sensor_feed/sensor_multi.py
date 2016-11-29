"""
A MultiSensorDevice represents a single device with multiple
sensors. This allows one interface to the device to be written
and that device to then expose multiple Sensor objects to
the feed.

This works by a MultiSensorDevice returning a collection
of ChildSensors, starting any of those sensors just passes
the command onto the parent device, the parent device then
passes data back to the feed via a collection of queues.
"""
from datetime import datetime
import logging
from threading import Event, Thread
import time

from sensor_feed.sensor import Sensor


LOGGER = logging.getLogger(__name__)


class ChildSensor(Sensor):
    """
        A child sensor just passes information back up to its parent.

        All scheduling and data fetching is performed by the parent
        device class.
    """
    def __init__(self, parent, param_name, param_id, param_unit, dtype=float):
        self.parent = parent
        self.param_name = param_name
        self.param_id = param_id
        self.param_unit = param_id
        self.dtype = dtype

    def start(self, queue, period):
        """Start this sensor. Delegates to parent."""
        self.parent.start(self, queue, period)

    def stop(self, join=True):
        """Stop this sensor. Delegates to parent."""
        self.parent.stop(self, join)


class MultiSensorDevice:
    """
        A MultiSensorDevice represents a logical device that has multiple
        sensors.

        A single control thread is used to periodically get data for all
        sensors at once, this data is then split up and provided back to
        the feed on individual feeds.

        Only child sensors that have had their ``start`` method called
        will have a queue to provide data back to the feed so only
        these sensors will work.

        To subclass this class you need to implement:

        * an __init__ method that calls the super __init__ method and
          instaniates a list of ChildSensors on the _children attribute.
        * the device_name class attribute
        * enqueue_data method

    """
    #: Identifying name for the device
    device_name = ''
    #: Shortest period beteen readings (in seconds)
    min_period = None
    #: Longest possible period between readings (in seconds)
    max_period = None

    def __init__(self):
        self.current_thread = None
        self.shutdown_event = None
        self.queues = dict()

        # implementing classes will need to make this actually
        # create some child sensors!
        self._children = []

    def enqueue_values(self, timestamp):
        """
            Actually get the data from the hardware and add it to the
            data feed queues.

            This class needs to be implemented by any subclass.

            It may, for example, use I2C to get data from two or more
            sensors and then add that data to the appropriate Queue in
            ``self.queues``.
        """
        raise NotImplementedError("subclass to implement")

    def get_sensors(self):
        """Get a list of Sensor-like objects."""
        return self._children

    def start(self, child, queue, period):
        """
            Start collecting data for child.

            If this is the first call then a new data collection thread
            is started.
        """
        if self.min_period is not None and period < self.min_period:
            raise ValueError("Requested period is too short " +
                             "for %s sensor. " % self.device_name +
                             "Must be greater than {} seconds".format(
                                 self.min_period
                             ))
        if self.max_period is not None and period > self.max_period:
            raise ValueError("Requested period is too long. " +
                             "Must be less than {} seconds".format(
                                 self.max_period
                             ))

        if child in self.queues:
            raise RuntimeError("Child sensor already running.")

        self.queues[child] = queue

        if self.current_thread is None:
            # first sensor to configure, start collector thread
            self.shutdown_event = Event()
            self.current_thread = self.get_thread(period, self.shutdown_event)
            self.current_thread.start()


    def stop(self, child, join=True):
        """
            Stop collecting data for child.

            If this stops the last child then the data collection
            thread is stopped.
        """
        if self.current_thread is None:
            return

        if child in self.queues:
            del self.queues[child]

        if len(self.queues) == 0:
            self.shutdown_event.set()
            if join:
                self.current_thread.join()
                self.shutdown_event = None
                self.current_thread = None
        return

    def get_thread(self, period, shutdown_event):
        """Create a Thread object that will do the work."""
        def run():
            """Inner data collection loop."""
            keep_going = True
            while keep_going:
                trigger_time = time.time()
                next_trigger = trigger_time + period

                if shutdown_event.is_set():
                    keep_going = False
                    continue

                self.enqueue_values(datetime.fromtimestamp(trigger_time))

                finished_time = time.time()
                sleep_time = next_trigger - finished_time
                LOGGER.debug('Device thread for %s: sleep=%f', self.device_name, sleep_time)
                if sleep_time < 0:
                    raise RuntimeError("Sensor too slow. Unable to get " +
                                       "reading in configured period of "
                                       "%f seconds." % period)
                time.sleep(sleep_time)
        thread = Thread(target=run)
        return thread


class DummyMultiSensor(MultiSensorDevice):
    device_name = 'dummy'

    def __init__(self, *args, **kwargs):
        super(DummyMultiSensor, self).__init__(*args, **kwargs)
        self._children = [
            ChildSensor(self, 'a', 'a', 'mm'),
            ChildSensor(self, 'b', 'b', '%'),
        ]

    def enqueue_values(self, timestamp):
        """Just map some data from a list to child sensors..."""
        data = [1.2, 5.4]
        for sensor, value in zip(self._children, data):
            try:
                queue = self.queues[sensor]
            except KeyError:
                # not running, skip.
                continue
            queue.put((timestamp, value))
