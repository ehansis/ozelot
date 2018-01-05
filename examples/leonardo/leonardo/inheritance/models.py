"""Data models for project 'leonardo', version with inheritance
"""

from sqlalchemy import Column, String, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship, backref

from ozelot import config
from ozelot.orm import base


class ArtistBase(base.Base):
    """Data representing a base artist object
    """

    #: wikidata id
    wiki_id = Column(String(length=16), index=True, unique=True)


class Artist(ArtistBase):
    """Artist with attributes
    """

    #: custom table name, required to be able to import models from all modes for API documentation
    __tablename__ = "artist_inheritance"

    #: Foreign-key relationship to associated base object
    id = Column(Integer, ForeignKey(ArtistBase.id), primary_key=True)

    #: artist name
    name = Column(String(length=128))

    #: gender (extended data - see documentation for how to handle model changes)
    gender = Column(String(length=16)) if config.EXTENDED else None

    #: year of birth (extended data - see documentation for how to handle model changes)
    year_of_birth = Column(Integer()) if config.EXTENDED else None


class PaintingBase(base.Base):
    """Data representing a base painting object
    """

    #: wikidata id
    wiki_id = Column(String(length=16), index=True, unique=True)

    #: reference to artist
    artist = relationship(ArtistBase, backref=backref("paintings", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`Artist` object
    artist_id = Column(Integer, ForeignKey(ArtistBase.id))


class Painting(PaintingBase):
    """Painting with attributes
    """

    #: custom table name, required to be able to import models from all modes for API documentation
    __tablename__ = "painting_inheritance"

    #: Foreign-key relationship to associated base object
    id = Column(Integer, ForeignKey(PaintingBase.id), primary_key=True)

    #: paiting name
    name = Column(String(length=128))

    #: painting area, sq m
    area = Column(Float())

    #: decade of inception (e.g. 1510, 1920, ...)
    decade = Column(Integer())
