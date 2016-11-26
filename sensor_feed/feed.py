"""Main event loop for the sensor feed."""
import logging
from queue import Queue, Empty
import time


LOGGER = logging.getLogger(__name__)


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
