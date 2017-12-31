.. _le-modes:

Models and migrations
*********************

- RDBMS and migrations
- Tasks and foreign key constraints
- Document-oriented DBs

Four modes, with extension
==========================

This example demonstrates four data models and how they cope with data model changes:
the :ref:`'standard' model <le-standard>` that was used so far;
a model using :ref:`extra columns <le-extracols>`;
a model using :ref:`inheritance <le-inheritance>`;
and a model storing key-value-pairs, also known as an :ref:`entity-attribute-value model <le-kvstore>`.
Which mode is being used is determined by the variable :attr:`MODE` in ``project_config.py``.
Please refer to :ref:`le-configuration`.
Each mode also comes with its own pipeline.

To demonstrate an evolving data model, each model/pipeline can be run with or without activating
a data model extension.
The extended version adds two attributes to one of the data models
(see e.g. the :ref:`standard data models <le-standard-model>`).
This is governed by setting the variable :attr:`EXTENDED` in ``project_config.py`` (see :ref:`le-configuration`).

In a real-life scenario you would, most likely, add fields to the model as your solution evolves, instead of
coding your extension into your models and switch it on when needed.
The extension by switch is done for illustration purposes here, to avoid having the user code the extension.

