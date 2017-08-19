
Setting up and running the example
==================================


Getting the example's code
--------------------------

The code for the example is located in the
``examples/eurominder`` directory of the `ozelot repository <https://github.com/trycs/ozelot>`_.
If you don't want to clone the repository, the easiest way is to download a current snapshot of the repository
`as a zip archive <https://github.com/trycs/ozelot/archive/master.zip>`_.
Unpack the archive to a directory of your choice, then navigate to ``examples/eurominder`` inside it.

.. note:: The link to the zip archive points to the 'master' branch of the repository, which holds
          the latest released version. If you need code from a different branch or version,
          `go to the repository <https://github.com/trycs/ozelot>`_ and navigate to your desired branch or tag.


Installing requirements with pip
--------------------------------

The Python packages required to run this example are listed in the file ``requirements.txt`` inside
the ``examples/eurominder`` directory. Install them by running

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
file included in the repository. To set up a Python 2.7 environment, use the file ``eurominder-environment-2.7.yml``
located in the example's folder to run

.. code-block:: none

    conda env crate -f eurominder-environment-2.7.yml


This will set up a new conda environment called ``ozelot-eurominder-2.7`` including all required packages.
For a Python 3.5 environment, use the file ``eurominder-environment-3.5.yml`` from the example's folder.


Configuration
-------------

Project-level configuration is defined in ``project_config.py``. You can leave all settings at the default
values to run the pipeline. A setting you might want to change is the database connection (or location of
the database file).


Input data
----------

To get the input data required to run the example, run ``python manage.py getdata``.
This downloads the data
`from the 'ozelot-example-data' repository <https://github.com/trycs/ozelot-example-data/raw/master/eurominder/data.zip>`_
and unzips it to the folder ``examples/eurominder/eurominder/data``.

Also, we provide the output database of a full pipeline run.
You can get it
`from the 'ozelot-example-data' repository <https://github.com/trycs/ozelot-example-data/raw/master/eurominder/eurominder.db.zip>`_
and unzip it. If you haven't changed the database configuration in ``project_config.py``, the file ``eurominder.db``
should come to lie next to ``manage.py`` in the ``examples/eurominder`` folder.

.. note:: Please check the :ref:`em-input-data` chapter for details on data sources,
          copyright and terms of use.


Running
-------

The example comes with a small script :file:`manage.py` that can be used to initiate various operations.

    - Run ``python manage.py getdata`` to download and unpack the pipeline input data (see above).

    - Run ``python manage.py initdb`` to (re-)initialize the database and create all tables for the :ref:`em-datamodel`.
      You need to run this once before launching the ETL pipeline.

      When using an SQLite database, the database file is created in case it does not exist yet.
      For other database backends (e.g. postgresql), the used database has to exist already.

      .. warning:: ``initdb`` deletes all present data in the database.

    - Calling ``python manage.py ingest`` runs the full :ref:`em-pipeline`. After successful completion,
      all ingested data is present in the database. A filled database from a complete pipeline
      run is also included in the example. To use it, unzip ``eurominder.db.zip`` in-place.

    - Run ``python manage.py analyze`` to generate the analysis output and write it
      to the current directory, or to a custom directory defined by appending ``--dir <output_path>``.

    - Run ``python manage.py diagrams`` to generate data model and pipeline diagrams and write them
      to the current directory, or to a custom directory defined by appending ``--dir <output_path>``.


