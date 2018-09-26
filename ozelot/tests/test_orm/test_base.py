"""Unit tests for ORM base model class
"""
from builtins import object

import os
import unittest

import sqlalchemy as sa
from sqlalchemy import exc, select, orm, func

from ozelot.tests import common
from ozelot.orm import base
from ozelot import config


class MyModelA(base.Base):
    my_field = sa.Column(sa.Integer())


class MyModelB(base.Base):
    my_other_field = sa.Column(sa.Integer())


# derived class
class MyModelB2(MyModelB):
    yet_another_field = sa.Column(sa.Integer())
    id = sa.Column(sa.Integer, sa.ForeignKey('mymodelb.id', ondelete="CASCADE"), primary_key=True)


class MyModelC(base.Base):
    b_id = sa.Column(sa.Integer(), sa.ForeignKey(MyModelB.id))
    b = orm.relationship(MyModelB)


class MyModelValidation(base.Base):
    my_validated_string = sa.Column(sa.String(10))
    my_unvalidated_string = sa.Column(sa.String(10))

    @orm.validates('my_validated_string')
    def truncate(self, field, value):
        return self.truncate_to_field_length(field, value)


class MyNotAModel(object):
    i = 5


class BaseTest(unittest.TestCase):
    def setUp(self):
        common.remove_test_db_file()
        self.client = common.get_test_db_client()

    def tearDown(self):
        common.remove_test_db_file()

    def test01(self):
        """Test creation and removal of ORM model tables
        """
        # get current DB state
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())

        # there should be no tables yet
        self.assertEqual(len(metadata.tables), 0)

        # create a new table for the model
        MyModelA().create_table(self.client)

        # now there is one table
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        self.assertEqual(len(metadata.tables), 1)

        # table name = lower case class name
        self.assertEqual(list(metadata.tables.keys())[0], 'mymodela')

        # 2 columns: id and my_field
        table = metadata.tables['mymodela']
        self.assertEqual(len(table.columns), 2)
        self.assertIn('id', table.columns)
        self.assertIn('my_field', table.columns)

        # drop the table
        MyModelA().drop_table(self.client)
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        self.assertEqual(len(metadata.tables), 0)

    def test02(self):
        """Trying to create a table twice results in an :mod:`sqlalchemy` error
        """
        MyModelA().create_table(self.client)
        self.assertRaises(exc.OperationalError, MyModelA().create_table, self.client)

    def test03(self):
        """Create two tables, drop one, check the other is still there
        """
        MyModelA().create_table(self.client)
        MyModelB().create_table(self.client)

        # now there are two tables now
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        self.assertEqual(len(metadata.tables), 2)

        MyModelA().drop_table(self.client)

        # one table left
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        self.assertEqual(len(metadata.tables), 1)
        self.assertEqual(list(metadata.tables.keys())[0], 'mymodelb')

    def test04(self):
        """Create a table and populate it with some objects
        """
        MyModelB().create_table(self.client)

        # create some objects
        session = self.client.create_session()
        session.add(MyModelB(my_other_field=17))
        session.add(MyModelB(my_other_field=18))
        session.add(MyModelB(my_other_field=19))
        session.commit()

        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        query = select([func.count()]).select_from(metadata.tables['mymodelb'])
        count = self.client.get_engine().execute(query).scalar()
        self.assertEqual(count, 3)

        session.close()

    def test05(self):
        """Query max id for a simple object
        """
        MyModelB().create_table(self.client)
        session = self.client.create_session()

        self.assertEqual(MyModelB.get_max_id(session), 0)

        # create some objects
        session.add(MyModelB(my_other_field=17))
        session.add(MyModelB(my_other_field=18))
        session.add(MyModelB(my_other_field=19))
        session.commit()

        self.assertEqual(MyModelB.get_max_id(session), 3)

        session.close()

    def test06(self):
        """Query max id for a derived class
        """
        MyModelB().create_table(self.client)
        MyModelB2().create_table(self.client)
        session = self.client.create_session()

        self.assertEqual(MyModelB.get_max_id(session), 0)
        self.assertEqual(MyModelB2.get_max_id(session), 0)

        # create some objects of the parent class
        session.add(MyModelB(my_other_field=17))
        session.add(MyModelB(my_other_field=18))
        session.add(MyModelB(my_other_field=19))
        session.commit()

        # for both objects the max id is now 3
        self.assertEqual(MyModelB.get_max_id(session), 3)
        self.assertEqual(MyModelB2.get_max_id(session), 3)

        # create some objects of the derived class
        session.add(MyModelB2(yet_another_field=17))
        session.add(MyModelB2(yet_another_field=18))
        session.add(MyModelB2(yet_another_field=19))
        session.commit()

        # for both objects the max id is now 6
        self.assertEqual(MyModelB.get_max_id(session), 6)
        self.assertEqual(MyModelB2.get_max_id(session), 6)

        # removing first object does not change max id
        session.query(MyModelB).filter(MyModelB.id == 1).delete()
        self.assertEqual(session.query(MyModelB).count(), 5)
        self.assertEqual(MyModelB.get_max_id(session), 6)
        self.assertEqual(MyModelB2.get_max_id(session), 6)

        # removing the base class objects removes derived objects by cascading
        session.query(MyModelB).delete()
        self.assertEqual(session.query(MyModelB).count(), 0)
        self.assertEqual(session.query(MyModelB2).count(), 0)
        self.assertEqual(MyModelB.get_max_id(session), 0)
        self.assertEqual(MyModelB2.get_max_id(session), 0)

        session.close()

    def test07(self):
        """Test truncation of string values to field length
        """
        MyModelValidation().create_table(self.client)
        session = self.client.create_session()

        # short enough string values, OK
        session.add(MyModelValidation(my_validated_string="1234567890",
                                      my_unvalidated_string="1234567890"))
        session.commit()

        # too long value in validated string
        session.add(MyModelValidation(my_validated_string="1234567890A",
                                      my_unvalidated_string="0987654321"))
        session.commit()

        obj = session.query(MyModelValidation).filter(MyModelValidation.my_unvalidated_string == "0987654321").one()
        self.assertEquals(obj.my_validated_string, "1234567890")

        # too long value in unvalidated string - does not fail in test SQLite DB, but value is not truncated
        session.add(MyModelValidation(my_validated_string="09876543210",
                                      my_unvalidated_string="1234567890A"))
        session.commit()

        obj = session.query(MyModelValidation).filter(MyModelValidation.my_validated_string == "0987654321").one()
        self.assertEquals(obj.my_unvalidated_string, "1234567890A")

        session.close()

    def test08(self):
        """Test creating and dropping all tables at once
        """
        # get current DB state
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())

        # there should be no tables yet
        self.assertEqual(len(metadata.tables), 0)

        # create all tables for all registered models
        base.Base.create_all(self.client)

        # now there are at least 5 tables (don't test equality, don't want to break the test
        # each time we add a new test model)
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        self.assertGreaterEqual(len(metadata.tables), 5)

        # test some table names
        self.assertIn('mymodela', list(metadata.tables.keys()))
        self.assertIn('mymodelb', list(metadata.tables.keys()))
        self.assertIn('mymodelb2', list(metadata.tables.keys()))

        # drop all tables
        base.Base.drop_all(self.client)
        metadata = sa.MetaData()
        metadata.reflect(self.client.get_engine())
        self.assertEqual(len(metadata.tables), 0)

    def test10(self):
        """Test class registry
        """
        # class registry might have accumulated tasks from other tests
        self.assertGreaterEqual(len(base.model_registry), 6)
        for c in ['MyModelA', 'MyModelB', 'MyModelB2', 'MyModelC',
                  'MyModelValidation']:
            self.assertIn(c, list(base.model_registry.keys()))

    def test11a(self):
        """Test generation of .dot file for diagram and graceful failure if DOT_EXECUTABLE is not configured
        """
        out_base = "_test_diagram"

        # un-set DOT_EXECUTABLE in config
        if hasattr(config, 'DOT_EXECUTABLE'):
            del config.DOT_EXECUTABLE

        # rendering diagram raises a runtime error
        self.assertRaises(RuntimeError, base.render_diagram, out_base)

        # dot file was still generated
        self.assertTrue(os.path.exists(out_base + '.dot'))

        # clean up
        os.remove(out_base + '.dot')

    def test11b(self):
        """Test generation of .dot file for diagram and graceful failure if DOT_EXECUTABLE is configured wrong
        """
        out_base = "_test_diagram"

        # set wrong DOT_EXECUTABLE in config
        config.DOT_EXECUTABLE = "lala.la"

        # rendering diagram raises a runtime error
        self.assertRaises(IOError, base.render_diagram, out_base)

        # dot file was still generated
        self.assertTrue(os.path.exists(out_base + '.dot'))

        # clean up
        os.remove(out_base + '.dot')
