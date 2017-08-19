from __future__ import absolute_import

from os import path

import jinja2
import json
import sqlalchemy as sa
from builtins import str

from ozelot import client
from . import models, pipeline

# global jinja2 environment
jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(path.join(path.dirname(__file__), 'templates')))

# global output directory, default is directory containing this file
out_dir = path.dirname(__file__)


def indicator_summary_table():
    """Export a table listing all NUTS2 regions with their (most current) data.

    Output is a CSV file and an Excel file, saved as 'characters.csv/.xlsx' in the output directory.
    """
    # a database client/session to run queries in
    cl = client.get_client()
    session = cl.create_session()

    # Query regions and indicators separately, join them in pandas

    query = session.query(models.NUTS2Region.name,
                          models.NUTS2Region.key,
                          models.NUTS2Region.id)
    df = cl.df_query(query).set_index('id')

    # For each EuroStat indicator, query latest available data year (varies between indicators)
    indicators = session.query(models.EuroStatIndicator.description,
                               models.EuroStatIndicator.id).all()
    for description, indicator_id in indicators:
        latest_year = session.query(sa.func.max(models.EuroStatValue.year)) \
            .filter(models.EuroStatValue.indicator_id == indicator_id) \
            .scalar()

        query = session.query(models.EuroStatValue.value,
                              models.EuroStatValue.region_id) \
            .filter(models.EuroStatValue.indicator_id == indicator_id) \
            .filter(models.EuroStatValue.year == latest_year)
        values = cl.df_query(query).set_index('region_id')['value']

        # rename series to description + year, join to data table
        values.name = description + ' ' + str(latest_year)
        df = df.join(values, how='left')

    # Query and join in weather indicators
    query = session.query(models.ClimateValue.region_id,
                          models.ClimateValue.value,
                          models.ClimateIndicator.description) \
        .join(models.ClimateIndicator)
    weather = cl.df_query(query).dropna(how='any')

    # pivot different indicators to columns, join to data table
    weather = weather.set_index(['region_id', 'description'])['value'].unstack()
    df = df.join(weather, how='left')

    # write output as both CSV and Excel; do not include index column
    df.to_csv(path.join(out_dir, "nuts2_values.csv"), encoding='utf-8', index=False)
    df.to_excel(path.join(out_dir, "nuts2_values.xlsx"), encoding='utf-8', index=False)

    session.close()


