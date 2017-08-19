.. _queries:

.. py:currentmodule:: superheroes.models

Querying Data
*************

Now that we have put all our data into the database, we need some way of getting it out again.
This chapter shows how to query data using :mod:`sqlalchemy` and our ORM layer.
However, since our data is stored in a simple relational database, you could also use any other
way of accessing it (like raw SQL).

.. _ht-basic-querying-setup:

The examples below show only a fraction of the :mod:`sqlalchemy` query API.
As always, please have a look at its `excellent documentation <http://docs.sqlalchemy.org/en/latest/orm/query.html>`_
for more details.


Basic setup
===========

We make queries using the :class:`ozelot.client.Client`, see also the comments :ref:`in the ETL chapter <ht-client>`.
The initialization for all examples below looks like this:

.. code-block:: python

    >>> import models
    2018-05-21 19:29:21,119 - ozelot - INFO - Reading project configuration from project_config.pyc

    >>> from ozelot.client import get_client

    >>> client = get_client()
    2018-05-21 19:29:59,576 - ozelot - INFO - Client connecting to: sqlite:///superheroes.db

    >>> session = client.create_session()

The log message after ``import models`` stems from the first import of :mod:`ozelot.config`.
At this point, the project configuration is read. When creating the client, you get a log
message telling you which database is connected to. Note that
you will not see this message on subsequent calls to :func:`get_client`:
no new client instance is created, the module-level singleton instance is returned instead.


.. _ht-querying-objects:

Querying objects
================

Lets query some characters:

.. code-block:: python

    >>> result = session.query(models.Character)

    >>> print type(result)
    sqlalchemy.orm.query.Query

Internally, :mod:`sqlalchemy` maps our query to
an SQL statement. It is sometimes instructive to view the statement, especially when debugging:

.. code-block:: python

    >>> print result.statement
    SELECT character.id, character.name, character.url, character.real_name,
    character.occupation, character.gender, character.height, character.weight,
    character.number_of_appearances, character.first_apperance_year,
    character.universe_id, character.place_of_birth_id
    FROM character

From the query we can, for example, retrieve the first item:

.. code-block:: python

    >>> c = result.first()

    >>> print type(c)
    <class 'models.Character'>

    >>> print c.name
    89P13

    >>> print c.weight
    None

What we get back is an object as defined in our data model. We can access all its attributes
(of which some may have no value).

We can also get all items from the query, as a list of objects:

.. code-block:: python

    >>> characters = result.all()

    >>> print len(characters)
    1408

    >>> print type(characters)
    <type 'list'>

    >>> print characters[-1].name
    Zzzax

Instead of querying mapped objects, we can also query specific attributes:

.. code-block:: python

    >>> result = session.query(models.Character.name, models.Character.id)

    >>> print result.statement
    SELECT character.name, character.id
    FROM character

    >>> c = result.first()

    >>> print type(c)
    <class 'sqlalchemy.util._collections.result'>

Now we get back an :mod:`sqlalchemy`-internal data type. We can access its fields either by keys or
by their positional index:

.. code-block:: python

    >>> print c.keys()
    ['name', 'id']

    >>> print c.name, c.id
    89P13 1

    >>> print c[0], c[1]
    89P13 1

You get tuples as results even when querying only a single attribute.
If you want a list of just this attribute, you need to unpack the tuples:

.. code-block:: python

    >>> result = session.query(models.Character.name)

    >>> names = [c[0] for c in result]

    >>> print names[20:25]
    [u'Agent Chaimson', u'Agent Hart', u'Agent Hauer', u'Agent Jacobson', u'Agent Jones']


Note that here we have not called ``result.all()``. This is implicitly done by :mod:`sqlalchemy`
when iterating over a query result.


.. _ht-querying-relationships:

Querying related objects
========================

Our data model defines object relationships. When querying objects, we can simply follow
the relationships:

.. code-block:: python

    >>> result = session.query(models.Character).first()

    >>> print result.place_of_birth.name
    Halfworld

    >>> print result.place_of_birth.id
    1

    >>> print result.universe.name
    Earth-199999

