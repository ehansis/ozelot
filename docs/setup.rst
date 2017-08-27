Installation and Setup
**********************


.. _installation:


Python setup
============

This documentation assumes that you have Python installed and that you have a working knowledge of the language.

If you don't have Python installed, there are many ways to do so
(a fair overview is beyond the scope of this documentation).
On Mac OS, Windows or Linux, one easy way is to use
`Anaconda <https://www.continuum.io/downloads>`_, which comes with a built-in package manager
and support for virtual environments.

This project was built and tested with **Python versions 2.7 and 3.5** and probably works with versions 3.6+ as well.

Use of a **virtual environment** is strongly recommended. A virtual environment lets you have separate
Python configurations, e.g. different versions of packages, for different projects.
For Anaconda, creating and using environments is
`described in the documentation <https://conda.io/docs/using/envs.html>`_.
If you use a different Python distribution, set up your virtual environment using
`virtualenv <https://conda.io/docs/using/envs.html>`_.


.. _ozelot-package-installation:

Package installation
====================

Once you have Python up and running (and have your virtual environment activated), install :mod:`ozelot` from GitHub:

.. code-block:: none

    pip install ozelot

If you are using anaconda, it is a good idea to install :mod:`numpy`, :mod:`scipy`, :mod:`pandas`,
:mod:`matplotlib` and :mod:`lxml` via the conda package manager **before** installing :mod:`ozelot`
(if you don't have the packages installed already).
To do this, run

.. code-block:: none

    conda install numpy scipy pandas matplotlib lxml

:mod:`scipy` and :mod:`matplotlib` are not required for :mod:`ozelot` but for running the examples.
:mod:`lxml` is required for running the unit tests and the examples.


Ready-made conda environments
=============================

If you want to set up a fresh conda environment for trying out :mod:`ozelot`, there is a handy environment
file included in the repository. To set up a Python 2.7 environment, use the file ``environment-2.7.yml``
`located in the repository root <https://raw.githubusercontent.com/trycs/ozelot/master/environment-2.7.yml>`_
and run

.. code-block:: none

    conda env create -f environment-2.7.yml


This will set up a new conda environment called ``ozelot-2.7`` including all required packages.
For a Python 3.5 environment, use the file ``environment-3.5.yml``
`from the repository root <https://raw.githubusercontent.com/trycs/ozelot/master/environment-3.5.yml>`_.

