import datetime
from os import path

import pandas as pd

from ozelot import config
from ozelot.etl import tasks


class ArtistsInputData(tasks.InputFileTask):
    """Input data file for artists data, with loading method"""

    input_file = path.join(config.DATA_DIR, "artists.csv")

    def load(self):
        """Load the data file, do some basic type conversions
        """

        df = pd.read_csv(self.input_file,
                         encoding='utf8')

        df['wiki_id'] = df['artist'].str.split('/').str[-1]

        # some years of birth are given as timestamps with prefix 't', convert to string
        timestamps = df['dob'].str.startswith('t')
        df.loc[timestamps, 'dob'] = df.loc[timestamps, 'dob'].str[1:].apply(
            lambda s: str(datetime.datetime.fromtimestamp(float(s))))

        df['year_of_birth'] = df['dob'].str[:4].astype(int)

        return df


class PaintingsInputData(tasks.InputFileTask):
    """Input data file for paintings, with loading method"""

    input_file = path.join(config.DATA_DIR, "paintings.csv")

    def load(self):
        """Load the data file, do some basic type conversions
        """

        df = pd.read_csv(self.input_file,
                         encoding='utf8')

        df['wiki_id'] = df['painting'].str.split('/').str[-1]
        df['creator_wiki_id'] = df['creator'].str.split('/').str[-1]
        df['decade'] = (df['inception'].str[:4].astype(float) / 10.).astype(int) * 10
        df['area'] = df['width'] * df['height']

        return df