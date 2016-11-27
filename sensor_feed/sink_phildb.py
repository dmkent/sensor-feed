"""A sink using the PhilDB timeseries database."""
from phildb.create import create
from phildb.exceptions import AlreadyExistsError, DuplicateError
from phildb.database import PhilDB

from sensor_feed.sink import BufferedSink


class PhilDBSink(BufferedSink):
    """
        A buffered sink using the PhilDB timeseries database.
    """
    def __init__(self, dbfile, *args, **kwargs):
        super(PhilDBSink, self).__init__(*args, **kwargs)

        try:
            create(dbfile)
        except AlreadyExistsError:
            pass # Database already exists, so no creation required.

        self.db = PhilDB(dbfile)
        self.last_known_freq = None
        try:
            self.db.add_source('SENSOR', 'Data from hardware sensor')
        except DuplicateError:
            pass # DuplicateError means the source already existed

    def write_buffer(self, param_name, series):
        """Write buffer of data to database."""
        if len(series) == 0:
            return

        try:
            self.db.add_measurand(param_name, param_name, param_name)
        except DuplicateError:
            pass # DuplicateError means the measurand already existed

        try:
            self.db.add_timeseries(param_name)
        except DuplicateError:
            pass # DuplicateError means the timeseries already existed

        freq = series.index.inferred_freq
        # need to handle special case where only one value being written
        # unable to calculate the frequency so we use the last known
        # value which in general should always be the same.
        if len(series) == 1:
            freq = self.last_known_freq
        elif freq is not None:
            self.last_known_freq = freq

        if freq is None:
            raise ValueError('Unable to determine sensor frequency')

        try:
            self.db.add_timeseries_instance(param_name, freq, 'None',
                                            measurand=param_name,
                                            source='SENSOR')
        except DuplicateError:
            pass # DuplicateError - the timeseries instance already existed

        self.db.write(param_name, freq, series, measurand=param_name, source='SENSOR')
