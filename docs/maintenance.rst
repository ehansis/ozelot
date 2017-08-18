Maintenance
***********


Testing
=======

Unit tests are contained in :mod:`ozelot.tests`.
Here is a `code coverage report <_static/cover/index.html>`_.
See :ref:`below <test-coverage>` for how to generate the report.


Configuration
-------------

Tests that need a database to run use an SQLite (file-based) database.
By default, the database is created in the directory containing :mod:`ozelot.tests`, as ``testing.db`` and
removed upon completion of a test. The database location can be overwritten by specifying
a different location as ``TESTING_SQLITE_DB_PATH`` in :mod:`ozelot.config`.


Running tests
-------------

Tests can be run by

.. code-block:: none

    python setup.py test

This will run all unit tests using :mod:`nose` as test runner. Alternatively, you can run selected tests
using :mod:`nose`. For example, running a single test function :func:`test01` from class :class:`BaseTest`
in module :mod:`ozelot.tests.test_models.test_base` can be achieved with

.. code-block:: none

    nosetests ozelot.tests.test_models.test_base:BaseTest.test01


.. _test-coverage:

Code coverage report
--------------------

This requires packages ``nose`` and ``coverage``.
Run the following command in the ``ozelot`` package directory (the one containing, e.g., ``config.py``):

.. code-block:: none

    nosetests --with-coverage --cover-erase --cover-html --cover-package=ozelot --cover-html-dir=<output directory>

This builds a `pretty html coverage report <_static/cover/index.html>`_.


Documentation
=============


Requirements
------------

Building the documentation requires :mod:`sphinx` and :mod:`sphinxcontrib-napoleon`, as well as
:mod:`sphinx_rtd_theme`.
You can install these packages by using the ``requirements.txt`` file in the documentation root folder
(make sure you have activated your virtual environment, if you are using one):

.. code-block:: none

    pip install -r requirements.txt


Source code links
-----------------

The documentation includes code snippets from :mod:`ozelot` and the examples, as well as a full API documentation.
To this end, the code must be available when building the documentation.
The contents of the `ozelot-src repository <https://github.com/ehansis/ozelot-src>`_ are
expected to be available in a directory ``ozelot-src`` in the documentation root (i.e. next to ``conf.py``).
The contents of the `ozelot-examples repository <https://github.com/ehansis/ozelot-examples>`_ are
expected a directory ``ozelot-examples`` in the ``examples`` directory of the documentation
(i.e. next to the directory ``superheroes``).

You can either clone these repositories into the expected locations, or you can symlink them
if you already have them cloned somewhere else.



Building the documentation
--------------------------

To generate the documentation, run

.. code-block:: none

    make html

The generated html will be placed in a sub-directory ``build`` of the documentation directory.

When building the API documentation, :mod:`sphinx` needs to import all modules from all source files.
Therefore, all required packages need to be installed to compile the documentation, both for
:mod:`ozelot` and for all examples that are part of the documentation.


Generating the API documentation
--------------------------------

The :mod:`ozelot` API documentation is generated with Sphinx ``autodoc`` and ``sphinx-apidoc`` by running

.. code-block:: none

    sphinx-apidoc -f -o api ozelot-src/ozelot

The file ``modules.rst`` that is part of the output is not needed and can be deleted.

Similarly, API documentation of each example has to be built. Do this in the respective sub-folder containing
the example documentation:

.. code-block:: none

    cd examples/superheroes
    sphinx-apidoc -f -o api ../ozelot-examples/superheroes/superheroes


.. code-block:: none

    cd examples/eurominder
    sphinx-apidoc -f -o api ../ozelot-examples/eurominder/eurominder

