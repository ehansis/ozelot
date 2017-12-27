from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()

from ozelot import client
from . import models


def decade_query():
    cl = client.get_client()
    session = cl.create_session()

    query = session.query(models.Painting.area,
                          models.Painting.decade) \
        .filter(models.Painting.decade.between(1600, 2000)) \
        .filter(models.Painting.area < 5)

    decade_df = cl.df_query(query)

    session.close()
    return decade_df


def gender_query():
    cl = client.get_client()
    session = cl.create_session()

    query = session.query(models.Painting.area,
                          models.Artist.gender) \
        .join(models.Artist) \
        .filter(models.Painting.decade.between(1600, 2000)) \
        .filter(models.Painting.area < 5) \
        .order_by(models.Painting.area)

    gender_df = cl.df_query(query)

    session.close()
    return gender_df
