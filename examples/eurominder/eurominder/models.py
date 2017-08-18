"""Data models for project 'eurominder'
"""

from sqlalchemy import Column, String, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship, backref

from ozelot.orm import base


class NUTS2Region(base.Base):
    """Metadata for a NUTS2 European Region
    """

    # official NUTS2 key
    key = Column(String(length=4), index=True, unique=True)

    # region name
    name = Column(String(length=64))


class EuroStatIndicator(base.Base):
    """Metadata for one socioeconomic indicator from EuroStat
    """

    # indicator ID number (corresponding to file name from EuroStat),
    # including leading zeros
    number = Column(String(length=5), index=True, unique=True)

    # indicator short description
    description = Column(String(length=128))

    # link to EuroStat page about that indicator
    # ("http://ec.europa.eu/eurostat/web/products-datasets/-/tgs" plus :attr:`number`)
    url = Column(String(length=256))


class EuroStatValue(base.Base):
    """One data point for socioeconomic data from EuroStat
    """

    # the value
    value = Column(Float())

    # year this value represents
    year = Column(Integer(), index=True)

    # reference to region this value represents
    region = relationship(NUTS2Region,
                          backref=backref("eurostat_values", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`NUTS2Region` object
    region_id = Column(Integer, ForeignKey(NUTS2Region.id))

    # reference to indicator metadata
    indicator = relationship(EuroStatIndicator,
                             backref=backref("values", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`EuroStatIndicator` object
    indicator_id = Column(Integer, ForeignKey(EuroStatIndicator.id))


class ClimateIndicator(base.Base):
    """Metadata for one climate indicator
    """

    # indicator short description
    description = Column(String(length=128))


class ClimateValue(base.Base):
    """One data point for climate data
    """

    # the value
    value = Column(Float())

    # reference to region this value represents
    region = relationship(NUTS2Region,
                          backref=backref("climate_values", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`NUTS2Region` object
    region_id = Column(Integer, ForeignKey(NUTS2Region.id))

    # reference to indicator metadata
    indicator = relationship(ClimateIndicator,
                             backref=backref("values", cascade="all, delete, delete-orphan"))
    #: ID of the associated :class:`ClimateIndicator` object
    indicator_id = Column(Integer, ForeignKey(ClimateIndicator.id))


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

