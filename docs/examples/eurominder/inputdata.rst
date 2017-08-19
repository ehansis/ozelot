
.. _em-input-data:

Input data
**********

All data files mentioned below are included in the ``eurominder/data/data.zip`` in the
example's directory. Unzip its contents in-place (all output should to into the ``data`` directory).
Please refer to the sections below for links to copyright information and terms of use for the different data sources.


NUTS2 nomenclature and boundaries
=================================

The European regional nomenclature, NUTS, provides a segmentation of European countries into comparable units.
It comes at different levels of granularity, with NUTS1 being the coarsest level,
and NUTS2, NUTS3 etc. the finer levels.
We are using data at the NUTS2 level, defined as 'basic regions', with approximately 800,000 to 3 million inhabitants.

We downloaded the official 2013 NUTS2 nomenclature `from EuroStat
<http://ec.europa.eu/eurostat/ramon/nomenclatures/index.cfm?TargetUrl=LST_CLS_DLD&StrNom=NUTS_2013L&StrLanguageCode=EN&StrLayoutCode=HIERARCHIC>`_
as CSV file. It lists region codes and names.
Please refer to that site for copyright information and terms of use.

The NUTS2 geographic boundaries in GeoJSON format were obtained from
`Open Knowledge International <http://data.okfn.org/data/core/geo-nuts-administrative-boundaries>`_.
The original boundary data is copyrighted by EuroGeographics and was
obtained from the `GISCO EU web site <http://ec.europa.eu/eurostat/web/gisco/geodata/reference-data>`_.
Refer to the
`Copyright notice <http://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units>`_
of the source dataset for any specific restrictions on using these data.


EuroStat regional data
======================

EuroStat, the European statistics office, publish `regional data <http://ec.europa.eu/eurostat/web/regions/overview>`_
for many socioeconomic parameters at various levels of (geographic) granularity.
We downloaded a sample of parameters at the level of NUTS2 regions


Climate data
============

The climate data used here is from the dataset 'UDel_AirT_Precip', provided by the University of Delaware and retrieved
`via the NOAA/OAR/ESRL PSD data store
<https://www.esrl.noaa.gov/psd/data/gridded/data.UDel_AirT_Precip.html>`_.
Please see the website for details on terms of use and copyright.
We downloaded long-term montly means of surface air temperature and precipitation
as 'netCDF' files. This file format is popular in climate sciences, but little used elsewhere.
Luckily, :mod:`scipy.io` provides IO routines for netCDF files.


