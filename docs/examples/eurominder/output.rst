
Analysis Output
***************

We have all data nicely integrated, now let's do something with it.
All analyses described here are contained in ``analysis.py`` in the example folder.
Once you have your database filled, you can also generate all analysis output by running

.. code-block:: none

    $ python manage.py analyze


Extracting an overview table
============================

As in the :ref:`superheroes project <sh-overview-table>`, the first output we want to
create is a tabular overview of some of the integrated data. We produce a table
listing, for each NUTS2 region, the latest available value of each EuroStats indicator
along with the weather data.

The function :func:`eurominder.analysis.indicator_summary_table` generates the tables.
The data querying and massaging happening here is nothing out of the ordinary, so you
can go ahead and study the commented code by yourself.
The output is written as a
`CSV <../../_static/eurominder/nuts2_values.csv>`_ and as an
`Excel <../../_static/eurominder/nuts2_values.xlsx>`_ file.


Interactive exploration interface
=================================

And now for something completely different ...

The JavaScript libraries `dc.js <https://dc-js.github.io/dc.js/>`_ and
`crossfilter <http://square.github.io/crossfilter/>`_ can be used to build amazing interactive dashboards.
Properly explaining their use is way beyond the scope of this documentation.
Your best place to start is the `extensively documented example <https://dc-js.github.io/dc.js/docs/stock.html>`_
in the `dc.js documentation <https://dc-js.github.io/dc.js/>`_.

We use these libraries to build `Eurominder Explorer <../../_static/eurominder/eurominder_explorer.html>`_,
an interactive exploration interface to our integrated data.

* How does unemployment evolve over time in Europe?
* How do socioeconomic indicators correlate?
* Are there regions in Europe with nice weather, healthy people  and a healthy economy?

All these questions we can explore in the interface.
You can plot socioeconomic indicators on a map and correlate them in a scatter plot.
You can filter by country, region, weather or the indicator values.
And there is a 'play' button to animate development over time.
The latter is inspired by the famous
`gapminder <http://www.gapminder.org/>`_ of `TED talk fame <https://www.ted.com/speakers/hans_rosling>`_.

Below you see a screenshot of the interface:

    .. image:: ../../_static/eurominder/explorer_screenshot.png

The HTML and JavaScript is contained in the template file
:download:`eurominder_explorer.html <../../../examples/eurominder/eurominder/templates/eurominder_explorer.html>`
in the example's ``templates`` folder. (Opening this template will **not** show the dashboard, it misses the data!)
This is a `jinja2 <http://jinja.pocoo.org/docs/2.9/>`_ template, into which the function
:func:`eurominder.analysis.eurominder_explorer` injects data in JSON format.
The data querying in this function is straightforward. The main complexity lies in reshaping the queried data
to a format usable in :mod:`crossfilter.js`/:mod:`dc.js`.

Overall, we try to put as much 'business logic' as possible in Python, instead of into JavaScript.
Still the whole :mod:`crossfilter.js`/:mod:`dc.js` setup with the desired interactivity results
in quite a bit of JavaScript code. Tough luck.

The output is written as
`a single html file <../../_static/eurominder/eurominder_explorer.html>`_, with all the
data baked into it.

What should you take away from this example? JavaScript, :mod:`crossfilter.js` and :mod:`dc.js`
have a somewhat steep learning curve. If you have never worked with these technologies, jumping straight
into your own dashboard project may be a bit hard. But, and this is what you should learn here,
it is possible, it is worth it, and it can even be fun!

