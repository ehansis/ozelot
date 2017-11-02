"""Unit tests for task base classes
"""

import os
import unittest

import luigi

from ozelot.etl.tasks import ORMTask
from ozelot.orm import base
from ozelot import config
from ozelot.etl import util


# noinspection PyAbstractClass
class TaskA(ORMTask):
    def requires(self):
        yield TaskB(p1=1, p2='la')
        yield TaskC()

    def run(self):
        pass


# noinspection PyAbstractClass
class TaskB(ORMTask):
    p1 = luigi.IntParameter()
    p2 = luigi.Parameter()

    def run(self):
        pass


# noinspection PyAbstractClass
class TaskC(ORMTask):
    def run(self):
        pass


class TestFlowchart(unittest.TestCase):
    def test01a(self):
        """Test generation of .dot file for diagram and graceful failure if DOT_EXECUTABLE is not configured
        """
        out_base = "_test_diagram"

        # un-set DOT_EXECUTABLE in config
        del config.DOT_EXECUTABLE

        # rendering diagram raises a runtime error
        self.assertRaises(RuntimeError, util.render_diagram, TaskA(), out_base)

        # dot file was still generated
        self.assertTrue(os.path.exists(out_base + '.dot'))

        # very simple checks on dot contents
        with open(out_base + '.dot') as f:
            dot = f.read()

        self.assertIn("TaskA", dot)
        self.assertIn("TaskB", dot)
        self.assertIn("p1", dot)
        self.assertIn("p2", dot)
        self.assertIn("TaskC", dot)

        # clean up
        os.remove(out_base + '.dot')

    def test01b(self):
        """Test generation of .dot file for diagram and graceful failure if DOT_EXECUTABLE is configured wrong
        """
        out_base = "_test_diagram"

        # set wrong DOT_EXECUTABLE in config
        config.DOT_EXECUTABLE = "lala.la"

        # rendering diagram raises a runtime error
        self.assertRaises(IOError, util.render_diagram, TaskA(), out_base)

        # dot file was still generated
        self.assertTrue(os.path.exists(out_base + '.dot'))

        # clean up
        os.remove(out_base + '.dot')
