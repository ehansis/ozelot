
Input data
==========

Most data used in the example are scraped from the
`Marvel wikia page <http://marvel.wikia.com/wiki/Marvel_Database>`_:

    - Characters (heroes, villains and supporting characters)
    - Marvel 'universes'
    - Movies and movie appearances of characters

.. note::

    Marvel comics are organized in 'Universes' or 'Continuities' within
    `a larger multiverse <https://en.wikipedia.org/wiki/Multiverse_(Marvel_Comics)>`_.
    For storage and performance reasons, only characters belonging to a pre-defined list of universes
    are imported, as set in ``project_config.py`` variable ``UNIVERSES``.
    This list default to the top 20 universes that have characters with movie appearances.
    Set it to ``None`` to import all characters from all universes.

Supporting data are from `imdb.com <http://www.imdb.com/>`_ (movie ratings)
and from the `Bureau of Labor Statistics <https://data.bls.gov>`_ (consumer price index data,
used for inflation adjustment).
Detailed descriptions of the used data can be found in the :ref:`sh-pipeline` chapter.

The page structure and data in the we-based data sources may change at any time.
This might break the ingestion pipline code or the tests.
To get results consistent with the provided code (and to save time), we strongly recommend
downloading cached data as described in :ref:`cached_data`.

Before running the example or making any use of the data, please make sure to read and adhere to
the terms of use of all data providers.
