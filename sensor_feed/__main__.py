"""Main event loop for the sensor feed."""
import argparse
import logging

from sensor_feed import __version__
from sensor_feed.feed import SensorFeed
from sensor_feed.config import SensorConfig
from sensor_feed.plant_control import PlantControl


LOGGER = logging.getLogger(__name__)


def get_parser():
    """Get an ArgumentParser."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=__version__,
                        help='show version information and exit')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='verbosity level, repeat for higher verbosity')

    parser.add_argument('--sensor-period', default=10, type=int,
                        help="the number of seconds between sensor readings, default is 10")

    parser.add_argument('--config', help='YAML config file', default=None)

    return parser


def main(args=None):
    """Run the feed!"""
    if args is None:
        args = get_parser().parse_args()

    log_level = (5 - args.verbose) * 10
    logging.basicConfig(level=log_level, format='%(asctime)s: %(message)s')

    # Create sensor and sink objects.
    config = SensorConfig(args.config)
    sensors = config.sensors()
    sinks = config.sinks()

    plant = PlantControl()
    sensors.append(plant)
    sinks.append(plant)

    # Create the feed
    feed = SensorFeed(sensors, sinks, args.sensor_period)

    # Start our sensors running
    feed.start_sensors()
    try:
        # Start the main event loop
        feed.run()
    except KeyboardInterrupt:
        # expected so don't propogate
        pass
    finally:
        # Quiting, stop the sensors.
        feed.stop_sensors()

        # Tidy up
        feed.finalise_sinks()


if __name__ == '__main__':
    main()
