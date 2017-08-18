from __future__ import absolute_import
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from os import path
import io
import json

import jinja2
from matplotlib import pyplot as plt
import seaborn
import sqlalchemy as sa

from ozelot import client, config
from . import models

# global jinja2 environment
jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(path.join(path.dirname(__file__), 'templates')))

# global output directory, default is directory containing this file
out_dir = path.dirname(__file__)


def character_summary_table():
    """Export a table listing all characters and their data

    Output is a CSV file and an Excel file, saved as 'characters.csv/.xlsx' in the output directory.
    """
    # a database client/session to run queries in
    cl = client.get_client()
    session = cl.create_session()

    # Define the query. Note that we need to rename the two joined-in name columns,
    # to make the labels intelligible and to not have two identical column names in the output.
    # Also, we need a left outer join on the place of birth (instead of the default left inner join)
    # if we want results for characters that have no place of birth set.
    query = session.query(models.Character,
                          models.Universe.name.label('universe'),
                          models.Place.name.label('place_of_birth')) \
        .join(models.Character.universe) \
        .outerjoin(models.Character.place_of_birth)

    # download all data as a pandas DataFrame, index it by the character ID
    characters = cl.df_query(query).set_index('id')

    # query the number of movie appearances per character
    query = session.query(sa.func.count(models.MovieAppearance.id).label('movie_appearances'),
                          models.MovieAppearance.character_id) \
        .group_by(models.MovieAppearance.character_id)

    appearances = cl.df_query(query).set_index('character_id')

    # join both tables, sort by name
    df = characters.join(appearances, how='left').sort_values(by='name')

    # drop the foreign key columns (have no meaning outside our DB)
    df = df.drop(['universe_id', 'place_of_birth_id'], axis=1)

    # write output as both CSV and Excel; do not include index column
    df.to_csv(path.join(out_dir, "characters.csv"), encoding='utf-8', index=False)
    df.to_excel(path.join(out_dir, "characters.xlsx"), encoding='utf-8', index=False)

    session.close()


def fig_to_svg(fig):
    """Helper function to convert matplotlib figure to SVG string

    Returns:
        str: figure as SVG string
    """
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    buf.seek(0)
    return buf.getvalue()


def pixels_to_inches(size):
    """Helper function: compute figure size in inches @ 72 dpi

    Args:
        size (tuple(int, int)): figure size in pixels

    Returns:
        tuple(int, int): figure size in inches
    """
    return size[0] / 72., size[1] / 72.


def plots_html_page():
    """Generate general statistics

    Output is an html page, rendered to 'plots_html_page.html' in the output directory.
    """
    # page template
    template = jenv.get_template("plots_html_page.html")

    # container for template context
    context = dict()

    # a database client/session to run queries in
    cl = client.get_client()
    session = cl.create_session()

    # general styling
    seaborn.set_style('whitegrid')

    #
    #  plot: number of superheroes, by year of first appearance
    #

    # just query all character data, do analysis in pandas
    query = session.query(models.Character)
    character_data = cl.df_query(query)

    # plot character appearances per year
    fig = plt.figure(figsize=pixels_to_inches((400, 300)))
    plt.plot(character_data.groupby('first_apperance_year')['id'].count(), '-o', c=seaborn.color_palette()[0])
    # labels and title
    plt.xlabel('Year')
    plt.ylabel('Number of first appearances')
    plt.title('Number of first character appearances per year')
    # render to svg string, store in template context
    context['first_appearances_per_year_svg'] = fig_to_svg(fig)
    plt.close(fig)

    #
    #  plot: number of movies, by year of publication
    #

    # just query all movie data, do analysis in pandas
    query = session.query(models.Movie)
    movie_data = cl.df_query(query)

    # plot movie publications per year
    fig = plt.figure(figsize=pixels_to_inches((400, 300)))
    plt.plot(movie_data.groupby('year')['id'].count(), '-o', c=seaborn.color_palette()[1])
    plt.xlabel('Year')
    plt.ylabel('Number of movies')
    plt.title('Number of movies per year')
    context['movies_per_year_svg'] = fig_to_svg(fig)
    plt.close(fig)

    #
    #  plot: average character appearances per movie per year
    #

    # query number of character appearances for each movie, together with the movie year
    query = session.query(sa.func.count(models.MovieAppearance.character_id).label('n_characters'),
                          models.Movie.id,
                          models.Movie.year) \
        .join(models.Movie) \
        .group_by(models.Movie.id, models.Movie.year)
    appearance_counts = cl.df_query(query)

    fig = plt.figure(figsize=pixels_to_inches((400, 300)))
    plt.plot(appearance_counts.groupby('year')['n_characters'].mean(), '-o', c=seaborn.color_palette()[2])
    plt.xlabel('Year')
    plt.ylabel('Average number of characters')
    plt.title('Average number of characters in a movie, per year')
    context['average_appearances_per_movie_svg'] = fig_to_svg(fig)

    #
    #  plots: average movie budget per year, with and without inflation adjustment
    #

    fig = plt.figure(figsize=pixels_to_inches((400, 300)))
    plt.plot(movie_data.groupby('year')['budget'].mean() / 1e6, '-o', c=seaborn.color_palette()[3])
    plt.xlabel('Year')
    plt.ylabel('Average budget in Mio Euro')
    plt.title('Average movie budget per year')
    plt.xlim(1980, plt.xlim()[1])
    context['budget_per_year_svg'] = fig_to_svg(fig)
    plt.close(fig)

    fig = plt.figure(figsize=pixels_to_inches((400, 300)))
    plt.plot(movie_data.groupby('year')['budget_inflation_adjusted'].mean() / 1e6, '-o', c=seaborn.color_palette()[4])
    plt.xlabel('Year')
    plt.ylabel('Average budget in Mio Euro')
    plt.title('Average movie budget per year, adjusted for inflation')
    plt.xlim(1980, plt.xlim()[1])
    context['budget_adjusted_per_year_svg'] = fig_to_svg(fig)
    plt.close(fig)

    #
    # render template
    #

    # add additional context data:
    # - html code for list of imported universes
    # noinspection PyUnresolvedReferences
    context['universes_list'] = ', '.join(config.UNIVERSES)

    out_file = path.join(out_dir, "plots_html_page.html")
    html_content = template.render(**context)
    with open(out_file, 'w') as f:
        f.write(html_content)

    # done, clean up
    plt.close('all')
    session.close()


