Pipeline management
*******************


Database initialization
=======================


The first thing you need to do, before running your ETL pipeline, is to initialize your database and
set up the table structure representing you data model.
The example includes a simple function :func:`superheroes.models.reinitialize` to clear and re-build the
database. This function can also be run :ref:`via the management script <running>`.

.. warning:: Re-initializing deletes all data currently held in the respective tables of your database.

Since we store task completion information within our data model, all tasks
will be 'incomplete' after (re-) initializing the database.


.. _ht-running-tasks:

Running tasks
=============

In this example, we run :mod:`luigi` tasks programatically using a local scheduler.
In serious projects you will likely run tasks using a central :mod:`luigi` scheduler.
This enables task coordination between processes and worker hosts, and also gives
you a nice web interface for task monitoring.
See `the luigi documentation <http://luigi.readthedocs.io/en/stable/>`_ for details.

The pipeline routes all web requests through a web request cache, to speed up
repeated runs. See :ref:`cached_data` for configuration details and information on
how to obtain a pre-filled cache file.


Running a single task
---------------------

.. py:currentmodule:: superheroes.pipeline

You can run a single task (or a list of tasks) with :func:`luigi.build`. Here, we
reinitialize the database and run the :class:`LoadUniverses` task from our pipeline:

.. code-block:: python

    >>> import pipeline
    2018-05-28 11:18:11,257 - ozelot - INFO - Reading project configuration from project_config.pyc

    >>> import luigi

    >>> import models

    >>> models.reinitialize()
    2018-05-28 11:18:34,503 - ozelot - INFO - Client connecting to: sqlite:///superheroes.db

    >>> luigi.build([pipeline.LoadUniverses()], local_scheduler=True)
    DEBUG: Checking if LoadUniverses() is complete
    INFO: Informed scheduler that task   LoadUniverses__99914b932b   has status   PENDING
    INFO: Done scheduling tasks
    INFO: Running Worker with 1 processes
    DEBUG: Asking scheduler for work...
    DEBUG: Pending tasks: 1
    INFO: [pid 3521] Worker Worker(salt=008989440, workers=1, host=My-Air, username=myuser, pid=3521) running   LoadUniverses()
    2018-05-28 11:19:06,911 - ozelot - INFO - Client connecting to: sqlite:///superheroes_web_cache.db
    2018-05-28 11:19:06,931 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/api/v1/Articles/List/?category=Realities&limit=5000
    INFO: [pid 3521] Worker Worker(salt=008989440, workers=1, host=My-Air, username=myuser, pid=3521) done      LoadUniverses()
    DEBUG: 1 running tasks, waiting for next task to finish
    INFO: Informed scheduler that task   LoadUniverses__99914b932b   has status   DONE
    DEBUG: Asking scheduler for work...
    DEBUG: Done
    DEBUG: There are no more tasks to run at this time
    INFO: Worker Worker(salt=008989440, workers=1, host=My-Air, username=myuser, pid=3521) was stopped. Shutting down Keep-Alive thread
    INFO:
    ===== Luigi Execution Summary =====

    Scheduled 1 tasks of which:
    * 1 ran successfully:
        - 1 LoadUniverses()

    This progress looks :) because there were no failed tasks or missing external dependencies

    ===== Luigi Execution Summary =====


.. note::

    If you happen to forget the ``local_scheduler=True`` flag to :func:`luigi.build`, you
    will get error messages about a :mod:`luigi` daemon not being found.


The :class:`LoadUniverses` task has no requirements, so :mod:`luigi` had to run just this one task.
If there are requirements to build, :mod:`luigi` will run the respective tasks beforehand:

