"""Data models for project 'leonardo', standard version
"""

from sqlalchemy import Column, String, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from ozelot import config
from ozelot.orm import base


class Artist(base.Base):
    """Data representing an artist
    """

    #: wikidata id
    wiki_id = Column(String(length=16), index=True, unique=True)

    #: artist name
    name = Column(String(length=128))

    #: gender (extended data - see documentation for how to handle model changes)
    gender = Column(String(length=16)) if config.EXTENDED else None

    #: year of birth (extended data - see documentation for how to handle model changes)
    year_of_birth = Column(Integer()) if config.EXTENDED else None


class Painting(base.Base):
    """Data representing a painting
    """

    #: wikidata id
    wiki_id = Column(String(length=16), index=True, unique=True)

    #: paiting name
    name = Column(String(length=128))

    #: decade of inception (e.g. 1510, 1920, ...)
    decade = Column(Integer())

    #: painting area, sq m
    area = Column(Float())

    #: reference to artist
    artist = relationship(Artist, backref=backref("paintings", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`Artist` object
    artist_id = Column(Integer, ForeignKey(Artist.id))
