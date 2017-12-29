Project 'leonardo'
******************

.. _leonardo:

Data models change when you add new features, fix bugs or refactor your code.
The cleanest and most radical way to incorporate these changes is the 'nuclear option': wipe your database,
re-build it with the new models and completely re-run the pipeline.
This is not always desirable, however. For example, your pipeline may include some long-running tasks
that you don't wish to re-run.
Or you might want to save time during development by re-running parts of the pipeline only.

- RDBMS and migrations
- Tasks and foreign key constraints
- Document-oriented DBs

For each model:

- model structure
- storing
- querying
- introducing the model change
- one-off data loading
- re-running a part of the pipeline

This example demonstrates four data models and how they cope with data model changes: the 'standard' model
used so far; a model using 'extra columns'; a model using inheritance; and a
key-value-store (a.k.a. entity-attribute-value model).

# .. toctree::
#    :maxdepth: 2
#
#    running
#    inputdata
#    datamodel
#    pipeline
#    queries
#    management
#    output
#   api/superheroes.rst
