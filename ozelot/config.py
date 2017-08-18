"""ozelot configuration

This module defines default configuration values for the ozelot package.
If you want to change any of these values, create a file ``project_config.py``
and place it anywhere in the Python path used for the respective project.
If such a module is found, any variables found in it will be added to the configuration.
Default values will be stored as ``<variable name>_DEFAULT``.

At the very least, your ``project_config.py`` will have to define the connection
parameters for the database you want to use, and set these as ``DEFAULT_DB_PARAMS``.

Database connection parameters are stored as dictionaries with the following structure:

.. code-block:: python

    TEMPLATE_DB_PARAMS = {
        'driver': 'postgresql+psycopg2',
        'host': 'my.server.com',
        'port': 5432,
        'user': 'myuser',
        'password': None,
        'database': 'mydb'
    }

Multiple sets of connection parameters can be stored, as separate variables (with names of your choosing).
The pipeline will use the ``DEFAULT_DB_PARAMS`` by default. If needed, you can switch between different
configurations by setting this parameter to your desired parameter set, before starting any pipeline operations.

The ``driver`` is the driver + dialect string for :mod:`sqlalchemy`. See
`the documentation <http://docs.sqlalchemy.org/en/latest/core/engines.html#supported-databases>`_ for details
on supported databases and drivers.
Pass the desired dictionary into :class:`ozelot.client.Client` to create a database connection.
``user``, ``password``, ``host`` and ``port`` can be omitted (or set to ``None``) if not needed.
For SQLite file-based databases, set ``database`` to the file path and omit ``host``, ``port``,
``user`` and ``password``.

If the password field is omitted from the dictionary (or set to ``None``), :class:`ozelot.client.Client` will
try to retrieve it from a :mod:`keyring` password store, using the ``user`` field as the user name for
keyring and ``<host>:<driver>`` as service name. :meth:`ozelot.client.Client.store_password` is a convenience function
for storing the password in keyring. Set ``password`` to an empty string to not use a password.

If you choose to store the password as clear text, make sure to set permissions appropriately
(``0600``) on the ``project_config.py`` file.

Attributes:
    TESTING_SQLITE_DB_PATH (str): Path to use for the SQLite database file used in unit tests.
        Default: ``testing.db`` in the directory of the tests package.

    LOG_LEVEL (int): Default log level for :mod:logging

    TEMPLATE_DB_PARAMS (dict): Template dictionary for definition of database connection parameters.

    DEFAULT_DB_PARAMS (dict): Default database parameters to use.

    REQUEST_CACHE_PATH: File path where to store request cache (note: '.db' will be appended to the given path)

"""
from builtins import str

import sys
from os import path
import logging
import types

#
# Logging
#

# configure a basic logging client
logger = logging.getLogger('ozelot')
logger_handler = logging.StreamHandler()
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_handler.setFormatter(logger_formatter)
logger.addHandler(logger_handler)

# the default log level
LOG_LEVEL = logging.INFO

# the log level may have been overwritten in the project-specific config, need
# to retrieve it here, because loading of the project-specific config already logs
try:
    # noinspection PyUnresolvedReferences
    import project_config

    logger.setLevel(getattr(project_config, 'LOG_LEVEL', LOG_LEVEL))
except ImportError:
    logger.setLevel(LOG_LEVEL)
logger_handler.setLevel(logger.level)

logger.debug("Configured logging!")

#
# Databases
#

# The path to the SQLite DB file to use for unit tests
try:
    # noinspection PyUnresolvedReferences
    from ozelot import tests

    TESTING_SQLITE_DB_PATH = path.join(path.dirname(tests.__file__), 'testing.db')
except ImportError:
    # tests not present, ignore
    pass

# A template for defining database connections (see docstring at top for explanation)
TEMPLATE_DB_PARAMS = {
    'driver': 'postgresql+psycopg2',
    'host': 'my.server.com',
    'port': 5432,
    'user': 'myuser',
    'password': None,
    'database': 'mydb'
}

DEFAULT_DB_PARAMS = TEMPLATE_DB_PARAMS

#
# Web request cache
#

# The path to the file to store the request cache in - default is next to this file as '_web_cache.db'

REQUEST_CACHE_PATH = path.join(path.dirname(__file__), '_web_cache.db')

#
# Supporting tools
#

# Location of 'dot' executable, required (only) for rendering data model and pipeline diagrams.
# Default: in same directory as the Python interpreter
DOT_EXECUTABLE = path.join(path.dirname(sys.executable), 'dot')

#
# Load the project-specific configuration
#

# try importing project-specific configuration
try:
    # noinspection PyUnresolvedReferences
    import project_config

    logger.info("Reading project configuration from " + project_config.__file__)

    # get reference to current module
    this_module = sys.modules[__name__]

    # import all non-private, non-module attributes starting with an uppercase letter
    for attr in dir(project_config):
        if not attr.startswith('__'):

            old_value = getattr(this_module, attr, None)

            # skip modules
            if isinstance(old_value, types.ModuleType):
                continue

            # make backup of old value
            if old_value is not None:
                setattr(this_module, attr + '_DEFAULT', getattr(this_module, attr))

            # set new value
            new_value = getattr(project_config, attr)
            setattr(this_module, attr, new_value)

            logger.debug(u"\tRead configuration value from project_config: {:s} = {:s}"
                         u"".format(attr, str(new_value)))

except ImportError:
    logger.debug("Could not find a 'project_config' module to import")
