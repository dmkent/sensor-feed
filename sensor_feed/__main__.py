"""Main event loop for the sensor feed."""
import argparse
import logging

from sensor_feed import __version__
from sensor_feed.feed import SensorFeed
from sensor_feed.sensor import sensors_from_config
from sensor_feed.sink import sinks_from_config


LOGGER = logging.getLogger(__name__)


def get_parser():
    """Get an ArgumentParser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=__version__,
                        help='show version information and exit')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='verbosity level, repeat for higher verbosity')

    return parser


def main(args=None):
    """Run the feed!"""
    if args is None:
        args = get_parser().parse_args()

    log_level = (5 - args.verbose) * 10
    logging.basicConfig(level=log_level, format='%(asctime)s: %(message)s')

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
    main()
