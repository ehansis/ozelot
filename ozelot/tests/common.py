"""Common functionality and utility functions for unit tests
"""

import os

from ozelot import client
from ozelot import config


def get_test_db_client():
    """Get client for test database

    Returns
        :mod:`ozelot.client.Client`: database client
    """
    return client.Client(connection_string='sqlite:///' + config.TESTING_SQLITE_DB_PATH)


def remove_test_db_file():
    """Remove the test database file (if it exists)
    """
    if os.path.exists(config.TESTING_SQLITE_DB_PATH):
        os.remove(config.TESTING_SQLITE_DB_PATH)


def get_fixtures_path():
    """Get path to test fixtures directory

    Returns
        str: path to test fixtures directory
    """
    return os.path.join(os.path.dirname(__file__), 'fixtures')
