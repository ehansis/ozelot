"""ETL pipeline for project 'eurominder'
"""
from __future__ import absolute_import
from builtins import zip
from builtins import range

from os import path

import luigi
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound
import sqlalchemy as sa
import pygeoj

from . import models
from ozelot import client
from ozelot.etl import tasks


class LoadEverything(tasks.ORMWrapperTask):
    """A top-level task to wrap the whole pipeline
    """

    def requires(self):
        yield LoadAllEuroStatsTables()
        yield LoadAllClimateData()
        yield Tests()


class Tests(tasks.ORMWrapperTask):
    """A task wrapping all tests
    """

    def requires(self):
        yield TestNUTS2Regions()
        yield TestAllEuroStatsTables()
        yield TestAllClimateData()


class NUTS2InputFile(tasks.InputFileTask):
    """An input file for NUTS2 metadata
    """

    @property
    def input_file(self):
        """Returns the input file name, with a default relative path
        """
        return path.join(path.dirname(__file__), 'data', 'NUTS_2013.csv')

    def load(self):
        """Load data, from default location

        Returns:
            pandas.DataFrame: columns 'key' (NUTS2 code), 'name'
        """
        # read file, keep all values as strings
        df = pd.read_csv(self.input_file,
                         sep=',',
                         quotechar='"',
                         encoding='utf-8',
                         dtype=object)

        # wer are only interested in the NUTS code and description, rename them also
        df = df[['NUTS-Code', 'Description']]
        df.columns = ['key', 'name']

        # we only want NUTS2 regions (4-digit codes)
        df = df[df['key'].str.len() == 4]

        # drop 'Extra Regio' codes ending in 'ZZ'
        df = df[df['key'].str[2:] != 'ZZ']

        return df


