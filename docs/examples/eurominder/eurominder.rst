Project 'eurominder'
********************

The European Union gathers and publishes a wider range of interesting data about its member states.
For example, you can get `regional statistictical data <http://ec.europa.eu/eurostat/web/regions/overview>`_
for many socioeconomic parameters. We want to combine these with
`weather data <https://www.esrl.noaa.gov/psd/data>`_, to correlate weather and economic success.
For data exploration, we will build an interface reminiscent of the famous
`gapminder <http://www.gapminder.org/>`_, shown in `many TED talks <https://www.ted.com/speakers/hans_rosling>`_.

The socioeconomic data is published on the level of
`NUTS2 regions <http://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/nuts#nuts13>`_,
and this is the granularity on which we want to store and analyze all data.
The weather data is provided as maps. To get values on the level of NUTS2 regions, we need to average the maps'
values within the boundary polygon of each NUTS2 region.

This amounts to an interesting problem in geospatial data processing, for which many people would
probably turn to specialty software. Fortunately, though, the Python data analytics stack provides all
the tools we need to tackle the problem. (Admittedly, we make some approximations to get a simple solution,
so the result may not be comparable to professional software in terms of accuracy.)
At the same time, this example introduces some advanced features of :class:`ozelot` that speed up loading of
large amounts of data and reduce boilerplate code.

In this example, you can learn how to:

    - Do fast bulk inserts of large amounts of data into the data model
    - Avoid code duplication by subclassing tasks and using task parameters
    - Use the :attr:`client` and :attr:`session` properties of :class:`ozelot.etl.tasks.ORMTask`
    - Perform geospatial processing with :mod:`matplotlib` and :mod:`scipy`
    - Build an interactive exploration interface with `dc.js <https://dc-js.github.io/dc.js/>`_
      and `crossfilter <http://square.github.io/crossfilter/>`_.

The following chapters describe the example in detail:

.. toctree::
    :maxdepth: 2

    running
    inputdata
    datamodel
    pipeline
    output
    api/eurominder
