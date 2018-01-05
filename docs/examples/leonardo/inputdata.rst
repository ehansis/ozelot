Input data
**********

Wikidata and SPARQL
-------------------

This example uses data from `Wikidata <https://www.wikidata.org>`_, 'the free knowledge database
with 42,268,475 data items that anyone can edit' (... at the time of writing this documentation).
Wikidata contains structured data on a huge variety of topics, which are linked in a knowledge graph.
Data is `public domain <https://creativecommons.org/publicdomain/zero/1.0/>`_, i.e. free for any type of use.

Data can be queried via the `Wikidata Query Service <https://query.wikidata.org/>`_ using
the `SPARQL <https://en.wikipedia.org/wiki/SPARQL>`_ query language.
The Query Service page contains links to helpful
`SPARQL help <https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/Wikidata_Query_Help>`_
and examples.
The SPARQL queries may look a bit opaque in the beginning, but the help and example pages are pretty good
and will enable you to build your first queries soon.


Portrait paintings and their artists
------------------------------------

In this example we will use some data about paintings and their artists.
In particular, we will limit the analysis to portrait paintings.
It is not required that you understand every aspect about the queries below, they are given here mainly
for completeness. The resulting data, after executing the queries in the
`Wikidata Query Service <https://query.wikidata.org/>`_, can be downloaded
`from the 'ozelot-example-data' repository <https://github.com/trycs/ozelot-example-data/raw/master/leonardo/data.zip>`_.

The first query retrieves data about the paintings.
It searches items that are any subclass of a painting (Q3305213) and are of the genre 'portrait painting'
(Q1400853). For these, it queries the creator (P170) as Wikidata link, width (P2049) and height (P2048)
in normalized units, and the date of inception (P571).
Since there may be many dates of inception (e.g. an earliest and latest estimated date),
a grouped query is executed and the minimum date selected. For the other fields,
a random sample is selected (from the, usually, single available value).
When writing this example, this returned data for 4500 paintings.

.. code-block:: none

    SELECT ?painting ?paintingLabel
    (SAMPLE(?creator) AS ?creator)
    (SAMPLE(?width) AS ?width)
    (SAMPLE(?height) AS ?height)
    (MIN(?inception) AS ?inception)
    WHERE {
      ?painting (wdt:P31/wdt:P279*) wd:Q3305213.
      ?painting wdt:P136 wd:Q1400853.
      ?painting wdt:P170 ?creator.
      ?painting p:P2048/psn:P2048 [wikibase:quantityAmount ?height;].
      ?painting p:P2049/psn:P2049 [wikibase:quantityAmount ?width;].
      ?painting wdt:P571 ?inception.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    GROUP BY ?painting ?paintingLabel

The second query retrieves data about the artists.
For portrait paintings selected as above, it retrieves the artist/creator (P170).
For the artist it exports the gender (P21) with an English label and
the date of birth (P569). Again, as there may be several dates of birth given,
a grouped query is used.
This returned data for 3159 artists, at the time of writing the example.

.. code-block:: none

    SELECT ?artist ?artistLabel
    (SAMPLE(?genderLabel) AS ?genderLabel)
    (MIN(?dob) AS ?dob)
    WHERE {
      ?painting (wdt:P31/wdt:P279*) wd:Q3305213.
      ?painting wdt:P136 wd:Q1400853.
      ?painting wdt:P170 ?artist.
      ?artist wdt:P21 ?gender.
      ?gender rdfs:label ?genderLabel.
      FILTER(LANG(?genderLabel) = "en")
      ?artist wdt:P569 ?dob.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    GROUP BY ?artist ?artistLabel


Representation in the pipeline
------------------------------

The input tables, including loading functions,
are contained in :mod:`leonardo.common.input.ArtistsInputData` and :mod:`leonardo.common.input.PaintingsInputData`.
These are common to all model/pipeline versions, the rest of the pipeline is implemented separately for each version.
