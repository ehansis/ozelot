# coding=utf-8
"""Unit tests for ETL utilities
"""

import os
import unittest

import luigi

from ozelot.etl.tasks import ORMTask
from ozelot import config
from ozelot.etl import util


# noinspection PyAbstractClass
class TaskA(ORMTask):
    def requires(self):
        yield TaskB(p1=1, p2='la')
        yield TaskC()

    def run(self):
        pass

    def complete(self):
        return False


# noinspection PyAbstractClass
class TaskB(ORMTask):
    p1 = luigi.IntParameter()
    p2 = luigi.Parameter()

    def run(self):
        pass

    def complete(self):
        return False


# noinspection PyAbstractClass
class TaskC(luigi.Task):
    def requires(self):
        yield TaskD(p3=42)

    def run(self):
        pass

    def complete(self):
        return False


# noinspection PyAbstractClass
class TaskD(luigi.Task):
    p3 = luigi.IntParameter()

    def run(self):
        pass

    def complete(self):
        return False


class TestFlowchart(unittest.TestCase):

    def test01a(self):
        """Test generation of .dot file for diagram and graceful failure if DOT_EXECUTABLE is not configured
        """
        out_base = "_test_diagram"

        # un-set DOT_EXECUTABLE in config
        if hasattr(config, 'DOT_EXECUTABLE'):
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
        self.assertIn("TaskD", dot)
        self.assertIn("p3", dot)
        self.assertNotIn("red", dot)

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

    def test01c(self):
        """Test generation of colored .dot file
        """
        out_base = "_test_diagram"

        # un-set DOT_EXECUTABLE in config
        if hasattr(config, 'DOT_EXECUTABLE'):
            del config.DOT_EXECUTABLE

        # rendering diagram raises a runtime error
        self.assertRaises(RuntimeError, util.render_diagram, TaskA(), out_base, colored=True)

        with open(out_base + '.dot') as f:
            dot = f.read()

        self.assertIn("red", dot)
        self.assertNotIn("green", dot)

        # clean up
        os.remove(out_base + '.dot')


class TestStringSanitizing(unittest.TestCase):

    def test01(self):
        """A very benign string"""
        s = util.sanitize(u"aaa bbb ccc")
        self.assertEquals(s, u"aaa bbb ccc")

    def test02a(self):
        """Strip whitespace"""
        s = util.sanitize(u"\t\t too \n   much  \r\n  whitespace!   ")
        self.assertEquals(s, u"too much whitespace!")

    def test02b(self):
        """Don't strip whitespace"""
        s = util.sanitize(u"\t\t too \n   much  \r\n  whitespace!   ", normalize_whitespace=False)
        self.assertEquals(s, u"\t\t too \n   much  \r\n  whitespace!   ")

    def test03a(self):
        """Normalize unicode representation"""
        # decomposed C with cedilla and roman numeral I
        s = util.sanitize(u"\u0043\u0327\u2160")
        # C with cedilla and capital I
        self.assertEquals(s, u"\u00C7I")

    def test03b(self):
        """Don't normalize unicode representation"""
        # C with cedilla and roman numeral I
        s = util.sanitize(u"\u00C7\u2160", normalize_unicode=False)
        # same as before
        self.assertEquals(s, u"\u00C7\u2160")

    def test03c(self):
        """Normalize to different unicode representation"""
        # decomposed C with cedilla
        s = util.sanitize(u"\u00C7", form='NFKD')
        # C with cedilla and capital I
        self.assertEquals(s, u"\u0043\u0327")

    def test04a(self):
        """Normalize encoding"""
        s = util.sanitize(u"Hör auf!", encoding='ascii')
        self.assertEquals(s, u"Hr auf!")

    def test04b(self):
        """Don't normalize encoding"""
        s = util.sanitize(u"Hör auf!", encoding='ascii', enforce_encoding=False)
        self.assertEquals(s, u"Hör auf!")
