"""Data integration pipeline for project 'leonardo', key-value-store version
"""

import datetime

from ozelot import config
from ozelot.etl import tasks

from . import models
from leonardo.common.input import ArtistsInputData, PaintingsInputData


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


# noinspection PyUnresolvedReferences
class EntityCreatorMixin(object):
    """Clearing function for a task that generates entities"""

    #: the entity type to clear (str), to be defined in derived classes
    type = None

    def clear(self):
        entities = self.session.query(models.Entity) \
            .filter(models.Entity.type == self.type)

        # Iterate over objects to delete to cascade the deletes to the linked
        # entities. For deletes on a query, there is no in-Python cascading
        # of delete statements in sqlalchemy, so the associated values would not
        # be deleted e.g. for SQLite databases.
        for entity in entities:
            self.session.delete(entity)

        self.mark_incomplete()

    def store(self, df, attribute_columns):
        """Store entities and their attributes

        Args:
            df (pandas.DataFrame): data to store (storing appends 'id' and 'type' columns!)
            attribute_columns (list(str)): list of column labels that define attributes
        """

        # ID start values depend on currently stored entities/attributes!
        entity_id_start = models.Entity.get_max_id(self.session) + 1
        attribute_id_start = models.Attribute.get_max_id(self.session) + 1

        # append ID and type columns
        df['id'] = range(entity_id_start, entity_id_start + len(df))
        df['type'] = self.type

        # store entities
        df[['id', 'type']].to_sql(name=models.Entity.__tablename__,
                                  con=self.client.engine,
                                  if_exists='append',
                                  index=False)

        # store attributes
        for col in attribute_columns:
            # ID column of df is the entity ID of the attribute
            attr_df = df[[col, 'id']].rename(columns={'id': 'entity_id',
                                                      col: 'value'})
            attr_df['name'] = col

            # add entity ID column, need to respect already existing entities
            attr_df['id'] = range(attribute_id_start, attribute_id_start + len(df))
            attribute_id_start += len(df)

            # store
            attr_df.to_sql(name=models.Attribute.__tablename__,
                           con=self.client.engine,
                           if_exists='append',
                           index=False)


class LoadArtists(EntityCreatorMixin, tasks.ORMTask):
    """Load artists to DB"""

    type = "artist"

    def requires(self):
        yield ArtistsInputData()

    def run(self):
        """Load all artists into the database
        """

        df = ArtistsInputData().load()

        # rename columns
        df.rename(columns={'artistLabel': 'name',
                           'genderLabel': 'gender'},
                  inplace=True)

        # attribute columns that exist in the data model
        attribute_columns = ['name', 'wiki_id']

        # the extended model also stores the date of birth and gender
        if config.EXTENDED:
            attribute_columns += ['gender', 'year_of_birth']

        # store entities and attributes
        self.store(df, attribute_columns)

        self.done()


class TestArtists(tasks.ORMTestTask):
    """Simple consistency checks for artist data"""

    def requires(self):
        yield LoadArtists()

    def run(self):
        df = models.Entity.query_with_attributes('artist', self.client)

        assert len(df) == len(df.dropna(how='any')), "Found NaN values"
        assert df['wiki_id'].is_unique, "Wiki ID is not unique"

        if config.EXTENDED:
            assert df['year_of_birth'].astype(int).min() > 0, "Found too small Date of Birth"
            assert df['year_of_birth'].astype(int).max() < datetime.datetime.now().year, "Found too large Date of Birth"

        self.done()


class LoadPaintings(EntityCreatorMixin, tasks.ORMTask):
    """Load paintings to DB"""

    type = 'painting'

    def requires(self):
        yield LoadArtists()
        yield PaintingsInputData()

    def run(self):
        """Load all paintings into the database
        """

        df = PaintingsInputData().load()

        # rename columns
        df.rename(columns={'paintingLabel': 'name'}, inplace=True)

        # get artist IDs, map via artist wiki ID
        artists = models.Entity.query_with_attributes('artist', self.client)
        df['artist_id'] = df['creator_wiki_id'].map(artists.set_index('wiki_id')['id'])

        # define attributes to create
        attribute_columns = ['name', 'wiki_id', 'area', 'decade', 'artist_id']

        # store entities and attributes
        self.store(df, attribute_columns)

        self.done()


class TestPaintings(tasks.ORMTestTask):
    """Simple consistency checks for paintings"""

    def requires(self):
        yield LoadPaintings()

    def run(self):
        df = models.Entity.query_with_attributes('painting', self.client)

        assert len(df['artist_id'].dropna()) > 0.8 * len(df), "Found too many missing artist IDs"
        assert len(df) == len(df.dropna(subset=[c for c in df.columns if not c == 'artist_id'],
                                        how='any')), "Found NaN values"
        assert df['wiki_id'].is_unique, "Wiki ID is not unique"
        assert df['area'].astype(float).max() < 100., "Too large area values"
        assert df['area'].astype(float).min() > 0.01 * 0.01, "Too small area values"

        self.done()
