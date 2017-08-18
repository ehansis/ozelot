import unittest
from os import path
import logging
import sys
import imp

# prepend the directory containing the project_config.py to the search path,
# to make it available upon importing ozelot.config
sys.path = [path.join(path.dirname(__file__), 'fixtures')] + sys.path

from ozelot import config


class TestConfig(unittest.TestCase):
    """Unit tests for the configuration module
    """

    def test_TESTING_SQLITE_DB_PATH(self):
        """Test the default path for the testing database.

        The default path should be ``testing.db`` in the directory containing this test.
        """
        self.assertEquals(config.TESTING_SQLITE_DB_PATH,
                          path.join(path.dirname(__file__), 'testing.db'))

    def test_value_override(self):
        """Test overriding a default value

        The project config of the logging module sets the log level to 'DEBUG' and defines some other testing values.
        """
        # reload the config module to make sure we get a fresh instance (nose shares module state between tests)
        imp.reload(config)

        self.assertEquals(config.LOG_LEVEL, logging.DEBUG)
        # noinspection PyUnresolvedReferences
        self.assertEquals(config.LOG_LEVEL_DEFAULT, logging.INFO)

        # this variable does not exist originally and does not have a backup of the default value
        # noinspection PyUnresolvedReferences
        self.assertEquals(config.TESTING_VARIABLE, 123)

        # # we could test for 'TESTING_VARIABLE_DEFAULT' not being set; however, the 'reload' statement
        # # above causes the testing variable to also be copied to 'TESTING_VARIABLE_DEFAULT'
        # self.assertIsNone(getattr(config, 'TESTING_VARIABLE_DEFAULT', None))
