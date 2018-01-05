from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()

import pandas as pd

from ozelot import client
from . import models


def decade_query():
    cl = client.get_client()

    paintings = models.Entity.query_with_attributes('painting', cl)
    paintings['area'] = pd.to_numeric(paintings['area'])
    paintings['decade'] = pd.to_numeric(paintings['decade']).astype(int)

    paintings = paintings[(1600 <= paintings['decade']) &
                          (paintings['decade'] < 2000) &
                          (paintings['area'] < 5)]

    return paintings


def gender_query():
    cl = client.get_client()

    paintings = models.Entity.query_with_attributes('painting', cl)
    paintings['area'] = pd.to_numeric(paintings['area'])
    paintings['decade'] = pd.to_numeric(paintings['decade']).astype(int)
    paintings['artist_id'] = pd.to_numeric(paintings['artist_id'])

    paintings = paintings[(1600 <= paintings['decade']) &
                          (paintings['decade'] < 2000) &
                          (paintings['area'] < 5)]

    artists = models.Entity.query_with_attributes('artist', cl)

    paintings = paintings.merge(artists[['id', 'gender']], left_on='artist_id', right_on='id')

    return paintings