:mod:`sqlalchemy` will launch separate SQL queries in the background for retrieving the related
information, if necessary. (The additional queries may cause severe performance problems in real-life
applications. Read up on 'eager loading' strategies' in order to avoid this.)


.. _ht-attr-label:

We can also use joins to jointly query attributes of related objects:

.. code-block:: python

    >>> result = session.query(models.Character.name,
    ...                        models.Character.id,
    ...                        models.Universe.name.label('universe_name'))
    ...     .join(models.Universe)

    >>> print result.statement
    SELECT character.name, character.id, universe.name AS universe_name
    FROM character JOIN universe ON universe.id = character.universe_id

    >>> print result.first()
    (u'89P13', 1, u'Earth-199999')

From our data model :mod:`sqlalchemy` knows how to join :class:`Universe` to :class:`Character`.
As long as the join is unambiguous, it is equivalent to specify the target class to join, as above,
or to specify the relationship: ``session.query([...]).join(models.Character.universe)``. (The latter
is helpful in cases where two or more relationships with the same class exist and one of them has to be selected).
Of course, we can join in and query across any number of related objects.

In the example we have given the universe name a new label, to distinguish it from the character name.
Having fields with the same name in the result set is confusing, and :mod:`sqlalchemy` may warn you
if that happens, with a message like this:

.. code-block:: none

    [...]lib/python2.7/site-packages/sqlalchemy/sql/base.py:524: SAWarning: Column 'name'
    on table <sqlalchemy.sql.selectable.Select at 0x1114f39d0; Select object> being replaced
    by Column('name', String(length=128), table=<Select object>), which has the same key.
    Consider use_labels for select() statements.

If you try to join two objects for which no relationship is defined, :mod:`sqlalchemy` will throw an exception:

.. code-block:: python

    >>> result = session.query(models.Place).join(models.MovieAppearance)
    InvalidRequestError: Could not find a FROM clause to join from.  Tried joining to
    <class 'models.MovieAppearance'>, but got: Can't find any foreign key relationships
    between 'place' and 'movieappearance'.

Our data model also defines the 'reverse' direction of relationships, as ``backref`` statements.
For example, on the relationship :attr:`Character.place_of_birth` we define the backref
:attr:`characters_born_here`. Since this relationship points to a :class:`Place` objet,
:attr:`characters_born_here` becomes an attribute of :class:`Place`:

.. code-block:: python

    >>> place = session.query(models.Place).first()

    >>> print place.name
    Germany

    >>> print len(place.characters_born_here)
    7

    >>> print type(place.characters_born_here)
    <class 'sqlalchemy.orm.collections.InstrumentedList'>

    >>> print [c.name for c in place.characters_born_here]
    [u'Abraham Erskine', u'Heinrich Zemo', u'Heinrich Zemo', u'Heinz Kruger',
     u'Heller Zemo', u'Helmut Gruler', u'Sinthea Schmidt']

When querying the ``backref``, we query the 'many' side of the 'one-to-many' relationship.
Therefore, we get back a list of objects.

.. _ht-query-outer-join:

.. note::

    Joins as stated above are, by default, 'left inner' joins. This means that the result set will
    be limited to items fhow which a relationship to the joined table exists. If you want to query
    the full resul set, including items for which the relationship is not defined, you need to
    explicitly perform a '(left) outer join'. As an example, with the default join we get only those
    characters, for which a place of birth is known, where an outer join gives us the complete
    list of characters.

    .. code-block:: python

        >>> print session.query(models.Character) \
        ...     .join(models.Character.place_of_birth) \
        ...     .count()
        167

        >>> print session.query(models.Character) \
        ...     .outerjoin(models.Character.place_of_birth) /
        ...     .count()
        1408


.. _ht-query-filter:

Filtering
=========

You can filter queries on any of the model attributes:

.. code-block:: python

    >>> result = session.query(models.Character) \
    ...     .filter(models.Character.name == 'Agent Jones')

    >>> print result.count()
    1

    >>> print result[0].name
    Agent Jones

Besides equality, filters support a range of other operators, for example SQL ``like``
and comparisons:

.. code-block:: python

    >>> print session.query(models.Character) \
    ...     .filter(models.Character.name.like('Agent%')) \
    ...     .count()
    17


    >>> print session.query(models.Character) \
    ...     .filter(models.Character.weight > 500) \
    ...     .count()
    3

.. _ht-query-missing-values:

Filtering on missing values is done by comparing to ``None``. The following queries show that
the :attr:`weight` attribute is empty for most of our characters:

.. code-block:: python

    >>> print session.query(models.Character) \
    ...     .filter(models.Character.weight == None) \
    ...     .count()
    1345

    >>> print session.query(models.Character) \
    ...     .filter(models.Character.weight != None) \
    ...     .count()
    63

.. _ht-query-one:

If you know that your query returns exactly one result, you can use the :func:`one` method to
get just this object (instead of a length-one list). In case no or multiple objects are found,
an exception is raised.

.. code-block:: python

    >>> c = session.query(models.Character) \
    ...     .filter(models.Character.id == 17) \
    ...     .one()

    >>> print c.name
    Adrian Toomes

    >>> c = session.query(models.Character) \
    ...     .filter(models.Character.id == 12345678) \
    ...     .one()
    NoResultFound: No row was found for one()

    >>> c = session.query(models.Character) \
    ...     .filter(models.Character.name.like('Z%')) \
    ...     .one()
    MultipleResultsFound: Multiple rows were found for one()

.. _ht-query-related-filter:

To filter on a related object attribute, join on the respective relationship and filter as usual.

.. code-block:: python

    >>> result = session.query(models.Character) \
    ...     .join(models.Character.place_of_birth) \
    ...     .filter(models.Place.name.like("London%"))

    >>> print result.count()
    2

    >>> print result[0].name
    Margaret Carter

    >>> print result[0].place_of_birth.name
    London

.. warning::

    If you filter on a related attribute but forget to ``join`` the related object, running the
    query might have unexpected consequences. :mod:`sqlalchemy` may run the query, without issuing
    an error or warning, but the result set may be giant (something like an outer product on the
    queried and filtered-on object), leading to vast memory consumption or an interpreter crash.


.. _ht-query-agg:

Grouping and aggregation
========================

The :mod:`sqlalchemy`
`query API <http://docs.sqlalchemy.org/en/latest/orm/query.html>`_ supports a wie range of grouping
and aggregation operations. As an example, let's query the sum of movie budgets per year in million dollars, sorted
in ascending order, limited to movies from 2010 and later:

.. code-block:: python

    >>> from sqlalchemy import func

    >>> result = session.query(models.Movie.year,
    ...                        func.sum(models.Movie.budget/ 1.e6).label('budget')) \
    ...     .filter(models.Movie.year >= 2010) \
    ...     .group_by(models.Movie.year) \
    ...     .order_by('budget')

    >>> print result.all()
    [(2018, None),
     (2019, None),
     (2017, 97.0),
     (2010, 198.0),
     (2012, 215.0),
     (2016, 223.0),
     (2015, 252.0),
     (2011, 270.0),
     (2013, 320.0),
     (2014, 570.0)]

You can express (almost) any SQL grouping/aggregation operation using :mod:`sqlalchemy`'s ORM layer
and our data model, in a relatively readable fashion. The web is full of examples and help
on this topic, in case you get stuck.


.. _ht-query-dataframe:

Querying to a pandas DataFrame
==============================

.. py:currentmodule:: ozelot.client

Often, it is useful to read the results of a query into a :class:`pandas.DataFrame`, to unleash
the full :mod:`pandas` arsenal of analytics functionality on your data. :mod:`ozelot` provides a utility
function to do just that, in :func:`ozelot.client.Client.df_query`. This function accepts a
:class:`sqlalchemy.orm.query.Query` object, runs the query and returns the result as
:class:`pandas.DataFrame`:

.. code-block:: python

    >>> query = session.query(models.Place)

    >>> df = client.df_query(query)

    >>> print df.head()
       id           name                  url
    0   1      Halfworld      /wiki/Halfworld
    1   2        Germany        /wiki/Germany
    2   3  Staten Island  /wiki/Staten_Island
    3   4        Broxton        /wiki/Broxton
    4   5      Australia      /wiki/Australia

If multiple queried attributes have the same name, you should assign unique labels
:ref:`as shown above <ht-attr-label>`. Alternatively, :func:`Client.df_query` accepts a flag
:attr:`with_labels`, which causes all attribute names to be prefixed with their respective
table name for disambiguation:

.. code-block:: python

    >>> query = session.query(models.MovieAppearance, models.Movie).join(models.Movie)

    >>> df = client.df_query(query, with_labels=True)

    >>> print df.columns
    Index([u'movieappearance_id', u'movieappearance_movie_id',
           u'movieappearance_character_id', u'movieappearance_appearance_type',
           u'movie_id', u'movie_name', u'movie_url', u'movie_year',
           u'movie_budget', u'movie_budget_inflation_adjusted',
           u'movie_imdb_rating'],
          dtype='object')

