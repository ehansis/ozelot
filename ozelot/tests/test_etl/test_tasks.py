"""Unit tests for task base classes
"""
from builtins import next

from os import path
import unittest
import datetime

import sqlalchemy as sa
from sqlalchemy.orm import relationship
import pandas as pd
import luigi

from ozelot.orm.target import ORMTargetMarker
from ozelot.etl.tasks import ORMTask, ORMObjectCreatorMixin, ORMWrapperTask, TaskBase, InputFileTask, \
    get_task_name, get_task_param_string, check_completion, ORMTestTask
from ozelot import client
from ozelot.tests import common
from ozelot.orm import base


# noinspection PyAbstractClass
class TaskA(ORMTask):
    """A task without parameters
    """

    def run(self):
        pass


# noinspection PyAbstractClass
class TaskB(ORMTask):
    """A task with parameters
    """

    p1 = luigi.IntParameter()
    p2 = luigi.Parameter()

    def run(self):
        pass


# noinspection PyAbstractClass
class TaskC(ORMTask):
    """Another task without parameters
    """

    def run(self):
        pass


class TaskWrapper(ORMWrapperTask):
    """A wrapper task
    """

    def requires(self):
        yield TaskA()
        yield TaskB(p1=1, p2="a")


class InputA(InputFileTask):
    """A task representing an input file
    """
    input_file = path.join(common.get_fixtures_path(), 'test_01.csv')

    def load(self):
        return pd.read_csv(self.input_file)


# noinspection PyAbstractClass
class InputNotExists(InputFileTask):
    """A task representing an input file that does not exist, with no load method
    """
    input_file = path.join(common.get_fixtures_path(), 'really_not_there.im_sure')


# noinspection PyAbstractClass
class InputBad(InputFileTask):
    """An input file task with no input file defined
    """
    pass


class MyCreatedModel(base.Base):
    my_field = sa.Column(sa.Integer())


class CreatorTaskA(ORMObjectCreatorMixin, ORMTask):
    """A task creating a certain object class
    """
    object_classes = [MyCreatedModel]

    def run(self):
        s = client.get_client().create_session()
        s.add(MyCreatedModel(my_field=1))
        s.add(MyCreatedModel(my_field=2))
        s.add(MyCreatedModel(my_field=3))
        s.commit()


# noinspection PyAbstractClass
class TaskBaseA(TaskBase):
    def run(self):
        pass


class LuigiTask(luigi.Task):
    a = luigi.Parameter()
    b = luigi.IntParameter()


class TestModuleFunctions(unittest.TestCase):
    """Test various module-level functions
    """

    def test01(self):
        """Test task name getting
        """
        self.assertEqual(get_task_name(LuigiTask(a='a', b=3)), 'LuigiTask')

    def test02(self):
        """Test param string getting
        """
        self.assertEqual(get_task_param_string(LuigiTask(a='a', b=3)),
                         "{'a': 'a', 'b': '3'}")


