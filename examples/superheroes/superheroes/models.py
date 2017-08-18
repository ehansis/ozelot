"""Data models for project 'superheroes'

All stored URLs of wiki pages can be opened by prefixing them with ``http://marvel.wikia.com``.
"""

from sqlalchemy import Column, String, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship, validates

from ozelot.orm import base


class Universe(base.Base):
    """A story 'universe'
    """

    #: Universe name/code
    name = Column(String(128), index=True)

    #: wiki page URL
    url = Column(String(256), index=True)


class Place(base.Base):
    """A place (e.g. place of birth)
    """

    #: Place name
    name = Column(String(128), index=True)

    #: wiki page URL
    url = Column(String(256), index=True)

    # truncate some fields to the maximum field length (not the url, we want to know if this happens to be too long)
    @validates('name')
    def truncate(self, field, value):
        return self.truncate_to_field_length(field, value)


class Character(base.Base):
    """A character (hero, villain, ...)
    """

    #: Character name
    name = Column(String(128), index=True)

    #: wiki page URL
    url = Column(String(256), index=True)

    #: The character's *real* name
    real_name = Column(String(128))

    #: Occupation
    occupation = Column(String(128))

    #: Gender
    gender = Column(String(32))

    #: Height, in m
    height = Column(Float())

    #: Weight, in kg
    weight = Column(Float())

    #: Number of appearances
    number_of_appearances = Column(Integer())

    #: Year of first appearance
    first_apperance_year = Column(Integer(), index=True)

    #: Universe: relationship to a :class:`Universe` object
    universe = relationship(Universe, backref='characters')
    #: ID of the associated :class:`Universe` object
    universe_id = Column(Integer, ForeignKey(Universe.id))

    #: Place of birth: relationship to a :class:`Place` object
    place_of_birth = relationship(Place, backref='characters_born_here')
    #: ID of the associated :class:`Place` object for the place of birth
    place_of_birth_id = Column(Integer, ForeignKey(Place.id))

    @validates('name', 'real_name', 'occupation')
    def truncate(self, field, value):
        return self.truncate_to_field_length(field, value)


class Movie(base.Base):
    """A movie
    """

    #: Movie name
    name = Column(String(128), index=True)

    #: wiki page URL
    url = Column(String(256), index=True)

    #: Year of publication
    year = Column(Integer())

    #: Budget, as given in database, in US$
    budget = Column(Float())

    #: Budget, inflation adjusted to the current year
    budget_inflation_adjusted = Column(Float())

    #: IMDB rating
    imdb_rating = Column(Float())

    @validates('name')
    def truncate(self, field, value):
        return self.truncate_to_field_length(field, value)


class MovieAppearance(base.Base):
    """An association object for the many-to-many relationship between characters and movies
    """

    #: ID of the movie
    movie_id = Column(Integer, ForeignKey(Movie.id))
    #: Movie as object relationship
    movie = relationship(Movie, backref="character_apperances")

    #: ID of the character
    character_id = Column(Integer, ForeignKey(Character.id))
    #: Character as object relationship
    character = relationship(Character, backref="movie_appearances")

    #: type of appearance (Featured Characters, Supporting Characters, ...)
    appearance_type = Column(String(64), index=True)


def reinitialize():
    """Drop all tables for all models, then re-create them
    """
    from ozelot import client

    # import all additional models needed in this project
    # noinspection PyUnresolvedReferences
    from ozelot.orm.target import ORMTargetMarker

    client = client.get_client()
    base.Base.drop_all(client)
    base.Base.create_all(client)

