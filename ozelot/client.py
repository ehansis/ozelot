"""Database client and singleton client instance
"""
from builtins import str
from builtins import object

import keyring
import sqlalchemy as sa
from sqlalchemy import orm

from ozelot import config


# the singleton client instance
_client = None


def get_client():
    """Get or create the singleton client instance
    """
    global _client

    if _client is None:
        _client = Client(params=config.DEFAULT_DB_PARAMS)

    return _client


def set_client(client):
    """Store a client instance as singleton client

    Args:
        client (ozelot.client.Client): database client
    """
    global _client

    _client = client


class Client(object):
    """The database client.
    """

    def __init__(self, params=None, connection_string=None):
        """Instantiate a client object

        A client can be configured either from a parameters dictionary ``params`` or directly
        from an :mod:`sqlalchemy` connection string ``connection_string``. Exactly one of the two
        must be provided.

        Args:
            params (dict): database configuration, as defined in :mod:`ozelot.config`
            connection_string (str): :mod:`sqlalchemy` connection string
        """

        if params is None and connection_string is None:
            raise RuntimeError("Please provide either 'params' or 'connection_string'")

        if params is not None and connection_string is not None:
            raise RuntimeError("Please provide only on of 'params' or 'connection_string'")

        if params is not None:
            # log connection string with password hidden
            # noinspection PyTypeChecker
            connection_string_no_pw = self.get_connection_string(params=params, hide_password=True)
            config.logger.info("Client connecting to: " + connection_string_no_pw)

            # noinspection PyTypeChecker
            connection_string = self.get_connection_string(params=params, hide_password=False)

        else:
            # noinspection PyTypeChecker
            config.logger.info("Client connecting to: " + connection_string)

        # create the engine
        self.engine = sa.create_engine(connection_string)

        # turn on foreign key support for SQLite (required for cascading deletes etc.)
        if connection_string.startswith('sqlite://'):

            def on_connect(conn, _):
                conn.execute('pragma foreign_keys=ON')

            from sqlalchemy import event
            event.listen(self.engine, 'connect', on_connect)

        # create a session factory
        self.session_maker = orm.sessionmaker(bind=self.get_engine())

    def get_engine(self):
        """Get the database engine
        """
        return self.engine

    def create_session(self):
        """Create a new :mod:`sqlalchemy` ORM session

        .. seealso:: `sqlalchemy documentation on sessions <http://docs.sqlalchemy.org/en/latest/orm/session.html>`_
        """
        return self.session_maker()

    @staticmethod
    def store_password(params, password):
        """Store the password for a database connection using :mod:`keyring`

        Use the ``user`` field as the user name and ``<host>:<driver>`` as service name.

        Args:
            params (dict): database configuration, as defined in :mod:`ozelot.config`
            password (str): password to store
        """
        user_name = params['user']
        service_name = params['host'] + ':' + params['driver']
        keyring.set_password(service_name=service_name,
                             username=user_name,
                             password=password)

    @staticmethod
    def _get_password(params):
        """Get the password for a database connection from :mod:`keyring`

        Args:
            params (dict): database configuration, as defined in :mod:`ozelot.config`

        Returns:
            str: password
        """
        user_name = params['user']
        service_name = params['host'] + ':' + params['driver']
        return keyring.get_password(service_name=service_name,
                                    username=user_name)

    @staticmethod
    def get_connection_string(params, hide_password=True):
        """Get a database connection string

        Args:
            params (dict): database configuration, as defined in :mod:`ozelot.config`
            hide_password (bool): if True, the password is hidden in the returned string
                (use this for logging purposes).

        Returns:
            str: connection string
        """
        connection_string = params['driver'] + '://'

        user = params.get('user', None)
        password = params.get('password', None)
        host = params.get('host', None)
        port = params.get('port', None)
        database = params.get('database', None)

        if database is None:
            raise ValueError("Field 'database' of connection parameters cannot be None.")

        # if password is not set, try to get it from keyring
        if password is None and user is not None:
            # noinspection PyTypeChecker
            password = Client._get_password(params)

            if password is None:
                raise RuntimeError("Password not defined and not available in keyring.")

        # don't add host/port/user/password if no host given
        if host is not None:

            # don't add user/password if user not given
            if user is not None:
                connection_string += user

                # omit zero-length passwords
                if len(password) > 0:
                    if hide_password:
                        connection_string += ":[password hidden]"
                    else:
                        connection_string += ":" + password

                connection_string += "@"

            connection_string += host

            if port is not None:
                connection_string += ':' + str(port)

        # noinspection PyTypeChecker
        connection_string += '/' + database

        return connection_string

    def df_query(self, query, with_labels=False):
        """
        Run a :mod:`sqlalchemy` query and return result as a :class:`pandas.DataFrame`

        Args:

            query (sqlalchemy.orm.query.Query): query object, usually generated by :func:`session.query()` in
                an :class:`sqlalchemy.orm.session.Session`

            with_labels (bool): A query for fields with the same name from different tables will cause problems
                when converting it to a :class:`pandas.DataFrame`, because there will be duplicate column names.
                When setting `with_labels=True`, disambiguation labels are assigned to all (!)
                fields in the query - the field name is prefixed with the column name. This enables
                querying fields with identical names from multiple tables but getting unique column names in the output.

        :return: query result as :class:`pandas.DataFrame`
        """
        import pandas as pd

        if with_labels:
            query = query.with_labels()

        # compile sql statement, including arguments
        statement = query.statement.compile(self.engine)

        # run query
        return pd.read_sql_query(sql=statement, con=self.engine)