class TestORMTask(unittest.TestCase):
    """Unit tests for :class:`ORMTask`
    """

    def setUp(self):
        common.remove_test_db_file()
        client.set_client(common.get_test_db_client())
        ORMTargetMarker().create_table(client.get_client())

    def tearDown(self):
        common.remove_test_db_file()

    def test01(self):
        """Mark a task as complete and then as incomplete
        """
        session = client.get_client().create_session()

        task = TaskB(p1=17, p2="lala")
        self.assertFalse(task.complete())

        task.mark_complete()
        self.assertTrue(task.complete())
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)

        obj = session.query(ORMTargetMarker).first()
        self.assertEqual(obj.name, 'TaskB')
        self.assertEqual(obj.params, "{'p1': '17', 'p2': 'lala'}")
        self.assertLess((obj.created - datetime.datetime.now()).total_seconds(), 3)

        task.mark_incomplete()
        self.assertFalse(task.complete())
        self.assertEqual(session.query(ORMTargetMarker).count(), 0)

        session.close()

    def test02(self):
        """Marking a task as completed twice does nothing
        """
        session = client.get_client().create_session()

        task = TaskB(p1=17, p2="lala")
        task.mark_complete()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)
        obj = session.query(ORMTargetMarker).first()

        task.mark_complete()
        self.assertEqual(session.query(ORMTargetMarker).count(), 1)
        obj2 = session.query(ORMTargetMarker).first()
        self.assertEqual(obj.created, obj2.created)

        session.close()

    def test03(self):
        """Marking an incomplete task as incomplete does nothing
        """
        session = client.get_client().create_session()

        task = TaskB(p1=17, p2="lala")
        self.assertEqual(session.query(ORMTargetMarker).count(), 0)
        task.mark_incomplete()
        self.assertEqual(session.query(ORMTargetMarker).count(), 0)

        session.close()

    def test04(self):
        """Calling 'clear' without implementing it raises an error
        """
        self.assertRaises(NotImplementedError, TaskA().clear)
        self.assertRaises(NotImplementedError, TaskBaseA().clear)

    def test05(self):
        """Test client property: None initially, then just one instance
        """
        task = TaskA()
        self.assertIsNone(task._client)
        cl = task.client
        self.assertIsNotNone(task._client)
        cl2 = task.client
        self.assertIs(cl, cl2)

    def test06(self):
        """Test session property: None initially, then just one instance
        """
        task = TaskA()
        self.assertIsNone(task._session)
        sess = task.session
        self.assertIsNotNone(task._session)
        sess2 = task.session
        self.assertIs(sess, sess2)
        task.mark_complete()
        m = task.session.query(ORMTargetMarker).one()
        self.assertEqual(m.name, 'TaskA')

    def test07(self):
        """Test closing of session property
        """
        task = TaskA()
        sess = task.session
        task.close_session()
        self.assertIsNone(task._session)
        sess2 = task.session
        self.assertIsNot(sess, sess2)

    def test08(self):
        """Test :func:`done`: session is committed and closed, task is complete
        """
        task = TaskA()
        sess = task.session
        sess.add(ORMTargetMarker(name='lala'))
        task.done()
        self.assertIsNone(task._session)
        self.assertTrue(task.complete())
        task.session.query(ORMTargetMarker).filter(ORMTargetMarker.name == 'lala').one()
        self.assertEqual(task.session.query(ORMTargetMarker).count(), 2)

    def test08b(self):
        """Test :func:`done`: session is NOT committed and closed, task is complete
        """
        task = TaskA()
        sess = task.session
        # this object is not being committed
        sess.add(ORMTargetMarker(name='lala'))
        task.done(commit=False)
        self.assertIsNone(task._session)
        self.assertTrue(task.complete())
        self.assertEqual(task.session.query(ORMTargetMarker).count(), 1)


class TestORMObjectCreatorMixin(unittest.TestCase):
    """Unit tests for mixin :class:`ORMObjectCreator`
    """

    def setUp(self):
        common.remove_test_db_file()
        client.set_client(common.get_test_db_client())
        ORMTargetMarker().create_table(client.get_client())
        MyCreatedModel().create_table(client.get_client())

    def tearDown(self):
        common.remove_test_db_file()

    def test01(self):
        """Run a task, then clear it
        """
        session = client.get_client().create_session()

        self.assertEqual(session.query(MyCreatedModel).count(), 0)
        self.assertFalse(CreatorTaskA().complete())

        luigi.build([CreatorTaskA()], local_scheduler=True)
        self.assertEqual(session.query(MyCreatedModel).count(), 3)
        self.assertFalse(CreatorTaskA().complete())

        CreatorTaskA().clear()
        self.assertEqual(session.query(MyCreatedModel).count(), 0)
        self.assertFalse(CreatorTaskA().complete())

        session.close()


class TestORMWrapperTask(unittest.TestCase):
    """Unit tests for :class:`ORMWrapperTask`
    """

    def setUp(self):
        common.remove_test_db_file()
        client.set_client(common.get_test_db_client())
        ORMTargetMarker().create_table(client.get_client())

    def tearDown(self):
        common.remove_test_db_file()

    def test01(self):
        """Test completion of a wrapper task
        """
        wrapper_task = TaskWrapper()
        task1 = TaskA()
        task2 = TaskB(p1=1, p2="a")

        self.assertFalse(wrapper_task.complete())

        task1.mark_complete()
        task2.mark_complete()

        wrapper_task.run()
        self.assertTrue(wrapper_task.complete())

        wrapper_task.clear()
        self.assertFalse(wrapper_task.complete())

    def test02(self):
        """Wrapper task is only complete if all requirements are complete
        """
        wrapper_task = TaskWrapper()
        task1 = TaskA()
        task2 = TaskB(p1=1, p2="a")

        task1.mark_complete()
        task2.mark_complete()
        wrapper_task.run()
        self.assertTrue(wrapper_task.complete())

        task1.mark_incomplete()
        self.assertFalse(wrapper_task.complete())


