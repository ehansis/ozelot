"""Configuration for project 'eurominder'

Attributes:
    DB_PARAMS (dict): Database connection parameters
    DEFAULT_DB_PARAMS (str): Key of database connection to use by default
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
    'database': path.join(current_directory, 'eurominder.db')
}

DEFAULT_DB_PARAMS = DB_PARAMS

