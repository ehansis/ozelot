from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()

from ozelot import client
from . import models


def decade_query():
    cl = client.get_client()
    session = cl.create_session()

    # NOTE: since the extra columns are strings, the filter on area (extra_1) does not behave as expected!
    query = session.query(models.Painting.extra_1.label('area'),
                          models.Painting.extra_2.label('decade')) \
        .filter(models.Painting.extra_2.between(1600, 2000)) \
        .filter(models.Painting.extra_1 < 5)

    decade_df = cl.df_query(query)

    decade_df['area'] = decade_df['area'].astype(float)
    decade_df['decade'] = decade_df['decade'].astype(int)

    session.close()
    return decade_df


def gender_query():
    cl = client.get_client()
    session = cl.create_session()

    query = session.query(models.Painting.extra_1.label('area'),
                          models.Artist.extra_2.label('gender')) \
        .join(models.Artist) \
        .filter(models.Painting.extra_2.between(1600, 2000)) \
        .filter(models.Painting.extra_1 < 5)

    gender_df = cl.df_query(query)

    gender_df['area'] = gender_df['area'].astype(float)

    session.close()
    return gender_df
