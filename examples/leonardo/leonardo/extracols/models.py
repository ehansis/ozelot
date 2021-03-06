"""Data models for project 'leonardo', version with 'extra columns'
"""

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from ozelot.orm import base


class Artist(base.Base):
    """Data representing an artist
    """

    #: custom table name, required to be able to import models from all modes for API documentation
    __tablename__ = "artist_extracols"

    #: wikidata id
    wiki_id = Column(String(length=16), index=True, unique=True)

    #: artist name
    name = Column(String(length=128))

    #: 'extra column' 1, for generic extensions
    extra_1 = Column(String(length=256))

    #: 'extra column' 2, for generic extensions
    extra_2 = Column(String(length=256))

    #: 'extra column' 3, for generic extensions
    extra_3 = Column(String(length=256))


class Painting(base.Base):
    """Data representing a painting
    """

    #: custom table name, required to be able to import models from all modes for API documentation
    __tablename__ = "painting_extracols"

    #: wikidata id
    wiki_id = Column(String(length=16), index=True, unique=True)

    #: paiting name
    name = Column(String(length=128))

    #: 'extra column' 1, for generic extensions
    extra_1 = Column(String(length=256))

    #: 'extra column' 2, for generic extensions
    extra_2 = Column(String(length=256))

    #: 'extra column' 3, for generic extensions
    extra_3 = Column(String(length=256))

    #: reference to artist
    artist = relationship(Artist, backref=backref("paintings", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`Artist` object
    artist_id = Column(Integer, ForeignKey(Artist.id))
