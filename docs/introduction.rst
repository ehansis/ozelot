.. image:: ozelot_wordmark_800.png

|
|

Introduction
############


tl;dr (a brief summary)
***********************

    - Data integration / ETL is a hard problem.
    - This package provides suggestions and examples for how to build your own ETL solution.
      The setup described here will likely work for many real-life problems. Yet, there are many other options.
    - To get started, install the package as described in :ref:`installation`, then study the :ref:`examples`
      or have a look at the :ref:`howto` chapter.
    - The complete API is documented in the `ozelot package <api/ozelot.html>`_ chapter.
    - Want to see some cool output? Check out the `Eurominder Explorer <_static/eurominder/eurominder_explorer.html>`_!


ETL introduction
****************

What is ETL?
============

ETL, short for extract, transform and load, represents the main tasks of most data integration problems:

    1. Extract the relevant data from one or several data sources.
    2. Transform the data -- clean, patch, compute derived or aggregate data, link data sources, enrich data, etc.
    3. Load the transformed data into a system for its intended use -- this may be a simple database,
       a fancy web interface, or a bunch of Excel files.

ETL is a hard problem. There is no single *best* toolset for implementing
an ETL solution, primarily because there is so much variation in data sources, data quality and intended use cases.
Dave Guarino has written a `nice article <http://daguar.github.io/2014/03/17/etl-for-america/>`_ on the
challenges of ETL and how to approach it.


Why do I need it?
=================

Does your organization have several IT systems, with no possibility to query data across all of them?
Would you like to merge data from a range of public data sources to do some interesting research?
Do you have to run 17 scripts in *just* the right order to import all your data, and would like to have
a more structured implementation of your data processing pipeline?
Do you have data lying around in hard-to-use formats and would like a nicely structured representation?

These are a few situations in which an ETL pipeline, as described in this package, may be useful.



What this package provides
**************************

Core functionality and templates
================================

The :mod:`ozelot` package does not 'solve' the problem of implementing an ETL solution.
It does provide you with core functionality, templates and examples for getting you started in
implementing your own solution.
It should work well for many real-life ETL problems, in particular those

    - that are too large or too complex to be solved in a simple spreadsheet program;
    - do not process giant amounts of data (beyond tens to hundreds of GB);
    - need to be run regularly, but not in real time or on streaming data.

By its nature, some of this documentation will read more like a tutorial than a 'classic'
Python package documentation. This is intended.


A scripted, open-source approach
================================

The :mod:`ozelot` ETL stack is fully 'scripted' - it is built entirely in Python source code.
A scripted approach provides the benefits of

    - Having your complete data processing workflow represented in code, making it reproducible and providing
      full 'documentation' of the process (if your code is readable...);
    - Providing a fully automated solution (you *will* run your process many times);
    - Enabling the re-use of functionality across the project, avoiding building common funtionality several times;
    - Giving you unbeatable flexibility and functionality, by leveraging the complete Python package ecosystem;
    - Being able to use standard tools like `git <https://git-scm.com/>`_ for revision control and collaborative
      development, which is not easily possible for GUI-based tools;
    - Enabling reasonable debugging using standard tools.

Furthermore, the :mod:`ozelot` ETL stack uses only open-source libraries. This has the advantage of

    - Providing full transparency to both your ETL solution and the underlying libraries;
    - Allowing you to use your solution in any way you care to imagine; and
    - Avoiding license fees.

.. note::

    There are `many types of open-source licenses <https://en.wikipedia.org/wiki/Comparison_of_free_and_open-source_software_licenses>`_.
    This package is released under the `MIT license <https://en.wikipedia.org/wiki/MIT_License>`_, which puts
    very few restrictions on what you can do with the code. The package does not link to any
    `GPL-ed <https://en.wikipedia.org/wiki/GNU_General_Public_License>`_ packages.


What about that name?
=====================

If your abbreviate 'Open Source Extract-Transform-Load' as 'OSETLo' and squint *really* hard,
it reads 'ozelot'. And, yes, in English you would write 'ocelot' with a 'c' instead of a 'z', but in
`some <https://de.wikipedia.org/wiki/Ozelot>`_
`other <https://nn.wikipedia.org/wiki/Ozelot>`_
`languages <https://no.wikipedia.org/wiki/Ozelot>`_
`you <https://sl.wikipedia.org/wiki/Ozelot>`_
`don't <https://sv.wikipedia.org/wiki/Ozelot>`_.


Solution architecture
*********************

The following is the suggested high-level structure of an ETL solution: The extraction and transformation process is broken
down into a series of **tasks**. These tasks are linked up to form a **pipeline**, representing dependencies
between tasks. The pipeline outputs its data to a database, using a well-defined **data model**.
The data model is described with help of an **ORM layer** (Object-Relationship-Manager layer).
Once your data is all loaded, transformed and stored in a structured manner, you can generate your
required **analysis output**.

To achieve this, :mod:`ozelot` relies on a number of awesome Pyton packages, most prominently:

    - :mod:`sqlalchemy` as database interface and for the ORM (Object-Relationship Mapping) layer
    - :mod:`luigi` for pipeline management
    - :mod:`pandas` for data analytics

The easiest way to start implementing your own solution is to study the :ref:`examples` and use one of
them as template.
The complete API is documented in the `ozelot package <api/ozelot.html>`_ chapter.


Where to find what (repositories)
*********************************

The :mod:`ozelot` library code, documentation sources and example sources reside in the repository
`ozelot <https://github.com/trycs/ozelot>`_.

Data for the examples are in the repository
`ozelot-example-data <https://github.com/trycs/ozelot-example-data>`_.

The compiled documentation (which you are currently viewing) is hosted
on `readthedocs.org <http://ozelot.readthedocs.io/>`_.


