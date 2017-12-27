"""Data integration pipeline for project 'leonardo', standard version
"""

import datetime

from ozelot.etl import tasks
from ozelot import config

from leonardo.common.input import ArtistsInputData, PaintingsInputData
from . import models


class LoadEverything(tasks.ORMWrapperTask):
    """Top-level wrapper task"""

    def requires(self):
        yield LoadPaintings()
        yield Tests()


class Tests(tasks.ORMWrapperTask):
    """Wrapper task for running all tests"""

    def requires(self):
        yield TestArtists()
        yield TestPaintings()


class LoadArtistsBase(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load artists to DB, generate base objects only"""

    object_classes = [models.ArtistBase]

    def requires(self):
        yield ArtistsInputData()

    def run(self):
        df = ArtistsInputData().load()

        # the base model only contains the wiki ID
        df = df[['wiki_id']]

        # append an ID column
        df['id'] = range(len(df))

        # store everything, done
        df.to_sql(name=models.ArtistBase.__tablename__,
                  con=self.client.engine,
                  if_exists='append',
                  index=False)

        self.done()


class LoadArtists(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load artist attributes to DB"""

    object_classes = [models.Artist]

    def requires(self):
        yield ArtistsInputData()
        yield LoadArtistsBase()

    def run(self):
        """Load all artists into the database
        """

        df = ArtistsInputData().load()

        # get base model instances, merge ID column via the unique wiki ID
        # (base and derived model instances must have the same ID values)
        base_data = self.client.df_query(self.session.query(models.ArtistBase))
        df = df.merge(base_data, on='wiki_id')

        # rename columns
        df.rename(columns={'artistLabel': 'name',
                           'genderLabel': 'gender'},
                  inplace=True)

        # columns that exist in the data model
        columns = ['name', 'id']

        # the extended model also stores the date of birth and gender
        if config.EXTENDED:
            columns += ['gender', 'year_of_birth']

        # keep only columns that exist in the data model
        df = df[columns]

        # store everything, done
        df.to_sql(name=models.Artist.__tablename__,
                  con=self.client.engine,
                  if_exists='append',
                  index=False)

        self.done()


class TestArtists(tasks.ORMTestTask):
    """Simple consistency checks for artist data"""

    def requires(self):
        yield LoadArtists()

    def run(self):
        df = self.client.df_query(self.session.query(models.Artist))

        assert len(df) == len(df.dropna(how='any')), "Found NaN values"
        assert df['wiki_id'].is_unique, "Wiki ID is not unique"

        if config.EXTENDED:
            assert df['year_of_birth'].min() > 0, "Found too small Date of Birth"
            assert df['year_of_birth'].max() < datetime.datetime.now().year, "Found too large Date of Birth"

        self.done()


class LoadPaintingsBase(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load paintings to DB, create base objects only"""

    object_classes = [models.Painting]

    def requires(self):
        yield LoadArtistsBase()
        yield PaintingsInputData()

    def run(self):
        df = PaintingsInputData().load()

        # get artist IDs, join to table via artist wiki ID
        artist_ids = self.client.df_query(self.session.query(models.Artist.wiki_id,
                                                             models.Artist.id))
        df['artist_id'] = df['creator_wiki_id'].map(artist_ids.set_index('wiki_id')['id'])

        # limit to columns that exist in the data model
        df = df[['wiki_id', 'artist_id']]

        # append an ID column
        df['id'] = range(len(df))

        # store everything, done
        df.to_sql(name=models.PaintingBase.__tablename__,
                  con=self.client.engine,
                  if_exists='append',
                  index=False)

        self.done()


class LoadPaintings(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load paintings to DB"""

    object_classes = [models.Painting]

    def requires(self):
        yield LoadPaintingsBase()
        yield PaintingsInputData()

    def run(self):
        df = PaintingsInputData().load()

        # rename columns
        df.rename(columns={'paintingLabel': 'name'}, inplace=True)

        # get base painting IDs, join them in via the wiki ID to get consistend ID values with the base objects
        base_data = self.client.df_query(self.session.query(models.PaintingBase))
        df = df.merge(base_data, on='wiki_id')

        # limit to columns that exist in the data model
        df = df[['name', 'area', 'decade', 'id']]

        # store everything, done
        df.to_sql(name=models.Painting.__tablename__,
                  con=self.client.engine,
                  if_exists='append',
                  index=False)

        self.done()


class TestPaintings(tasks.ORMTestTask):
    """Simple consistency checks for paintings"""

    def requires(self):
        yield LoadPaintings()

    def run(self):
        df = self.client.df_query(self.session.query(models.Painting))

        assert len(df['artist_id'].dropna()) > 0.8 * len(df), "Found too many missing artist IDs"
        assert len(df) == len(df.dropna(subset=[c for c in df.columns if not c == 'artist_id'],
                                        how='any')), "Found NaN values"
        assert df['wiki_id'].is_unique, "Wiki ID is not unique"
        assert df['area'].max() < 100., "Too large area values"
        assert df['area'].min() > 0.01 * 0.01, "Too small area values"

        self.done()