.. code-block:: python

    >>> models.reinitialize()

    >>> luigi.build([pipeline.LoadCharacters()], local_scheduler=True)
    DEBUG: Checking if LoadCharacters() is complete
    DEBUG: Checking if LoadUniverses() is complete
    INFO: Informed scheduler that task   LoadCharacters__99914b932b   has status   PENDING
    INFO: Informed scheduler that task   LoadUniverses__99914b932b   has status   PENDING
    INFO: Done scheduling tasks
    INFO: Running Worker with 1 processes
    DEBUG: Asking scheduler for work...
    DEBUG: Pending tasks: 2
    INFO: [pid 3521] Worker Worker(salt=784662517, workers=1, host=My-Air, username=myuser, pid=3521) running   LoadUniverses()
    2018-05-28 11:22:16,747 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/api/v1/Articles/List/?category=Realities&limit=5000
    INFO: [pid 3521] Worker Worker(salt=784662517, workers=1, host=My-Air, username=myuser, pid=3521) done      LoadUniverses()
    DEBUG: 1 running tasks, waiting for next task to finish
    INFO: Informed scheduler that task   LoadUniverses__99914b932b   has status   DONE
    DEBUG: Asking scheduler for work...
    DEBUG: Pending tasks: 1
    INFO: [pid 3521] Worker Worker(salt=784662517, workers=1, host=My-Air, username=myuser, pid=3521) running   LoadCharacters()
    2018-05-28 11:22:17,168 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/api/v1/Articles/List/?category=Characters&limit=100000
    2018-05-28 11:22:17,611 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/wiki/89P13_(Earth-199999)
    2018-05-28 11:22:17,648 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/wiki/Abigail_Brand_(Earth-8096)
    [...]
    2018-05-28 11:22:42,463 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/wiki/Zip_(Earth-199999)
    2018-05-28 11:22:42,479 - ozelot - INFO - Request cache hit: http://marvel.wikia.com/wiki/Zzzax_(Earth-8096)
    INFO: [pid 3521] Worker Worker(salt=784662517, workers=1, host=My-Air, username=myuser, pid=3521) done      LoadCharacters()
    DEBUG: 1 running tasks, waiting for next task to finish
    INFO: Informed scheduler that task   LoadCharacters__99914b932b   has status   DONE
    DEBUG: Asking scheduler for work...
    DEBUG: Done
    DEBUG: There are no more tasks to run at this time
    INFO: Worker Worker(salt=784662517, workers=1, host=My-Air, username=myuser, pid=3521) was stopped. Shutting down Keep-Alive thread
    INFO:
    ===== Luigi Execution Summary =====

    Scheduled 2 tasks of which:
    * 2 ran successfully:
        - 1 LoadCharacters()
        - 1 LoadUniverses()

    This progress looks :) because there were no failed tasks or missing external dependencies

    ===== Luigi Execution Summary =====


Running all tasks
-----------------

.. py:currentmodule:: superheroes.pipeline

Our pipeline contains a handy wrapper task :class:`LoadEverything` that includes our whole pipeline as
requirements. Building the complete pipeline is now as easy as:

.. code-block:: python

    >>> luigi.build([pipeline.LoadEverything()], local_scheduler=True)
    [...]
    ===== Luigi Execution Summary =====

    Scheduled 8 tasks of which:
    * 2 present dependencies were encountered:
        - 1 ConsumerPriceIndexFile()
        - 1 IMDBMovieRatings()
    * 6 ran successfully:
        - 1 InflationAdjustMovieBudgets()
        - 1 LoadCharacters()
        - 1 LoadEverything()
        - 1 LoadMovieAppearances()
        - 1 LoadMovies()
        ...

    This progress looks :) because there were no failed tasks or missing external dependencies

    ===== Luigi Execution Summary =====

If you had run some of the tasks before, :mod:`luigi` will recognize them as being complete and
will not re-run them. Launching the build command a second time (without re-initializing), :mod:`luigi` immediately sees
the completion marker on :class:`LoadEverything` and exits:

.. code-block:: python

    >>> luigi.build([pipeline.LoadEverything()], local_scheduler=True)
    DEBUG: Checking if LoadEverything() is complete
    INFO: Informed scheduler that task   LoadEverything__99914b932b   has status   DONE
    INFO: Done scheduling tasks
    INFO: Running Worker with 1 processes
    DEBUG: Asking scheduler for work...
    DEBUG: Done
    DEBUG: There are no more tasks to run at this time
    INFO: Worker Worker(salt=556453380, workers=1, host=My-Air, username=myuser, pid=3521) was stopped. Shutting down Keep-Alive thread
    INFO:
    ===== Luigi Execution Summary =====

    Scheduled 1 tasks of which:
    * 1 present dependencies were encountered:
        - 1 LoadEverything()

    Did not run any tasks
    This progress looks :) because there were no failed tasks or missing external dependencies

    ===== Luigi Execution Summary =====



