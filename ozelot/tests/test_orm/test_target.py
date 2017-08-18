"""Unit tests for pipeline target classes.
"""
from builtins import next
from builtins import str

import unittest
import datetime

import luigi

from ozelot.orm.target import ORMTargetMarker
from ozelot.etl.tasks import ORMTask
from ozelot.etl.targets import ORMTarget
from ozelot import client
from ozelot.tests import common


class TaskA(ORMTask):
    """A task without parameters
    """

    def clear(self):
        pass

    def run(self):
        pass


class TaskB(ORMTask):
    """A task with parameters
    """

    p1 = luigi.IntParameter()
    p2 = luigi.Parameter()

    def clear(self):
        pass

    def run(self):
        pass


class TaskC(ORMTask):
    """Another task without parameters
    """

    def clear(self):
        pass

    def run(self):
        pass


class TestORMTarget(unittest.TestCase):
    """Unit tests for ORM targets
    """

    def setUp(self):
        common.remove_test_db_file()
        client.set_client(common.get_test_db_client())
        ORMTargetMarker().create_table(client.get_client())

    def tearDown(self):
        common.remove_test_db_file()

    def test01(self):
        """Create a target from a task without parameters
        """
        task = TaskA()
        target = ORMTarget.from_task(task)
        self.assertEqual(target.name, 'TaskA')
        self.assertEqual(target.params, "{}")

    def test02(self):
        """Create a target from a task with parameters
        """
        task = TaskB(p1=17, p2="lala")
        target = ORMTarget.from_task(task)
        self.assertEqual(target.name, 'TaskB')
        self.assertEqual(target.params, "{'p1': '17', 'p2': 'lala'}")

    def test03(self):
        """Mark a target as complete and check its existence, then remove it
        """
        session = client.get_client().create_session()

        task = TaskB(p1=17, p2="lala")
        target = ORMTarget.from_task(task)
        self.assertFalse(target.exists())
        self.assertEqual(session.query(ORMTargetMarker).count(), 0)

        target.create()
        self.assertTrue(target.exists())
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)

        obj = session.query(ORMTargetMarker).first()
        self.assertEqual(obj.name, target.name)
        self.assertEqual(obj.params, target.params)
        self.assertLess((obj.created - datetime.datetime.now()).total_seconds(), 3)

        target.remove()
        self.assertFalse(target.exists())
        self.assertEqual(session.query(ORMTargetMarker).count(), 0)

        session.close()

    def test04(self):
        """Creating a target twice does nothing
        """
        session = client.get_client().create_session()

        task = TaskB(p1=17, p2="lala")
        target = ORMTarget.from_task(task)
        target.create()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)
        obj = session.query(ORMTargetMarker).first()

        # create target again, does nothing
        target.create()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)
        obj2 = session.query(ORMTargetMarker).first()
        self.assertEqual(obj.created, obj2.created)

        session.close()

    def test05(self):
        """Removing a non-existing target raises an error
        """
        task = TaskB(p1=17, p2="lala")
        target = ORMTarget.from_task(task)
        self.assertRaises(RuntimeError, target.remove)

    def test06(self):
        """Targets for the same task but with different parameters are handled as different targets
        """
        session = client.get_client().create_session()

        task = TaskB(p1=17, p2="lala")
        ORMTarget.from_task(task).create()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)

        task = TaskB(p1=18, p2="lala")
        ORMTarget.from_task(task).create()
        self.assertEqual(session.query(ORMTargetMarker).count(), 2)

        # remove target for the first task
        task = TaskB(p1=17, p2="lala")
        ORMTarget.from_task(task).remove()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)

        obj = session.query(ORMTargetMarker).first()
        self.assertEqual(obj.params, "{'p1': '18', 'p2': 'lala'}")

        session.close()

    def test07(self):
        """Targets for differnt tasks but with the same parameters are handled as different targets
        """
        session = client.get_client().create_session()

        task = TaskA()
        ORMTarget.from_task(task).create()

        task = TaskC()
        ORMTarget.from_task(task).create()

        self.assertEqual(session.query(ORMTargetMarker).count(), 2)

        # remove target for the first task
        task = TaskA()
        ORMTarget.from_task(task).remove()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)

        obj = session.query(ORMTargetMarker).first()
        self.assertEqual(obj.name, 'TaskC')

        session.close()

    def test08(self):
        """Check unicode representation of target markers
        """
        tgt = next(TaskA().output())
        marker = ORMTargetMarker(name=tgt.name, params=tgt.params)
        self.assertEqual(str(marker), "TaskA {} None")

        tgt = next(TaskB(p1=5, p2='lala').output())
        marker = ORMTargetMarker(name=tgt.name, params=tgt.params)
        self.assertEqual(str(marker), "TaskB {'p1': '5', 'p2': 'lala'} None")
