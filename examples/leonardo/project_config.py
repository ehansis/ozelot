"""Configuration for project 'leonardo'

Attributes:
    DB_PARAMS (dict): Database connection parameters
    DEFAULT_DB_PARAMS (str): Key of database connection to use by default
    DATA_DIR (str): Directory containing example data
    EXTENDED = True
                     model changes and partial re-running of the pipeline
    MODE = "kvstore"
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
    'database': path.join(current_directory, 'leonardo.db')
}

DEFAULT_DB_PARAMS = DB_PARAMS

DATA_DIR = path.join(current_directory, 'data')

EXTENDED = False

MODE = "kvstore"