class NUTS2Regions(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load base data about NUTS2 regions
    """

    object_classes = [models.NUTS2Region]

    def requires(self):
        yield NUTS2InputFile()

    def run(self):
        # read the data
        df = next(self.requires()).load()

        # -- start documentation include: standard-object-add
        # build all objects
        for _, row in df.iterrows():
            self.session.add(models.NUTS2Region(name=row['name'],
                                                key=row['key']))
        # -- end documentation include: standard-object-add

        self.done()


class TestNUTS2Regions(tasks.ORMTestTask):
    """Test for :func:`NUTS2Regions` loading task
    """

    def requires(self):
        yield NUTS2Regions()

    def run(self):
        # load all region data
        regions = self.client.df_query(self.session.query(models.NUTS2Region))

        # known number of entries
        assert len(regions) == 276

        # uniqueness and non-null-ness
        assert len(regions) == len(regions.dropna(how='any'))
        assert len(regions['key'].unique()) == len(regions)
        assert len(regions['name'].unique()) == len(regions)

        # check one random element
        sel = regions[regions['key'] == 'DE27']
        assert sel.iloc[0]['name'] == u'Schwaben'

        self.done()


class EuroStatsInputFile(tasks.InputFileTask):
    """An input file for EuroStats tables
    """

    # indicator number, as string, including leading zeros (to be defined in derived class)
    number = luigi.Parameter()

    @property
    def input_file(self):
        """Returns the input file name, with a default relative path
        """
        return path.join(path.dirname(__file__), 'data', 'tgs{:s}.tsv'.format(self.number))

    def load(self, key_filter=None, header_preproc=None):
        """Load data table from tsv file, from default location

        Args:
            key_filter (str): additional filter for key column - regex matching
                key values to include; None for no filter

            header_preproc (func): function to apply to column headers to extract year numbers (as strings)

        Returns:
            pd.DataFrame: data
        """
        # read file, keep all values as strings
        df = pd.read_csv(self.input_file,
                         sep='\t',
                         dtype=object)

        if key_filter is not None:
            # filter on key column (first column)
            df = df[df[df.columns[0]].str.match(key_filter)]

        # first column contains metadata, with NUTS2 region key as last (comma-separated) value
        meta_col = df.columns[0]
        df[meta_col] = df[meta_col].str.split(',').str[-1]

        # convert columns to numbers, skip first column (containing metadata)
        for col_name in df.columns[1:]:
            # some values have lower-case characters indicating footnotes, strip them
            stripped = df[col_name].str.replace(r'[a-z]', '')

            # convert to numbers, convert any remaining empty values (indicated by ':' in the input table) to NaN
            df[col_name] = pd.to_numeric(stripped, errors='coerce')

        # preprocess headers
        if header_preproc is not None:
            df.columns = list(df.columns[:1]) + [header_preproc(c) for c in df.columns[1:]]

        # rename columns, convert years to integers
        # noinspection PyTypeChecker
        df.columns = ['key'] + [int(y) for y in df.columns[1:]]

        return df


class LoadAllEuroStatsTables(tasks.ORMWrapperTask):
    """Wrapper task for loading all EuroStats tables
    """

    def requires(self):
        yield EuroStatsGDP()
        yield EuroStatsUnemployment()
        yield EuroStatsPopDensity()
        yield EuroStatsHRSciTech()
        yield EuroStatsCancerDeaths()
        yield EuroStatsHeartDiseaseDeaths()
        yield EuroStatsFertilityRate()
        yield EuroStatsLifeExpectancy()


class TestAllEuroStatsTables(tasks.ORMWrapperTask):
    """Wrapper task for consistency checks for all EuroStats tables
    """

    def requires(self):
        yield TestEuroStatsGDP()
        yield TestEuroStatsUnemployment()
        yield TestEuroStatsPopDensity()
        yield TestEuroStatsHRSciTech()
        yield TestEuroStatsCancerDeaths()
        yield TestEuroStatsHeartDiseaseDeaths()
        yield TestEuroStatsFertilityRate()
        yield TestEuroStatsLifeExpectancy()


class LoadEuroStatsTableBase(tasks.ORMTask):
    """Base class for loading EuroStats tables
    """

    # indicator number, as string, including leading zeros (to be defined in derived class)
    number = None

    # indicator (short) description (to be defined in derived class)
    description = None

    # additional filter on key column (e.g. to select from a table with values by sex);
    # regular expression for columns to include, None for no filter
    key_filter = None

    # header preprocessing for input file (see :class:`EuroStatsInputFile`)
    header_preproc = None

    def requires(self):
        yield EuroStatsInputFile(number=self.number)
        yield NUTS2Regions()

    def clear(self):
        """Clear output from one (derived) class loader
        """
        # mark this task as incomplete
        self.mark_incomplete()

        # Delete the indicator metadata, this also deletes values by cascading.
        #
        # NOTE: calling 'delete()' on the query (instead of on the queried object,
        # as done here), would NOT work! For a query, there is no in-Python cascading
        # of delete statements in sqlalchemy, so the associated values would not
        # be deleted e.g. for SQLite databases.
        try:
            indicator = self.session.query(models.EuroStatIndicator) \
                .filter(models.EuroStatIndicator.number == self.number) \
                .one()
            self.session.delete(indicator)
        except NoResultFound:
            # Data didn't exist yet, no problem
            pass

        self.close_session()

    def run(self):
        """Load table data to :class:`EuroStatsValue` objects
        """
        # -- start documentation include: eurostats-run-1
        # create a new indicator metadata object
        indicator = models.EuroStatIndicator(
            number=self.number,
            description=self.description,
            url="http://ec.europa.eu/eurostat/web/products-datasets/-/tgs" + self.number)

        # add/commit to get the object ID filled
        self.session.add(indicator)
        self.session.commit()
        # -- end documentation include: eurostats-run-1

        # -- start documentation include: eurostats-run-2
        # load data from input file task
        df = next(self.requires()).load(key_filter=self.key_filter,
                                        header_preproc=self.header_preproc)

        # Transform data: DataFrame from loading has NUTS2 key and years as columns.
        # Index by key, then stack years as second level of index. Reset the index
        # to get year and key as regular columns, with one value column left.
        values = df.set_index('key').stack()
        values.index.levels[1].name = 'year'
        values.name = 'value'
        df = values.reset_index()
        # -- end documentation include: eurostats-run-2

        # -- start documentation include: eurostats-run-3
        # get current max ID for EuroStatValue objects, for manual ID generation
        max_id = models.EuroStatValue.get_max_id(self.session)

        # append an ID column, starting with the current max ID of the object class plus one
        df['id'] = list(range(max_id + 1, max_id + 1 + len(df)))
        # -- end documentation include: eurostats-run-3

        # -- start documentation include: eurostats-run-4
        # append indicator ID (constant)
        df['indicator_id'] = indicator.id

        # append region ID column, by mapping NUTS2 region keys to DB object IDs
        regions = self.client.df_query(self.session.query(models.NUTS2Region)) \
            .set_index('key')['id']
        df['region_id'] = df['key'].map(regions)

        # drop columns that are not part of the data model
        df = df.drop(['key'], axis=1)  # type: pd.DataFrame
        # -- end documentation include: eurostats-run-4

        # -- start documentation include: eurostats-run-5
        # store, done
        df.to_sql(name=models.EuroStatValue.__tablename__,
                  con=client.get_client().engine,
                  if_exists='append',
                  index=False)

        self.done()
        # -- end documentation include: eurostats-run-5


class TestEuroStatsTableBase(tasks.ORMTestTask):
    """Base class for testing loading of EuroStats tables
    """

    # max number of missing values (to be defined in derived class)
    max_missing = None

    # value for DE71, 2012 (to be defined in derived class)
    test_value = None

    # min/max admissable values (to be defined in derived class)
    min_val = None
    max_val = None

    # maximum fraction of regions with no values
    max_missing_region_fraction = 0.05

    # header preprocessing for input file (see :class:`EuroStatsInputFile`)
    header_preproc = None

    def run(self):
        # the tested task's data ID
        number = next(self.requires()).number

        # get number of regions
        n_regions = self.session.query(models.NUTS2Region).count()

        # get number of years from input file
        input_df = EuroStatsInputFile(number=number).load(header_preproc=self.header_preproc)
        n_years = len(input_df.columns) - 1

        # values for the indicator
        # noinspection PyComparisonWithNone
        query = self.session.query(models.EuroStatValue.value) \
            .filter(models.EuroStatValue.indicator.has(number=number)) \
            .filter(models.EuroStatValue.region_id != None)
        values = self.client.df_query(query)['value']

        # full data for 12 years * all 276 NUTS2 regions, with less than N missing values,
        # but also not more values than full coverage (to test if key filter works);
        # ignore additional data points
        assert len(values) >= n_years * n_regions - self.max_missing
        assert len(values) < n_years * n_regions

        # most regions should have some values
        # noinspection PyComparisonWithNone
        cnt = self.session.query(models.EuroStatValue.region_id.distinct()) \
            .filter(models.EuroStatValue.indicator.has(number=number)) \
            .filter(models.EuroStatValue.region_id != None) \
            .count()
        assert cnt > n_regions * (1. - self.max_missing_region_fraction)

        # all years should have some values
        # noinspection PyComparisonWithNone
        cnt = self.session.query(models.EuroStatValue.year.distinct()) \
            .filter(models.EuroStatValue.indicator.has(number=number)) \
            .filter(models.EuroStatValue.region_id != None) \
            .count()
        assert cnt == n_years

        # test min/max
        assert values.min() >= self.min_val
        assert values.max() <= self.max_val

        self.done()


class EuroStatsGDP(LoadEuroStatsTableBase):
    number = "00005"
    description = "Regional gross domestic product (PPS per inhabitant)"


class TestEuroStatsGDP(TestEuroStatsTableBase):
    max_missing = 2
    min_val = 3000
    max_val = 200000

    def requires(self):
        yield EuroStatsGDP()


class EuroStatsUnemployment(LoadEuroStatsTableBase):
    number = "00010"
    description = "Unemployment rate (percent)"

    # additional filter on input file key column: extract totals only, not male/female
    key_filter = '.*,T,.*'


class TestEuroStatsUnemployment(TestEuroStatsTableBase):
    max_missing = 100
    min_val = 1
    max_val = 40

    def requires(self):
        yield EuroStatsUnemployment()


class EuroStatsPopDensity(LoadEuroStatsTableBase):
    number = "00024"
    description = "Population density (people per km^2)"


class TestEuroStatsPopDensity(TestEuroStatsTableBase):
    max_missing = 100
    min_val = 1
    max_val = 15000

    def requires(self):
        yield EuroStatsPopDensity()


class EuroStatsHRSciTech(LoadEuroStatsTableBase):
    number = "00038"
    description = "Human resources in science and technology (percent)"


class TestEuroStatsHRSciTech(TestEuroStatsTableBase):
    max_missing = 100
    min_val = 5
    max_val = 95

    def requires(self):
        yield EuroStatsHRSciTech()


class EuroStatsCancerDeaths(LoadEuroStatsTableBase):
    number = "00058"
    description = "Deaths due to cancer (cases per 100k population)"

    # additional filter on input file key column: extract totals only, not male/female
    key_filter = '^T,.*'

    # column headers give 3-year averaging periods like '1997_1999', extract the second year
    @staticmethod
    def header_preproc(s):
        return s.split('_')[1]


class TestEuroStatsCancerDeaths(TestEuroStatsTableBase):
    max_missing = 800
    max_missing_region_fraction = 0.2
    min_val = 150
    max_val = 450

    # column headers give 3-year averaging periods like '1997_1999', extract the second year
    @staticmethod
    def header_preproc(s):
        return s.split('_')[1]

    def requires(self):
        yield EuroStatsCancerDeaths()


class EuroStatsHeartDiseaseDeaths(LoadEuroStatsTableBase):
    number = "00059"
    description = "Deaths due to ischemic heart disease (cases per 100k population)"

    # additional filter on input file key column: extract totals only, not male/female
    key_filter = '^T,.*'

    # column headers give 3-year averaging periods like '1997_1999', extract the second year
    @staticmethod
    def header_preproc(s):
        return s.split('_')[1]


class TestEuroStatsHeartDiseaseDeaths(TestEuroStatsTableBase):
    max_missing = 800
    max_missing_region_fraction = 0.2
    min_val = 50
    max_val = 800

    # column headers give 3-year averaging periods like '1997_1999', extract the second year
    @staticmethod
    def header_preproc(s):
        return s.split('_')[1]

    def requires(self):
        yield EuroStatsHeartDiseaseDeaths()


class EuroStatsFertilityRate(LoadEuroStatsTableBase):
    number = "00100"
    description = "Total fertility rate"


class TestEuroStatsFertilityRate(TestEuroStatsTableBase):
    max_missing = 200
    min_val = 0.8
    max_val = 6.0

    def requires(self):
        yield EuroStatsFertilityRate()


class EuroStatsLifeExpectancy(LoadEuroStatsTableBase):
    number = "00101"
    description = "Life expectancy at birth (years)"

    # additional filter on input file key column: extract totals only, not male/female
    key_filter = '.*,T,.*'


class TestEuroStatsLifeExpectancy(TestEuroStatsTableBase):
    max_missing = 300
    min_val = 60
    max_val = 90

    def requires(self):
        yield EuroStatsLifeExpectancy()


class NUTS2GeoJSONInputFile(tasks.InputFileTask):
    """An input file for NUTS2 GeoJSON polygons
    """

    @property
    def input_file(self):
        """Returns the input file name, with a default relative path
        """
        return path.join(path.dirname(__file__), 'data', 'nuts_rg_60M_2013_lvl_2.geojson')

    def load(self):
        """Load data, from default location

        Returns:
            pygeoj.GeojsonFile: GeoJSON data
        """
        return pygeoj.load(self.input_file)


def geojson_polygon_to_mask(feature, shape, lat_idx, lon_idx):
    """Convert a GeoJSON polygon feature to a numpy array

    Args:
        feature (pygeoj.Feature): polygon feature to draw
        shape (tuple(int, int)): shape of 2D target numpy array to draw polygon in
        lat_idx (func): function converting a latitude to the (fractional) row index in the map
        lon_idx (func): function converting a longitude to the (fractional) column index in the map

    Returns:
        np.array: mask, background is zero, foreground is one
    """
    import matplotlib

    # specify 'agg' renderer, Mac renderer does not support what we want to do below
    matplotlib.use('agg')

    import matplotlib.pyplot as plt
    from matplotlib import patches
    import numpy as np

    # we can only do polygons right now
    if feature.geometry.type not in ('Polygon', 'MultiPolygon'):
        raise ValueError("Cannot handle feature of type " + feature.geometry.type)

    # fictional dpi - don't matter in the end
    dpi = 100

    # -- start documentation include: poly-setup
    # make a new figure with no frame, no axes, with the correct size, black background
    fig = plt.figure(frameon=False, dpi=dpi, )
    fig.set_size_inches(shape[1] / float(dpi), shape[0] / float(dpi))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    # noinspection PyTypeChecker
    ax.set_xlim([0, shape[1]])
    # noinspection PyTypeChecker
    ax.set_ylim([0, shape[0]])
    fig.add_axes(ax)
    # -- end documentation include: poly-setup

    # for normal polygons make coordinates iterable
    if feature.geometry.type == 'Polygon':
        coords = [feature.geometry.coordinates]
    else:
        coords = feature.geometry.coordinates

    for poly_coords in coords:
        # the polygon may contain multiple outlines; the first is
        # always the outer one, the others are 'holes'
        for i, outline in enumerate(poly_coords):
            # inside/outside fill value: figure background is white by
            # default, draw inverted polygon and invert again later
            value = 0. if i == 0 else 1.

            # convert lats/lons to row/column indices in the array
            outline = np.array(outline)
            xs = lon_idx(outline[:, 0])
            ys = lat_idx(outline[:, 1])

            # draw the polygon
            poly = patches.Polygon(list(zip(xs, ys)),
                                   facecolor=(value, value, value),
                                   edgecolor='none',
                                   antialiased=True)
            ax.add_patch(poly)

    # -- start documentation include: poly-extract
    # extract the figure to a numpy array,
    fig.canvas.draw()
    data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    # reshape to a proper numpy array, keep one channel only
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))[:, :, 0]
    # -- end documentation include: poly-extract

    # make sure we get the right shape back
    assert data.shape[0] == shape[0]
    assert data.shape[1] == shape[1]

    # convert from uints back to floats and invert to get black background
    data = 1. - data.astype(float) / 255.  # type: np.array

    # image is flipped horizontally w.r.t. map
    data = data[::-1, :]

    # done, clean up
    plt.close('all')

    return data


class ClimateDataInputFile(tasks.InputFileTask):
    """Climate data input file with loading method
    """

    # -- start documentation include: climate-input-params
    # climate variable name (in netcdf file)
    variable_name = luigi.Parameter()

    # output file name (without path)
    file_name = luigi.Parameter()

    # -- end documentation include: climate-input-params

    @property
    def input_file(self):
        """Returns the input file name, with a default relative path
        """
        return path.join(path.dirname(__file__), 'data', self.file_name)

    def load(self):
        """Load the climate data as a map

        Returns:
            dict: {data: masked 3D numpy array containing climate data per month (first axis),
                   lat_idx: function converting a latitude to the (fractional) row index in the map,
                   lon_idx: function converting a longitude to the (fractional) column index in the map}
        """
        from scipy.io import netcdf_file
        from scipy import interpolate
        import numpy as np

        # load file
        f = netcdf_file(self.input_file)

        # extract data, make explicity copies of data
        out = dict()
        lats = f.variables['lat'][:].copy()
        lons = f.variables['lon'][:].copy()

        # lons start at 0, this is bad for working with data in Europe because the map border runs right through;
        # roll array by half its width to get Europe into the map center
        out['data'] = np.roll(f.variables[self.variable_name][:, :, :].copy(), shift=len(lons) // 2, axis=2)
        lons = np.roll(lons, shift=len(lons) // 2)

        # avoid wraparound problems around zero by setting lon range to -180...180, this is
        # also the format used in the GeoJSON NUTS2 polygons
        lons[lons > 180] -= 360

        # data contains some very negative value (~ -9e36) as 'invalid data' flag, convert this to a masked array
        out['data'] = np.ma.array(out['data'])
        out['data'][out['data'] < -1.e6] = np.ma.masked

        # -- start documentation include: climate-input-interp
        # build interpolators to convert lats/lons to row/column indices
        out['lat_idx'] = interpolate.interp1d(x=lats, y=np.arange(len(lats)))
        out['lon_idx'] = interpolate.interp1d(x=lons, y=np.arange(len(lons)))
        # -- end documentation include: climate-input-interp

        # clean up
        f.close()

        return out


# suffixes for seasonal climate data
CLIMATE_SEASON_SUFFIXES = dict(summer=' Apr-Sep',
                               winter=' Oct-Mar')


class LoadClimateData(tasks.ORMTask):
    """Load data for one climate variable
    """

    # -- start documentation include: climate-load-params
    # climate variable name (as in netcdf file)
    variable_name = luigi.Parameter()

    # input file name (without path)
    input_file = luigi.Parameter()

    # climate variable description (in indicator)
    description = luigi.Parameter()

    # -- end documentation include: climate-load-params

    def requires(self):
        yield ClimateDataInputFile(variable_name=self.variable_name,
                                   file_name=self.input_file)
        yield NUTS2GeoJSONInputFile()
        yield NUTS2Regions()

    def clear(self):
        """Clear output of one climate variable
        """
        # mark this task as incomplete
        self.mark_incomplete()

        # Delete the indicator metadata, this also deletes values by cascading.
        for suffix in list(CLIMATE_SEASON_SUFFIXES.values()):
            try:
                # noinspection PyUnresolvedReferences
                indicator = self.session.query(models.ClimateIndicator) \
                    .filter(models.ClimateIndicator.description == self.description + suffix) \
                    .one()
                self.session.delete(indicator)
            except NoResultFound:
                # Data didn't exist yet, no problem
                pass

        self.close_session()

    def run(self):
        """Load climate data and convert to indicator objects
        """
        import numpy as np

        # get all NUTS region IDs, for linking values to region objects
        query = self.session.query(models.NUTS2Region.key,
                                   models.NUTS2Region.id)
        region_ids = self.client.df_query(query).set_index('key')['id'].to_dict()

        # load climate data and NUTS2 polygons
        data = next(self.requires()).load()
        nuts = NUTS2GeoJSONInputFile().load()

        # generated indicator IDs, keyed by season
        indicator_ids = dict()

        # climate data by season
        t_data = dict()

        # create new indicator objects for summer and winter, create averaged climate data
        for season, suffix in CLIMATE_SEASON_SUFFIXES.items():
            # noinspection PyUnresolvedReferences
            indicator = models.ClimateIndicator(description=self.description + suffix)
            self.session.add(indicator)

            # commit, to get indicator ID filled
            self.session.commit()
            indicator_ids[season] = indicator.id

            # select winter or summer data by month index, average over time range
            if season == 'summer':
                t_data[season] = np.ma.average(data['data'][3:9, :, :], axis=0)
            else:
                # noinspection PyTypeChecker
                t_data[season] = np.ma.average(0.5 * (data['data'][0:3, :, :] + data['data'][9:12, :, :]), axis=0)

        # container for output objects, for bulk saving
        objects = []

        # start value for manual object id generation
        current_value_id = models.ClimateValue.get_max_id(self.session)

        # for each region, get a mask, average climate variable over the mask and store the indicator value;
        # loop over features first, then over seasons, because mask generation is expensive
        for feature in nuts:

            # draw region mask (doesn't matter for which season we take the map shape)
            mask = geojson_polygon_to_mask(feature=feature,
                                           shape=t_data['summer'].shape,
                                           lat_idx=data['lat_idx'],
                                           lon_idx=data['lon_idx'])

            # create indicator values for summer and winter
            for season in list(CLIMATE_SEASON_SUFFIXES.keys()):
                # weighted average from region mask
                value = np.ma.average(t_data[season], weights=mask)

                # region ID must be cast to int (DBs don't like numpy dtypes from pandas)
                region_id = region_ids.get(feature.properties['NUTS_ID'], None)
                if region_id is not None:
                    region_id = int(region_id)

                # append an indicator value, manually generate object IDs for bulk saving
                current_value_id += 1
                objects.append(models.ClimateValue(id=current_value_id,
                                                   value=value,
                                                   region_id=region_id,
                                                   indicator_id=indicator_ids[season]))

                # # print some debugging output
                # print self.variable_name + ' ' + season, feature.properties['NUTS_ID'], value

                # # generate some plots for debugging
                # from matplotlib import pyplot as plt
                # plt.subplot(211)
                # plt.imshow(0.02 * t_data + mask * t_data, interpolation='none')
                # plt.subplot(212)
                # plt.imshow(t_data, interpolation='none')
                # plt.savefig('/tmp/' + feature.properties['NUTS_ID'] + '.png')

        # bulk-save all objects
        self.session.bulk_save_objects(objects)
        self.session.commit()

        self.done()


class TestClimateData(tasks.ORMTestTask):
    """Consistency checks for climate data
    """

    # min/max values to test against
    min_val = luigi.FloatParameter()
    max_val = luigi.FloatParameter()

    # max number of regions with missing value
    max_missing = luigi.IntParameter()

    # climate variable description (in indicator), including season
    description = luigi.Parameter()

    def requires(self):
        # testing one output doesn't really require all climate data to be loaded, but setting the
        # requirement to a specific task requires passing around lots of parameters
        yield LoadAllClimateData()

    def run(self):
        # load values for all 'official' NUTS2 regions (join is 'inner left' by default)
        query = self.session.query(models.ClimateValue) \
            .join(models.NUTS2Region) \
            .filter(models.ClimateValue.indicator.has(description=self.description))
        df = self.client.df_query(query)

        # get number of NUTS2 regions
        n_regions = self.session.query(sa.func.count(models.NUTS2Region.id)).scalar()

        # test values
        assert df['value'].min() >= self.min_val
        assert df['value'].max() <= self.max_val
        assert len(df) >= n_regions - self.max_missing

        self.done()


# list of climate data input file names and indicator descriptions, keyed by variable name
CLIMATE_DEFS = {
    'air': {'file_name': 'air.mon.1981-2010.ltm.v301.nc',
            'description': 'Mean temperature (C)'},
    'precip': {'file_name': 'precip.mon.ltm.v301.nc',
               'description': 'Mean precipitation (cm/month)'},
}


class LoadAllClimateData(tasks.ORMWrapperTask):
    """Wrapper task for loading all climate data
    """

    def clear(self):
        """For this task we want to clear requirements
        """
        self.mark_incomplete()

        for req in self.requires():
            req.clear()

    def requires(self):
        # generate one requirement for each listed climate variable
        for variable_name, settings in CLIMATE_DEFS.items():
            yield LoadClimateData(variable_name=variable_name,
                                  input_file=settings['file_name'],
                                  description=settings['description'])


class TestAllClimateData(tasks.ORMWrapperTask):
    def clear(self):
        """For this task we want to clear requirements
        """
        self.mark_incomplete()

        for req in self.requires():
            req.clear()

    def requires(self):
        yield TestClimateData(description=CLIMATE_DEFS['air']['description'] + CLIMATE_SEASON_SUFFIXES['winter'],
                              min_val=-10,
                              max_val=30,
                              max_missing=10)

        yield TestClimateData(description=CLIMATE_DEFS['air']['description'] + CLIMATE_SEASON_SUFFIXES['summer'],
                              min_val=5,
                              max_val=35,
                              max_missing=10)

        yield TestClimateData(description=CLIMATE_DEFS['precip']['description'] + CLIMATE_SEASON_SUFFIXES['winter'],
                              min_val=2,
                              max_val=50,
                              max_missing=10)

        yield TestClimateData(description=CLIMATE_DEFS['precip']['description'] + CLIMATE_SEASON_SUFFIXES['summer'],
                              min_val=0,
                              max_val=50,
                              max_missing=10)