class TestInputFileTask(unittest.TestCase):
    """Unit tests for :class:`InputFileTask`
    """

    def test01(self):
        """Existence and loading of a regular, existing input file
        """
        task = InputA()
        self.assertTrue(task.complete())

        df = task.load()
        self.assertEqual(len(df), 3)
        self.assertEqual(len(df.columns), 3)

        # clearing does nothing
        task.clear()
        self.assertTrue(task.complete())

        # running does nothing
        task.run()
        self.assertTrue(task.complete())

    def test02(self):
        """Input file task for a file that does not exist
        """
        task = InputNotExists()
        self.assertFalse(task.complete())

        # load method not implemented
        self.assertRaises(NotImplementedError, task.load)

    def test03(self):
        """Input file task with no input file specified, raises errors
        """
        task = InputBad()
        self.assertRaises(RuntimeError, task.output)


class TestTaskA(ORMTestTask):

    def run(self):
        pass


class TestORMTestTask(unittest.TestCase):

    def setUp(self):
        common.remove_test_db_file()
        client.set_client(common.get_test_db_client())
        ORMTargetMarker().create_table(client.get_client())

    def test01(self):
        """Test :func:`done`: session is NOT committed by default
        """
        task = TestTaskA()
        sess = task.session
        # this object is not being committed
        sess.add(ORMTargetMarker(name='lala'))
        task.done()
        self.assertIsNone(task._session)
        self.assertTrue(task.complete())
        self.assertEqual(task.session.query(ORMTargetMarker).count(), 1)


#
# task tree for task completion checking
#

class MyStringModel(base.Base):
    name = sa.Column(sa.String())
    params = sa.Column(sa.String())


class ModelWithForeignKey(base.Base):
    rel_id = sa.Column(sa.Integer, sa.ForeignKey(MyStringModel.id))
    rel = relationship(MyStringModel, backref="parent")


# base with a run method
class TreeTaskBase(ORMTask):
    def clear(self):
        s = client.get_client().create_session()
        s.query(MyStringModel) \
            .filter(MyStringModel.name == self.get_name()) \
            .filter(MyStringModel.params == self.get_param_string()) \
            .delete()
        s.commit()
        s.close()
        self.mark_incomplete()

    def run(self):
        s = client.get_client().create_session()
        s.add(MyStringModel(name=self.get_name(),
                            params=self.get_param_string()))
        s.commit()
        s.close()
        self.mark_complete()


# This is a task that creates a foreign key reference to an object created by one of its
# requirements. If tasks are cleared in the naive order (bottom up), this fails, because
# the requirement has to be cleared AFTER this task. Top-down clearing works.
class TreeTaskAll(ORMWrapperTask):
    def requires(self):
        yield TreeTask1A(param='a')
        yield TreeTask1A(param='b')
        yield TreeTask1B()

    def clear(self):
        s = client.get_client().create_session()
        s.query(ModelWithForeignKey).delete()
        s.commit()
        s.close()

        super(TreeTaskAll, self).clear()

    def run(self):
        s = client.get_client().create_session()

        rel_obj = s.query(MyStringModel).filter(MyStringModel.name == 'TreeTask1B').one()
        s.add(ModelWithForeignKey(rel_id=rel_obj.id))
        s.commit()
        s.close()

        super(TreeTaskAll, self).run()


class TreeTask1A(TreeTaskBase):
    param = luigi.Parameter()
    pass


class TreeTask1B(TreeTaskBase):
    def requires(self):
        yield TreeTask2A()
        yield TreeTask2B()
        # a requirement repeated from TreeTaskAll, does not increment stats
        yield TreeTask1A(param='a')


class TreeTask2A(TreeTaskBase):
    pass


class TreeTask2B(luigi.Task):
    def requires(self):
        yield TreeTask3A()

    def complete(self):
        return next(self.requires()).complete()


class TreeTask3A(TreeTaskBase):
    pass


