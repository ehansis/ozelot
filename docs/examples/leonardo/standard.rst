.. _le-standard:

Standard version
****************

- model structure
- storing
- querying
- introducing the model change
- one-off data loading
- re-running a part of the pipeline

.. _le-standard-model:

Data model
==========

.. py:currentmodule:: leonardo.standard.models

Our data model in this example consists of two object types, paintings and artists, each modeled
by its own ORM class. In our 'standard' way of doing things, both are pretty straightforward.
The :class:`Artist` model stores the unique wikipedia object ID :attr:`wiki_id` and name
of the artist.
In the :ref:`extended version <le-modes>`, it additionally stores gender and date of birth.

.. literalinclude:: ../../../examples/leonardo/leonardo/standard/models.py
    :pyobject: Artist

The :class:`Painting` is similarly straightforward and should be self-descriptive.
Note the foreign-key relationship linking a :class:`Painting` to an :class:`Artist`;
this is going to cause headaches when working with data model changes.

.. literalinclude:: ../../../examples/leonardo/leonardo/standard/models.py
    :pyobject: Painting


Pipeline
========


