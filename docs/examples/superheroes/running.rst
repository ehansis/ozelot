
Setting up and running the example
==================================


Getting the example's code
--------------------------

The code for the example is located in the
``examples/superheroes`` directory of the `ozelot repository <https://github.com/trycs/ozelot>`_.
If you don't want to clone the repository, the easiest way is to download a current snapshot of the repository
`as a zip archive <https://github.com/trycs/ozelot/archive/master.zip>`_.
Unpack the archive to a directory of your choice, then navigate to ``examples/superheroes`` inside it.

.. note:: The link to the zip archive points to the 'master' branch of the repository, which holds
          the latest released version. If you need code from a different branch or version,
          `go to the repository <https://github.com/trycs/ozelot>`_ and navigate to your desired branch or tag.


Installing requirements with pip
--------------------------------

The Python packages required to run this example are listed in the file ``requirements.txt`` inside
the ``examples/superheroes`` directory. Install them by running

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
located in the example's folder to run

.. code-block:: none

    conda env crate -f superheroes-environment-2.7.yml


This will set up a new conda environment called ``ozelot-superheroes-2.7`` including all required packages.
For a Python 3.5 environment, use the file ``superheroes-environment-3.5.yml`` from the example's folder.


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
the file ``superheroes_web_cache.db`` in the example's base directory.

We provide a filled web cache with the example. This is useful, because

    1) it lets you run the pipeline quickly, without waiting for all the data to load,
    2) it avoids unneccesary load on the data providers' servers, and
    3) you can be sure your results are consistent with the pipeline implementations and tests.

To get the pre-filled cache, run ``python manage.py getdata``.
This downloads the data
`from the 'ozelot-example-data' repository <https://github.com/trycs/ozelot-example-data/raw/master/superheroes/superheroes_web_cache.db.zip>`_
and unzips it as ``superheroes_web_cache.db``.
If you have changed the ``REQUEST_CACHE_PATH`` variable in ``project_config.py`` move/rename the file accordingly.

Also, we provide the output database of a full pipeline run.
You can get it
`from the 'ozelot-example-data' repository <https://github.com/trycs/ozelot-example-data/raw/master/superheroes/superheroes.db.zip>`_
and unzip it. If you haven't changed the database configuration in ``project_config.py``, the file ``superheroes.db``
should come to lie next to ``manage.py`` in the ``examples/superheroes`` folder.


.. _running:

Running
-------

The example comes with a small script :file:`manage.py` that can be used to initiate various operations.

    - Run ``python manage.py getdata`` to download and unpack the pre-filled web cache (see above).

    - Run ``python manage.py initdb`` to (re-)initialize the database and create all tables for the :ref:`sh-datamodel`.
      You need to run this once before launching the ETL pipeline.

      When using an SQLite database, the database file is created in case it does not exist yet.
      For other database backends (e.g. postgresql), the used database has to exist already.

      .. warning:: ``initdb`` deletes all present data in the database.

    - Calling ``python manage.py ingest`` runs the full :ref:`sh-pipeline`. After successful completion,
      all ingested data is present in the database.

    - Run ``python manage.py analyze`` to generate the analysis output and write it
      to the current directory, or to a custom directory defined by appending ``--dir <output_path>``.

    - Run ``python manage.py diagrams`` to generate data model and pipeline diagrams and write them
      to the current directory, or to a custom directory defined by appending ``--dir <output_path>``.


