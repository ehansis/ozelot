Project 'leonardo'
******************

.. _leonardo:

Data models change when you add new features, fix bugs or refactor your code.
The cleanest and most radical way to incorporate these changes is the 'nuclear option': wipe your database,
re-build it with the new models and completely re-run the pipeline.
This is not always desirable, however. For example, your pipeline may include some long-running tasks
that you don't wish to re-run.
Or you might want to save time during development by re-running parts of the pipeline only.

In this example, we explore different ways of implementing the same data integration pipeline with
different data models. In particular, we look at how changes to the data model are handled by each version.
Continue reading :ref:`le-modes` to learn more.


.. toctree::
   :maxdepth: 2

   modes
   running
   inputdata
   standard
   extracols
   inheritance
   kvstore
   api/leonardo.rst