.. _ht-checking-completion:

Checking task completion
========================

.. py:currentmodule:: superheroes.pipeline

Imaging you are given the output database of an ETL pipeline and want to know what state it is in -- which
tasks have run already, which are incomplete? The method :func:`ozelot.etl.tasks.check_completion` takes
a task instance as input and checks the complete *upstream* pipeline from this task on for completion.
For doing this, all task requirements are checked in a recursive fashion.

As an example, let's run only the :class:`LoadCharacters` task and check completion on our
:class:`LoadEverything` wrapper task:

.. code-block:: python

    >>> models.reinitialize()

    >>> luigi.build([pipeline.LoadCharacters()], local_scheduler=True)
    [...]
    This progress looks :) because there were no failed tasks or missing external dependencies
    ===== Luigi Execution Summary =====

    >>> from ozelot.etl import tasks

    >>> complete = tasks.check_completion(pipeline.LoadEverything())
    2017-05-28 12:29:04,300 - ozelot - INFO - Task incomplete: LoadMovies {}
    2017-05-28 12:29:04,306 - ozelot - INFO - Task incomplete: LoadMovieAppearances {}
    2017-05-28 12:29:04,311 - ozelot - INFO - Task incomplete: InflationAdjustMovieBudgets {}
    2017-05-28 12:29:04,311 - ozelot - INFO - Task incomplete: LoadEverything {}
    2017-05-28 12:29:04,311 - ozelot - INFO - Task completion checking, summary:
    {'Complete tasks': 4, 'Incomplete tasks': 4}

    >>> print complete
    False

This prints a listing of incomplete tasks and a summary count (which you can get
as return value by passing ``return_stats=True``), and returns the overall completion state (here: ``False``).
You can get more detailed output by modifying the
log level in your ``project_config.py``, for example setting ``LOG_LEVEL = logging.DEBUG``.

Once we build the whole pipeline, all tasks are found to be complete.

.. code-block:: python

    >>> luigi.build([pipeline.LoadEverything()], local_scheduler=True)
    [...]
    This progress looks :) because there were no failed tasks or missing external dependencies
    ===== Luigi Execution Summary =====

    >>> tasks.check_completion(pipeline.LoadEverything())
    2017-05-28 12:38:14,868 - ozelot - INFO - Task completion checking, summary:
    {'Complete tasks': 8}
    Out[21]: True


:func:`check_completion` regards all tasks as incomplete that are marked incomplete themselves, or for which any
requirement (recursively) is incomplete. For example, if :class:`LoadMovies` was incomplete but all other
tasks marked complete, we would get as a result:

.. code-block:: python

    >>> complete = tasks.check_completion(pipeline.LoadEverything())
    2017-05-28 12:52:24,109 - ozelot - INFO - Task incomplete: LoadMovies {}
    2017-05-28 12:52:24,122 - ozelot - INFO - Task complete but requirements incomplete: LoadMovieAppearances {}
    2017-05-28 12:52:24,132 - ozelot - INFO - Task complete but requirements incomplete: InflationAdjustMovieBudgets {}
    2017-05-28 12:52:24,140 - ozelot - INFO - Task complete but requirements incomplete: LoadEverything {}
    2017-05-28 12:52:24,140 - ozelot - INFO - Task completion checking, summary:
    {'Complete tasks': 4, 'Incomplete tasks': 4}

    >>> print complete
    False

For this example, the completion marker on :class:`LoadMovies` was artificially removed. This is a bad
state for your pipeline to be in -- you should re-build all tasks depend on :class:`LoadMovies`, but
they have apparently already run.


.. _ht-clearing-tasks:

Clearing and re-running tasks
=============================

.. py:currentmodule:: superheroes.pipeline

:mod:`ozelot` helps you with re-building specific tasks and their dependents. Let's assume that you built the
whole pipeline and afterwards made a small change to the :class:`LoadMovies` code. You want to re-run
this task, and all tasks that depend on it, while avoiding clearing and re-running tasks that don't depend
on :class:`LoadMovies`.

For this purpose, you first call :func:`LoadMovies.clear` to clear the task output
(and mark the task incomplete). Then you tell
:func:`ozelot.etl.tasks.check_completion` to call :func:`clear` for all tasks that it regards as incomplete,
by passing the flag ``clear=True``:

