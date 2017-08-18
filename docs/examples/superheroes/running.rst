
Setting up and running the example
==================================


Installation
------------

The code for the example doesn't have to be installed. Just copy the contents of the
``superheroes`` directory from the `example repository <https://github.com/ehansis/ozelot-examples>`_
to a directory of your choice. If you don't need to clone the repository, the easiest way is
to download a current snapshot of the repository
`as zip file <https://github.com/ehansis/ozelot-examples/archive/master.zip>`_.
Note that cloning or downloading may take a while, since the examples contain data (about 20 MB total).

The Python packages required to run this exapmle are listed in the file ``requirements.txt`` inside
the example code directory. Install them by running

.. code-block:: none

    pip install -r requirements.txt

If you are using a virtual environment, make sure to activate it before installing.

Note that the example requires :mod:`matplotlib` and :mod:`scipy`, so a pure ``pip`` installation
may not be possible (or cause severe headaches). See the :mod:`ozelot`
:ref:`installation instructions <ozelot-package-installation>` for how to install these
using conda.


Ready-made conda environments
-----------------------------

If you want to set up a fresh conda environment for trying out this example, there is a handy environment
file included in the repository. To set up a Python 2.7 environment, use the file ``superheroes-environment-2.7.yml``
`located in the example's folder <https://raw.githubusercontent.com/ehansis/ozelot-examples/master/superheroes/superheroes-environment-2.7.yml>`_
and run

.. code-block:: none

    conda env crate -f superheroes-environment-2.7.yml


This will set up a new conda environment called ``ozelot-superheroes-2.7`` including all required packages.
For a Python 3.5 environment, use the file ``superheroes-environment-3.5.yml``
`from the repository root <https://raw.githubusercontent.com/ehansis/ozelot-examples/master/superheroes/superheroes-environment-3.5.yml>`_.

Note that this will not download the example's source code, see above for how to get that.



Configuration
-------------

Project-level configuration is defined in ``project_config.py``. You can leave all settings at the default
values to run the pipeline. Settings you might want to change are the database connection (or location of
the database file), the location of the web request cache file, and the selection of universes to import
(see :ref:`sh-pipeline`).


.. _cached_data:

Retrieving cached data
----------------------

The pipeline runs all web requests through an :class:`ozelot.cache.RequestCache`. This way,
upon re-running the pipeline you have the data already cached on your hard drive, speeding up debugging and testing.
The location of the cache file is defined as ``REQUEST_CACHE_PATH`` in ``project_config.py``. By default, it points to
the file ``superheroes_web_cache.db`` in the project's source directory.

We provide a filled web cache with the example.
To use it, unzip ``superheroes_web_cache.db.zip`` in-place (or wherever you have pointed
the ``REQUEST_CACHE_PATH`` to). This is useful because

    1) it lets you run the pipeline quickly, without waiting for all the data to load,
    2) it avoids unneccesary load on the data providers' servers, and
    3) you can be sure your results are consistent with the pipeline implementations and tests.


.. _running:

Running
-------

The example comes with a small script :file:`manage.py` that can be used to run initiate various operations.

    - Run ``python manage.py initdb`` to (re-)initialize the database and create all tables for the :ref:`sh-datamodel`.
      You need to run this once before launching the ETL pipeline.

      When using an SQLite database, the database file is created in case it does not exist yet.
      For other database backends (e.g. postgresql), the used database has to exist already.

      .. warning:: ``initdb`` deletes all present data in the database.

    - Calling ``python manage.py ingest`` runs the full :ref:`sh-pipeline`. After successful completion,
      all ingested data is present in the database. A filled database from a complete pipeline
      run is also included in the example. To use it, unzip ``superheroes.db.zip`` in-place.

    - Run ``python manage.py analyze`` to generate the analysis output and write it
      to the current directory, or to a custom directory defined by appending ``--dir <output_path>``.

    - Run ``python manage.py diagrams`` to generate data model and pipeline diagrams and write them
      to the current directory, or to a custom directory defined by appending ``--dir <output_path>``.


