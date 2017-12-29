"""Data models for project 'leonardo', key-value-store version
"""

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from ozelot.orm import base


class Entity(base.Base):
    """Data representing an entity (e.g. painting or artist)
    """

    #: entity type
    type = Column(String(length=16), index=True)

    @staticmethod
    def query_with_attributes(type_to_query, client):
        """Query all entities of a specific type, with their attributes

        Args:
            type_to_query (str): type of entity to query
            client: DB client to perform query with

        Returns:
            pandas.DataFrame: table of entities, with attributes as columns
        """
        session = client.create_session()

        # query all data
        query = session.query(Attribute.name,
                              Attribute.value,
                              Entity.id) \
            .join(Entity) \
            .filter(Entity.type == type_to_query)

        df = client.df_query(query)

        session.close()

        # don't store NaN values
        df = df.dropna(how='any')

        # pivot attribute names to columns, drop column names to one level ('unstack' generated multi-level names)
        df = df.set_index(['id', 'name']).unstack().reset_index()
        # noinspection PyUnresolvedReferences
        df.columns = ['id'] + list(df.columns.get_level_values(1)[1:])

        return df


class Attribute(base.Base):
    """Data representing an attribute of an entity
    """

    #: attribute name
    name = Column(String(length=32))

    #: attribute value
    value = Column(String(length=256))

    #: reference to the respective entity
    entity = relationship(Entity, backref=backref("attributes", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`Entity` object
    entity_id = Column(Integer, ForeignKey(Entity.id))
