"""Main event loop for the sensor feed."""
import argparse
import logging
from queue import Queue, Empty
import time

from sensor_feed import __version__
from sensor_feed.sensor import DummySensor


LOGGER = logging.getLogger(__name__)


def get_parser():
    """Get an ArgumentParser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=__version__)

    return parser


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


class SensorFeed:
    """
        The main sensor feed controller.

        Handles starting, stopping sensors and passing queued data to the sinks.
    """

    def __init__(self, sensors, sinks, sensor_period):
        self.sensors = sensors
        self.sinks = sinks
        self.sensor_period = sensor_period
        self.queue_wait_period = 5


    def start_sensors(self):
        """Start all the sensors."""
        queues = {}
        LOGGER.critical('Starting sensors...')
        for sensor in self.sensors:
            LOGGER.critical('... %s', sensor.param_name)
            queue = Queue()
            sensor.start(queue, self.sensor_period)
            queues[sensor] = queue
        self.queues = queues


    def stop_sensors(self):
        """
            Shutdown all sensors.

            Sends a stop event to each sensor allowing any shutdown code to
            be executed.
        """
        LOGGER.critical('Shutting down sensors...')
        for sensor in self.sensors:
            LOGGER.critical('... %s', sensor.param_name)
            sensor.stop()
        LOGGER.critical('... done.')


    def run(self):
        """
            Run the feed.

            This loops over all the sensors and handles any enqueued data.
            Each piece of data is then sent to each configured sink.
        """
        while True:
            for sensor, queue in self.queues.items():
                process_queue(sensor.param_name, queue, self.sinks)
            time.sleep(self.queue_wait_period)

    def finalise_sinks(self):
        """Tell sinks we're bailing so they can tidy-up."""
        LOGGER.critical('Shutting down sinks...')
        for sink in self.sinks:
            sink.finalise()
        LOGGER.critical('... done.')


def process_queue(sensor_name, queue, sinks):
    """
        Take all tasks from queue and process them.

        Gets items from ``queue`` until an ``Empty`` exception
        is raised. For each item we call ``process_value`` on
        each available sink.
    """
    try:
        while True:
            timestamp, value = queue.get_nowait()
            for sink in sinks:
                sink.process_value(sensor_name, timestamp, value)
            queue.task_done()
    except Empty:
        return


def sensors_from_config():
    """Create the sensor objects."""
    sensors = [DummySensor()]
    return sensors


def sinks_from_config():
    """Create the sink objects."""
    LOGGER.critical('Starting sinks...')
    sinks = [PrintingSink(), LoggingSink()]
    return sinks


def main(args=None):
    """Run the feed!"""
    if args is None:
        args = get_parser().parse_args()

    period = 3

    # Create sensor and sink objects.
    sensors = sensors_from_config()
    sinks = sinks_from_config()

    # Create the feed
    feed = SensorFeed(sensors, sinks, period)

    # Start our sensors running
    feed.start_sensors()
    try:
        # Start the main event loop
        feed.run()
    except KeyboardInterrupt:
        # Quiting, stop the sensors.
        feed.stop_sensors()

    # Tidy up
    feed.finalise_sinks()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s: %(message)s')
    main()
