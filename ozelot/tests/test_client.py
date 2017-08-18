"""Unit tests for :mod:`ozelot.client`
"""
from builtins import range

import random
import unittest
import string

import keyring
import sqlalchemy as sa

from ozelot import client, config
from ozelot.orm import base
from ozelot.tests import common


class MyModelD(base.Base):
    my_field = sa.Column(sa.Integer())


class MyModelD2(base.Base):
    d_id = sa.Column(sa.Integer(), sa.ForeignKey(MyModelD.id))
    my_field = sa.Column(sa.String())


class TestConnectionStrings(unittest.TestCase):
    """Tests for the connection string generation
    """

    def test01(self):
        """Basic postgres connection
        """

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user': 'myuser',
            'password': 'supersecret',
            'database': 'mydb'
        }

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "postgresql+psycopg2://myuser:supersecret@my.server.com:5432/mydb")

        s = client.Client.get_connection_string(params)
        self.assertEqual(s, "postgresql+psycopg2://myuser:[password hidden]@my.server.com:5432/mydb")

    def test02(self):
        """Connection with empty password
        """

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user': 'myuser',
            'password': '',
            'database': 'mydb'
        }

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "postgresql+psycopg2://myuser@my.server.com:5432/mydb")

        s = client.Client.get_connection_string(params)
        self.assertEqual(s, "postgresql+psycopg2://myuser@my.server.com:5432/mydb")

    def test03(self):
        """Connection with no user set
        """

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'password': 'lalala',
            'database': 'mydb'
        }

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "postgresql+psycopg2://my.server.com:5432/mydb")

        s = client.Client.get_connection_string(params)
        self.assertEqual(s, "postgresql+psycopg2://my.server.com:5432/mydb")

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user': None,
            'password': 'lalala',
            'database': 'mydb'
        }

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "postgresql+psycopg2://my.server.com:5432/mydb")

        s = client.Client.get_connection_string(params)
        self.assertEqual(s, "postgresql+psycopg2://my.server.com:5432/mydb")

    def test04(self):
        """Connection with no port set
        """

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': None,
            'user': 'myuser',
            'password': 'lalala',
            'database': 'mydb'
        }

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "postgresql+psycopg2://myuser:lalala@my.server.com/mydb")

    def test05(self):
        """Connection with no host set (e.g. sqlite)
        """

        params = {
            'driver': 'sqlite',
            'host': None,
            'port': None,
            'user': 'myuser',
            'password': 'lalala',
            'database': 'mydb.db'
        }

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "sqlite:///mydb.db")

    def test06(self):
        """Get password from :mod:`keyring`
        """
        password = ''.join(random.choice(string.ascii_letters) for _ in range(64))

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user': 'myuser',
            'password': None,
            'database': 'mydb'
        }

        # set the password
        client.Client.store_password(params, password)

        # retrieve password directly from keyring
        pw = keyring.get_password(service_name='my.server.com:postgresql+psycopg2', username='myuser')
        self.assertEqual(pw, password)

        s = client.Client.get_connection_string(params, hide_password=False)
        self.assertEqual(s, "postgresql+psycopg2://myuser:{:s}@my.server.com:5432/mydb"
                            "".format(password))

    def test07(self):
        """If password is not set and does not exist in :mod:`keyring`, throw an error.
        """
        # use a long random user name to make sure password does not exist yet
        user = ''.join(random.choice(string.ascii_letters) for _ in range(64))

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user':  user,
            'password': None,
            'database': 'mydb'
        }

        self.assertRaises(RuntimeError,
                          client.Client.get_connection_string, params, {'hide_password': True})
        self.assertRaises(RuntimeError,
                          client.Client.get_connection_string, params, {'hide_password': False})

    def test08(self):
        """Database field must not be empty
        """

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user':  'me',
            'password': 'yep'
        }

        self.assertRaises(ValueError,
                          client.Client.get_connection_string, params, {'hide_password': True})

        params = {
            'driver': 'postgresql+psycopg2',
            'host': 'my.server.com',
            'port': 5432,
            'user':  'me',
            'password': 'yep',
            'database': None
        }

        self.assertRaises(ValueError,
                          client.Client.get_connection_string, params, {'hide_password': True})