def eurominder_explorer():
    """Generate interactive data exploration tool

    Output is an html page, rendered to 'eurominder_explorer.html' in the output directory.

    Data structure (only relevant items are shown below):

    .. code-block:: none

        {
            "nuts2Features": [{"geometry": [<boundary geometry>],
                               "properties": { "NUTS_ID": "AT11" } },
                              {"geometry": [<boundary geometry>],
                               "properties": { "NUTS_ID": "AT12" } },
                              ...],

            "regionNames": {"AT11": "Burgenland",
                            "AT13": "Wien",
                            ...
                           },

            "indicatorDescriptions": {"000005": "some description",
                                      "000010": "another description",
                                      ...},

            "indicators": [ {"key": "AT11",
                             "000005 2010": 37.0
                             "000005 2011": 38.0
                             ...
                             "000010 2010": 1234.0
                             "000010 2011": 1235.0
                             ...
                             "Mean temperature (C) Apr-Sep": 16.0,
                             "Mean temperature (C) Oct-Mar": 9.0,
                             ...
                             },
                            {"key": "AT12",
                             "000005 2010: 19.0,
                             ..
                            },
                            ...
                         ]

            "ranges": {"000005": [10, 20],
                       "000010": [1234, 5678],
                       ...,
                       "Mean temperature (C) Apr-Sep": 16.0,
                       "Mean temperature (C) Oct-Mar": 9.0,
                       ...
                       },

            "years": ["1999", "2000", ...],

        }
    """
    # switch off some pandas warnings
    import pandas as pd
    pd.options.mode.chained_assignment = None

    # page template
    template = jenv.get_template("eurominder_explorer.html")

    # container for template context
    context = dict()

    # plot data
    data = dict()

    # a database client/session to run queries in
    cl = client.get_client()
    session = cl.create_session()

    #
    # query data
    #

    # get region names and keys
    query = session.query(models.NUTS2Region.key,
                          models.NUTS2Region.name).all()
    data['regionNames'] = {t[0]: t[1] for t in query}

    # get indicator descriptions
    query = session.query(models.EuroStatIndicator.number,
                          models.EuroStatIndicator.description)
    data['indicatorDescriptions'] = {t[0]: t[1] for t in query}

    # build options for HTML selector for selecting which indicator to show
    context['y_field_selector_options'] = ''
    context['x_field_selector_options'] = ''
    for i_field, number in enumerate(sorted(data['indicatorDescriptions'].keys())):
        description = data['indicatorDescriptions'][number]

        # first field is default option for y selector, second field for x selector
        y_selected = " selected=\"selected\"" if i_field == 0 else ""
        x_selected = " selected=\"selected\"" if i_field == 1 else ""

        context['y_field_selector_options'] += "<option value=\"{:s}\" {:s}>{:s}</option>" \
                                               "".format(number, y_selected, description)
        context['x_field_selector_options'] += "<option value=\"{:s}\" {:s}>{:s}</option>" \
                                               "".format(number, x_selected, description)

    # get all eurostats data
    query = session.query(models.EuroStatValue.value,
                          models.EuroStatValue.year,
                          models.EuroStatIndicator.number,
                          models.NUTS2Region.key) \
        .join(models.EuroStatIndicator) \
        .join(models.NUTS2Region)
    eurostat = cl.df_query(query)

    # reformat to list of value dicts per region, as described above
    data['indicators'] = []
    for region_key, region_data in eurostat.groupby('key'):
        region_data['str_id'] = region_data['number'] + ' ' + region_data['year'].apply(lambda x: str(x))
        value_dict = region_data.set_index('str_id')['value'].to_dict()
        value_dict['key'] = region_key
        data['indicators'].append(value_dict)

    # store min/max values per indicator across all years, to keep plot scales fixed on playback
    data['ranges'] = dict()
    for number, indicator_data in eurostat.groupby('number'):
        data['ranges'][number] = [indicator_data['value'].min(), indicator_data['value'].max()]

    # build options for year selector (also store options in a list, for playback control)
    data['years'] = sorted([str(y) for y in eurostat['year'].unique()])
    context['year_selector_options'] = ''
    for year in data['years']:
        year_selected = " selected=\"selected\"" if year == "2010" else ""
        context['year_selector_options'] += "<option {:s}>{:s}</option>".format(year_selected, year)

    # query climate data
    query = session.query(models.ClimateValue.value,
                          models.ClimateIndicator.description,
                          models.NUTS2Region.key) \
        .join(models.ClimateIndicator) \
        .join(models.NUTS2Region)
    climate = cl.df_query(query).set_index('key')

    # inject data into 'indicators' records
    for record in data['indicators']:
        try:
            # index by a list of keys to be sure to get back a DataFrame even for one matching record
            cdata = climate.loc[[record['key']]]
        except KeyError:
            # no data available
            continue

        for description, value in cdata.set_index('description')['value'].iteritems():
            record[description] = value

    # sorted list of climate descriptions
    data['climateDescriptions'] = sorted(list(climate['description'].unique()))

    # store ranges of climate indicators, lump summer and winter together (by stripping season indicator)
    # to get comparable scales
    climate['variable_description'] = climate['description'].map(lambda s: ' '.join(s.split()[:-1]))
    for variable_description, indicator_data in climate.groupby('variable_description'):
        r = [indicator_data['value'].min(), indicator_data['value'].max()]
        data['ranges'][variable_description + pipeline.CLIMATE_SEASON_SUFFIXES['winter']] = r
        data['ranges'][variable_description + pipeline.CLIMATE_SEASON_SUFFIXES['summer']] = r

    # inject GeoJSON polygons
    with open(pipeline.NUTS2GeoJSONInputFile().input_file) as in_file:
        nuts2_boundaries = json.load(in_file)
    data['nuts2Features'] = nuts2_boundaries['features']

    #
    # render template
    #

    # inject data
    context['data'] = json.dumps(data, indent=4)

    out_file = path.join(out_dir, "eurominder_explorer.html")
    html_content = template.render(**context)
    with open(out_file, 'w') as f:
        f.write(html_content)

    # done, clean up
    session.close()


# noinspection PyShadowingBuiltins
def all():
    """Wrapper function for running all analyses
    """
    indicator_summary_table()
    eurominder_explorer()