class TestTaskCheckCompletion(unittest.TestCase):
    """Unit tests for recursive task completion checking
    """

    def setUp(self):
        common.remove_test_db_file()
        client.set_client(common.get_test_db_client())
        ORMTargetMarker().create_table(client.get_client())
        MyStringModel().create_table(client.get_client())
        ModelWithForeignKey().create_table(client.get_client())
        self.session = client.get_client().create_session()

    def tearDown(self):
        self.session.close()
        common.remove_test_db_file()

    def test01(self):
        """Check completion on top-level task after building the full pipeline
        """
        self.assertFalse(check_completion(TreeTaskAll()))
        luigi.build([TreeTaskAll()], local_scheduler=True)

        # without stats
        self.assertTrue(check_completion(TreeTaskAll()))

        # with stats
        is_complete, stats = check_completion(TreeTaskAll(), return_stats=True)
        self.assertTrue(is_complete)
        # complete (and tracked): TreeTaskAll, TreeTask1A a + b, TreeTask1B, TreeTask2A, TreeTask2B, TreeTask3A
        self.assertEqual(stats, {'Complete tasks': 7})

    def test02(self):
        """Build full pipeline, clear one downstream task, check again on top-level task
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        self.assertTrue(check_completion(TreeTaskAll()))
        TreeTask2A().clear()
        self.assertFalse(check_completion(TreeTaskAll()))

        # with stats
        is_complete, stats = check_completion(TreeTaskAll(), return_stats=True)
        self.assertFalse(is_complete)
        # incomplete: TreeTaskAll, TreeTask1B, TreeTask2A
        # complete: TreeTask1A a + b, TreeTask2B, TreeTask3A
        self.assertEqual(stats, {'Complete tasks': 4, 'Incomplete tasks': 3})

    def test03(self):
        """Check completion on down-stream tasks after building the full pipeline
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)

        is_complete, stats = check_completion(TreeTask1A(param='a'), return_stats=True)
        self.assertTrue(is_complete)
        # task depends on nothing
        self.assertEqual(stats, {'Complete tasks': 1})

        is_complete, stats = check_completion(TreeTask1B(), return_stats=True)
        self.assertTrue(is_complete)
        # complete + dependencies: TreeTask1B, TreeTask2A, TreeTask1A a, TreeTask2B, TreeTask3A
        self.assertEqual(stats, {'Complete tasks': 5})

    def test04(self):
        """Build full pipeline, clear one downstream task, check on downstream tasks
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        TreeTask2A().clear()

        # task depends on nothing, is still complete
        is_complete, stats = check_completion(TreeTask1A(param='a'), return_stats=True)
        self.assertTrue(is_complete)
        self.assertEqual(stats, {'Complete tasks': 1})

        is_complete, stats = check_completion(TreeTask1B(), return_stats=True)
        self.assertFalse(is_complete)
        # incomplete: TreeTask1B, TreeTask2A
        # complete: TreeTask1A a, TreeTask2B, TreeTask3A
        self.assertEqual(stats, {'Complete tasks': 3, 'Incomplete tasks': 2})

    def test05(self):
        """Complete pipeline, marking as incomplete or clearing does nothing
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        # target markers for: TreeTaskAll, TreeTask1A a + b, TreeTask1B, TreeTask2A, TreeTask3A
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 6)
        # run()-generated models from TreeTask1A a + b, TreeTask1B, TreeTask2A
        query = self.session.query(MyStringModel)
        self.assertEqual(query.count(), 5)
        task_ids = [t.name + " " + t.params for t in query.all()]
        self.assertIn("TreeTask2A {}", task_ids)
        self.assertIn("TreeTask1B {}", task_ids)
        self.assertIn("TreeTask1A {'param': 'a'}", task_ids)
        self.assertIn("TreeTask1A {'param': 'b'}", task_ids)
        self.assertIn("TreeTask3A {}", task_ids)

        is_complete = check_completion(TreeTaskAll(), mark_incomplete=True)
        self.assertTrue(is_complete)
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 6)
        self.assertEqual(self.session.query(MyStringModel).count(), 5)

        is_complete = check_completion(TreeTaskAll(), clear=True)
        self.assertTrue(is_complete)
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 6)
        self.assertEqual(self.session.query(MyStringModel).count(), 5)

    def test06A(self):
        """Build full pipeline, clear one downstream task, check and mark incomplete on top-level task
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        TreeTask1A(param='a').clear()
        # one completion marker and one run()-generated object missing
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 5)
        self.assertEqual(self.session.query(MyStringModel).count(), 4)

        is_complete = check_completion(TreeTaskAll(), mark_incomplete=True)
        self.assertFalse(is_complete)
        # Task2A and Task1A b remain complete
        query = self.session.query(ORMTargetMarker)
        self.assertEqual(query.count(), 3)
        task_ids = [t.name + " " + t.params for t in query.all()]
        self.assertIn("TreeTask2A {}", task_ids)
        self.assertIn("TreeTask1A {'param': 'b'}", task_ids)
        # all run()-generated objects remain
        self.assertEqual(self.session.query(MyStringModel).count(), 4)

    def test06B(self):
        """Build full pipeline, clear one downstream task, check and mark incomplete on top-level task
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        TreeTask1A(param='a').clear()
        # one completion marker and one run()-generated object missing
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 5)
        self.assertEqual(self.session.query(MyStringModel).count(), 4)

        is_complete = check_completion(TreeTaskAll(), clear=True)
        self.assertFalse(is_complete)
        # Task2A and Task1A b remain complete, MyStringModel from Task1B was cleared
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 3)
        query = self.session.query(MyStringModel)
        self.assertEqual(query.count(), 3)
        obj_ids = [t.name + " " + t.params for t in query.all()]
        self.assertIn("TreeTask2A {}", obj_ids)
        self.assertIn("TreeTask1A {'param': 'b'}", obj_ids)
        self.assertIn("TreeTask3A {}", obj_ids)

    def test07A(self):
        """Build full pipeline, clear one downstream task, check and mark incomplete on downstream tasks
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        TreeTask2A().clear()

        # this task doesn't depend on anything, clearing changes nothing
        is_complete = check_completion(TreeTask1A(param='a'), mark_incomplete=True)
        self.assertTrue(is_complete)
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 5)
        self.assertEqual(self.session.query(MyStringModel).count(), 4)

        # Task1B is marked incomplete in addition, Task1A a + b and AllTasks remain
        is_complete = check_completion(TreeTask1B(), mark_incomplete=True)
        self.assertFalse(is_complete)
        query = self.session.query(ORMTargetMarker)
        self.assertEqual(query.count(), 4)
        task_ids = [t.name + " " + t.params for t in query.all()]
        self.assertIn("TreeTaskAll {}", task_ids)
        self.assertIn("TreeTask1A {'param': 'a'}", task_ids)
        self.assertIn("TreeTask1A {'param': 'b'}", task_ids)
        self.assertIn("TreeTask3A {}", task_ids)
        self.assertEqual(self.session.query(MyStringModel).count(), 4)

    def test07B(self):
        """Build full pipeline, clear one downstream task, check and clear on downstream tasks
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        TreeTask2A().clear()

        # this task doesn't depend on anything, clearing changes nothing
        is_complete = check_completion(TreeTask1A(param='a'), clear=True)
        self.assertTrue(is_complete)
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 5)
        self.assertEqual(self.session.query(MyStringModel).count(), 4)

        # Task1B is cleared in addition, Task1A a + b objects remain; to be able to do that without
        # violating foreign key constraints, the model instance with foreign key has to be removed first
        self.session.query(ModelWithForeignKey).delete()
        self.session.commit()
        is_complete = check_completion(TreeTask1B(), clear=True)
        self.assertFalse(is_complete)
        self.assertEqual(self.session.query(ORMTargetMarker).count(), 4)
        query = self.session.query(MyStringModel)
        self.assertEqual(query.count(), 3)
        obj_ids = [t.name + " " + t.params for t in query.all()]
        self.assertIn("TreeTask1A {'param': 'a'}", obj_ids)
        self.assertIn("TreeTask1A {'param': 'b'}", obj_ids)
        self.assertIn("TreeTask3A {}", obj_ids)

    def test08a(self):
        """Trying to mark incomplete a luigi.Task causes no error (but its incomplete requirement is detected)
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        is_complete = check_completion(TreeTaskAll(), mark_incomplete=False)
        self.assertTrue(is_complete)
        TreeTask3A().clear()
        is_complete = check_completion(TreeTaskAll(), mark_incomplete=False)
        self.assertFalse(is_complete)
        is_complete = check_completion(TreeTaskAll(), mark_incomplete=True)
        self.assertFalse(is_complete)
        is_complete = check_completion(TreeTask2B(), mark_incomplete=True)
        self.assertFalse(is_complete)

    def test08b(self):
        """Trying to clear a luigi.Task causes no error (but its incomplete requirement is detected)
        """
        luigi.build([TreeTaskAll()], local_scheduler=True)
        TreeTask3A().clear()
        is_complete = check_completion(TreeTaskAll(), clear=True)
        self.assertFalse(is_complete)
        is_complete = check_completion(TreeTask2B(), clear=True)
        self.assertFalse(is_complete)