class TestClientCreation(unittest.TestCase):
    """Tests for creating a client
    """

    def test01(self):
        """SQLite connection to test database
        """
        # create client via connection string
        common.remove_test_db_file()
        client1 = common.get_test_db_client()

        # create some data
        MyModelD().create_table(client1)
        session = client1.create_session()
        session.add(MyModelD(my_field=17))
        session.add(MyModelD(my_field=18))
        session.add(MyModelD(my_field=19))
        session.commit()
        session.close()

        # create connection via parameter dict
        params = {
            'driver': 'sqlite',
            'database': config.TESTING_SQLITE_DB_PATH
        }
        client2 = client.Client(params=params)
        session2 = client2.create_session()
        count = session.query(MyModelD).count()
        session2.close()

        self.assertEqual(count, 3)

        common.remove_test_db_file()

    def test02(self):
        """Supplying both params and a connection string raises an error
        """
        self.assertRaises(RuntimeError, client.Client, params=dict(la="la"), connection_string="lala")

    def test03(self):
        """Supplying neither params nor a connection string raises an error
        """
        self.assertRaises(RuntimeError, client.Client, params=None, connection_string=None)


class TestQueryToDataFrame(unittest.TestCase):
    """Tests for querying directly to a :class:`pandas.DataFrame`
    """

    def setUp(self):
        common.remove_test_db_file()
        self.client = common.get_test_db_client()

    def tearDown(self):
        common.remove_test_db_file()

    def test01(self):
        """Query some data from one object
        """

        # create some data
        MyModelD().create_table(self.client)
        session = self.client.create_session()
        session.add(MyModelD(my_field=17))
        session.add(MyModelD(my_field=18))
        session.add(MyModelD(my_field=19))
        session.commit()

        # query all to a DataFrame
        query = session.query(MyModelD)
        df = self.client.df_query(query)
        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[0].to_dict(), dict(id=1, my_field=17))
        self.assertEqual(df.iloc[1].to_dict(), dict(id=2, my_field=18))
        self.assertEqual(df.iloc[2].to_dict(), dict(id=3, my_field=19))

        # query single entry to a DataFrame
        query = session.query(MyModelD).filter(MyModelD.my_field == 18)
        df = self.client.df_query(query)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0].to_dict(), dict(id=2, my_field=18))

        session.close()

    def test02(self):
        """Querying fields with identical names from multiple tables results duplicate column names.
        There will be an `SAWarning` shown when running the query.
        """

        # create some data
        MyModelD().create_table(self.client)
        MyModelD2().create_table(self.client)
        session = self.client.create_session()
        session.add(MyModelD(my_field=17))
        session.commit()
        session.add(MyModelD2(d_id=1, my_field='lala'))
        session.commit()

        query = session.query(MyModelD, MyModelD2).join(MyModelD2)
        df = self.client.df_query(query)

        # column 'my_field' id duplicated
        self.assertEqual(len([c for c in df.columns if c == 'my_field']), 2)

    def test03(self):
        """Querying fields with identical names from multiple tables with disambiguation
        """

        # create some data
        MyModelD().create_table(self.client)
        MyModelD2().create_table(self.client)
        session = self.client.create_session()
        session.add(MyModelD(my_field=17))
        session.commit()
        session.add(MyModelD2(d_id=1, my_field='lala'))
        session.commit()

        query = session.query(MyModelD, MyModelD2).join(MyModelD2)
        df = self.client.df_query(query, with_labels=True)

        self.assertIn('mymodeld_my_field', df.columns)
        self.assertIn('mymodeld2_my_field', df.columns)


