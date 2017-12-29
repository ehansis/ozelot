.. _howto:

HowTo
*****

Here you can find links to specific topics discussed in the package and example
documentation.

ORM data model
==============

    - :ref:`ORM model basics and the ozelot Base class <ht-orm-basics>`
    - :ref:`Basic field validation <ht-basic-field-validation>`
    - :ref:`Basic (one-to-many) object relationships <ht-object-relationships>`
    - :ref:`Many-to-many relationships using an association object <ht-many-to-many>`
    - :ref:`Representing time series <ht-timeseries-model>`
    - :ref:`Cascading deletes across relationships <ht-cascading>`
    - :ref:`Initializing a database with the ORM schame <ht-initializing-db>`
    - :ref:`Drawing a data model diagram <ht-model-diagram>`

ETL pipeline
============

Defining the pipeline
---------------------

    - :ref:`Luigi basics <ht-luigi-basics>`
    - :ref:`The ozelot database client <ht-client>`
    - :ref:`The how and why of clear() methods in tasks <ht-clear-methods>`
    - :ref:`Defining a custom clear() method <ht-custom-clear>`
    - :ref:`The ORMTarget and ORMTask classes <ht-ormtarget-ormtask>`
    - :ref:`The ORMObjectCreatorMixin for object-generating tasks <ht-ormobjectcreator>`
    - :ref:`Static input files and the InputFile class <ht-static-input-file>`
    - :ref:`Defining a (top-level) wrapper task <ht-wrapper-task>`
    - :ref:`Data consistency checks for the pipeline results <ht-consistency-checks>`
    - :ref:`ht-subclassing-tasks`
    - :ref:`ht-task-parameters`
    - :ref:`Using the client and session properties of ORMTask <ht-task-session>`

Running the pipeline
--------------------

    - :ref:`Running specific tasks <ht-running-tasks>`
    - :ref:`Checking and acting on pipeline run failures <ht-pipeline-exit-status>`
    - :ref:`ht-checking-completion`
    - :ref:`ht-clearing-tasks`
    - :ref:`Drawing a pipeline diagram <ht-pipeline-diagram-simple>`
    - :ref:`Pipeline diagrams for tasks with parameters <ht-pipeline-diagram-params>`


ORM data management
===================

    - :ref:`Creating references to other objects <ht-creating-orm-references>`
    - :ref:`Creating many-to-many association objects <ht-many-to-many-generation>`
    - :ref:`Adding an object class to an existing database <ht-add-object-class>`
    - :ref:`Modifying an object class in an existing database <ht-modify-object-class>`
    - :ref:`Standard (slow but convenient) instance creation <ht-slow-add>`
    - :ref:`ht-write-sql`
    - :ref:`ht-bulk-save`
    - :ref:`Issues with bulk saving and auto-incrementing primary keys <ht-sequences-and-bulk>`


Queries
=======

    - :ref:`Basic setup for querying data <ht-basic-querying-setup>`
    - :ref:`Querying single object classes <ht-querying-objects>`
    - :ref:`Querying relationships (and their 'backref' reverese) <ht-querying-relationships>`
    - :ref:`Assigning labels to queried attributes <ht-attr-label>`
    - :ref:`Inner and outer joins in queries <ht-query-outer-join>`
    - :ref:`Filtering queries <ht-query-filter>`
    - :ref:`Filtering on missing values <ht-query-missing-values>`
    - :ref:`Retrieving exactly one item <ht-query-one>`
    - :ref:`Grouping and aggregation <ht-query-agg>`
    - :ref:`Querying to a pandas DataFrane <ht-query-dataframe>`
    - :ref:`ht-delete-cascade`

Web scraping
============

    - :ref:`Requesting web pages (via the request cache) <ht-requesting-pages>`
    - :ref:`HTML parsing using lxml <ht-lxml-html-parsing>`

