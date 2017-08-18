
Setting up and running the example
==================================


Installation
------------

The code for the example doesn't have to be installed. Just copy the contents of the
``eurominder`` directory from the `example repository <https://github.com/ehansis/ozelot-examples>`_
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
file included in the repository. To set up a Python 2.7 environment, use the file ``eurominder-environment-2.7.yml``
`located in the example's folder <https://raw.githubusercontent.com/ehansis/ozelot-examples/master/eurominder/eurominder-environment-2.7.yml>`_
and run

.. code-block:: none

    conda env crate -f eurominder-environment-2.7.yml


This will set up a new conda environment called ``ozelot-eurominder-2.7`` including all required packages.
For a Python 3.5 environment, use the file ``eurominder-environment-3.5.yml``
`from the repository root <https://raw.githubusercontent.com/ehansis/ozelot-examples/master/eurominder/eurominder-environment-3.5.yml>`_.

Note that this will not download the example's source code, see above for how to get that.


Input data
----------

All data files mentioned below are included in the ``eurominder/data/data.zip`` in the
example's directory. Unzip its contents in-place (all output should to into the ``data`` directory).
Please check the :ref:`em-input-data` chapter for details on data sources, copyright and terms of use.


Configuration
-------------

Project-level configuration is defined in ``project_config.py``. You can leave all settings at the default
values to run the pipeline.


Running
-------

The example comes with a small script :file:`manage.py` that can be used to run initiate various operations.

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