def movie_network():
    """Generate interactive network graph of movie appearances

    Output is an html page, rendered to 'movie_network.html' in the output directory.
    """
    # page template
    template = jenv.get_template("movie_network.html")

    # container for template context
    context = dict()

    # a database client/session to run queries in
    cl = client.get_client()
    session = cl.create_session()

    #
    # query data
    #

    # get all Movies
    query = session.query(models.Movie.id,
                          models.Movie.name,
                          models.Movie.url,
                          models.Movie.budget_inflation_adjusted,
                          models.Movie.imdb_rating)
    movies = cl.df_query(query)

    # get all Movie Appearances
    query = session.query(models.MovieAppearance.movie_id,
                          models.MovieAppearance.character_id)
    appearances = cl.df_query(query)

    # get all Characters that have movie appearances
    query = session.query(models.Character.id,
                          models.Character.url,
                          models.Character.name) \
        .filter(models.Character.id.in_([int(i) for i in appearances['character_id'].unique()]))
    characters = cl.df_query(query)

    #
    # transform to network graph
    #

    graph = dict(nodes=[],
                 graph=[],  # this stays empty
                 links=[],
                 directed=False,
                 multigraph=True)

    # containers for lookups from movie/character IDs to node IDs
    movie_node_id = dict()
    character_node_id = dict()

    # normalization for movie node size: 100 = max budget
    movie_size_factor = 100. / movies['budget_inflation_adjusted'].max()

    # nodes for movies
    for _, data in movies.iterrows():
        movie_node_id[data['id']] = len(graph['nodes'])
        # noinspection PyTypeChecker
        graph['nodes'].append(dict(id=data['name'],
                                   size=max(5., data['budget_inflation_adjusted'] * movie_size_factor),
                                   score=data['imdb_rating'] / 10.,
                                   type='square',
                                   url="http://marvel.wikia.com" + data['url']))

    # nodes for characters
    for _, data in characters.iterrows():
        character_node_id[data['id']] = len(graph['nodes'])
        # noinspection PyTypeChecker
        graph['nodes'].append(dict(id=data['name'],
                                   size=10,
                                   type='circle',
                                   url="http://marvel.wikia.com" + data['url']))

    # links: movie appearances
    for _, data in appearances.iterrows():
        # noinspection PyTypeChecker
        graph['links'].append(dict(source=movie_node_id[data['movie_id']],
                                   target=character_node_id[data['character_id']]))

    context['graph'] = json.dumps(graph, indent=4)

    #
    # render template
    #

    out_file = path.join(out_dir, "movie_network.html")
    html_content = template.render(**context)
    with open(out_file, 'w') as f:
        f.write(html_content)

    # done, clean up
    plt.close('all')
    session.close()


# noinspection PyShadowingBuiltins
def all():
    """Wrapper function for running all analyses
    """
    character_summary_table()
    plots_html_page()
    movie_network()
