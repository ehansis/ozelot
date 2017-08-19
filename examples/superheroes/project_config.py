"""Configuration for project 'superheroes'

Attributes:
    DB_PARAMS (dict): Database connection parameters
    DEFAULT_DB_PARAMS (str): Key of database connection to use by default
    REQUEST_CACHE_PATH (str): Path to file for web request cache
    UNIVERSES (list(str)): List of universes to load characters for
"""

from os import path

current_directory = path.dirname(__file__)

# database configuration: an sqlite database in the current directory
DB_PARAMS = {
    'driver': 'sqlite',
    'host': None,
    'port': None,
    'user': None,
    'password': None,
    'database': path.join(current_directory, 'superheroes.db')
}

DEFAULT_DB_PARAMS = DB_PARAMS

# Web request cache, file in the current directory
REQUEST_CACHE_PATH = path.join(current_directory, 'superheroes_web_cache.db')

# Selection of universes to ingest characters for, set to None to ingest all;
# Default selection: top 20 universes by number of character appearances in movies.
UNIVERSES = ['Earth-199999',
             'Earth-10005',
             'Earth-TRN414',
             'Earth-96283',
             'Earth-120703',
             'Earth-8096',
             'Earth-701306',
             'Earth-10022',
             'Earth-TRN011',
             'Earth-58460',
             'Earth-700029',
             'Earth-58732',
             'Earth-TRN554',
             'Earth-26320',
             'Earth-121698',
             'Earth-14123',
             'Earth-96173',
             'Earth-199673',
             'Earth-730911',
             'Earth-635972']