.. code-block:: python

    >>> pipeline.LoadMovies().clear()

    >>> complete = tasks.check_completion(pipeline.LoadEverything(), clear=True)
    2017-05-29 21:52:17,267 - ozelot - INFO - Task incomplete: LoadMovies {}
    2017-05-29 21:52:17,286 - ozelot - INFO - Cleared task: LoadMovies {}
    2017-05-29 21:52:17,292 - ozelot - INFO - Task complete but requirements incomplete: LoadMovieAppearances {}
    2017-05-29 21:52:17,314 - ozelot - INFO - Cleared task: LoadMovieAppearances {}
    2017-05-29 21:52:17,318 - ozelot - INFO - Task complete but requirements incomplete: InflationAdjustMovieBudgets {}
    2017-05-29 21:52:17,337 - ozelot - INFO - Cleared task: InflationAdjustMovieBudgets {}
    2017-05-29 21:52:17,337 - ozelot - INFO - Task complete but requirements incomplete: LoadEverything {}
    2017-05-29 21:52:17,352 - ozelot - INFO - Cleared task: LoadEverything {}
    2017-05-29 21:52:17,352 - ozelot - INFO - Task completion checking, summary:
    {'Complete tasks': 4, 'Incomplete tasks': 4, 'Cleared': 4}

    >>> print complete
    False


Note that, as before, we pass :class:`LoadEverything` into :func:`check_completion`, to check
completion (and, where necessary, clear tasks) for the whole pipeline.
After this cleaning operation, you can re-build the necessary parts of your pipeline.

Besides ``clear``, :func:`ozelot.etl.tasks.check_completion` also accepts a flag ``mark_incomplete``.
This will delete the completion marker for (recursively) incomplete tasks.
However, it does not change the actual contents of your database, so unless your tasks are idempotent,
re-running the pipeline will probably lead to duplicate records.

.. note::

    Be careful when modifying task completion markers and clearing/re-building the output
    of single tasks. It is easy to overlook task interactions and side effects
    in complex pipelines. Accurate and well-tested :func:`clear` methods for your tasks help.
    Yet, it remains challenging to ensure that your pipeline completion markers are consistent
    with the actual state of data in your database (and with your understanding of what that state
    should be).


Managing data model changes
===========================

Making changes to the data model and migrating your database to a new schema is a challenging topic.
If you need to migrate regularly, consider using a tool like `alembic <http://alembic.zzzcomputing.com/>`_.

For many small- to medium-sized projects, the 'nuclear' option is a safe bet: re-initalize the database
and rebuild the whole pipeline using your new data model.
If you find this as being tedious for small changes, here are some other options.

.. _ht-add-object-class:

Adding an object class
----------------------

In :mod:`sqlalchemy`, each ORM object class maps to a table. If you add an object class
derived from :class:`ozelot.orm.base`, you can create that table calling :func:`create_table` on
an instance of that class.

.. code-block:: python

    >>> import models
    >>> from ozelot import client
    >>> cl = client.get_client()
    >>> models.MovieAppearance().create_table(cl)

(:func:`ozelot.orm.base.ExtendedBase.create_table` is a one-liner method, you can easily replicate it
if you don't want to use :class:`ozelot.orm.base`).


.. _ht-modify-object-class:

Modifying an object class
-------------------------

Modifying an existing object class is a bit more difficult. If you extend the class by one or a few fields,
you could issue the respective ``ALTER TABLE ... ADD COLUMN ...`` statements in an SQL interface of your choice.

If you want to completely re-write the table using the :func:`create_table` method cited above, you would
have to delete the table first. To do that, there exists a corresponding :func:`drop_table` method:

.. code-block:: python

    >>> import models
    >>> from ozelot import client
    >>> cl = client.get_client()
    >>> models.MovieAppearance().drop_table(cl)

However, this is not possible if there are other models that keep foreign-key references to the table, because
most databases enforce foreign key constraints! (SQLite does not, here you can drop as you please,
with possibly devastating consequences for your data integrity.)
In this case, you would have to (recursively) drop all tables that keep foreign key references before dropping your
target table, and re-create them in reverse order.

