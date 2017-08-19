"""ETL pipeline for project 'superheroes'
"""
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library

standard_library.install_aliases()

import json
# noinspection PyPackageRequirements
from lxml import html
import urllib.request, urllib.parse, urllib.error
from os import path
import re

import pandas as pd
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from ozelot.etl import tasks
from ozelot import cache, client, config
from . import models


class LoadEverything(tasks.ORMWrapperTask):
    """A top-level task to wrap the whole pipeline
    """

    def requires(self):
        yield LoadCharacters()
        yield LoadMovies()
        yield LoadMovieAppearances()
        yield InflationAdjustMovieBudgets()
        yield Tests()


class Tests(tasks.ORMWrapperTask):
    """A task wrapping all tests
    """

    def requires(self):
        yield TestUniverses()
        yield TestCharacters()
        yield TestMovies()
        yield TestMovieAppearances()


class LoadUniverses(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load all Marvel universes (realities)
    """

    object_classes = [models.Universe]

    def run(self):
        # make all requests via a cache instance
        request_cache = cache.get_request_cache()

        # DB session to operate in
        session = client.get_client().create_session()

        # clear completion flag for this task
        self.mark_incomplete()

        # get the list of all universe pages; default limit is 25,
        # currently (2017) there are about 2100 pages
        content = request_cache.get("http://marvel.wikia.com/api/v1/Articles/List/"
                                    "?category=Realities&limit=5000")

        # translate JSON response into a dictionary
        list_data = json.loads(content)

        # iterate over all pages, build a new Universe object per page
        for item in list_data['items']:
            # a new Universe object for this page
            universe = models.Universe()

            # get wiki page URL (is URL-quoted in the data, un-quote it)
            # noinspection PyUnresolvedReferences
            universe.url = urllib.parse.unquote(item['url'])

            # get page title = character name
            universe.name = item['title']

            # schedule the object for database inclusion.
            session.add(universe)

        # done, save all data, finalize task
        session.commit()
        session.close()
        self.mark_complete()


class TestUniverses(tasks.ORMTestTask):
    """Consistency checks for LoadUniverses
    """

    def requires(self):
        yield LoadUniverses()

    # noinspection PyComparisonWithNone
    def run(self):
        # initialize
        self.mark_incomplete()
        session = client.get_client().create_session()

        # more than 2000, less than 10000 objects
        count = session.query(models.Universe).count()
        assert count > 2000
        assert count < 10000

        # names and URLs are never empty
        assert session.query(models.Universe).filter(models.Universe.name == None).count() == 0
        assert session.query(models.Universe).filter(models.Universe.url == None).count() == 0

        # names and URLs are unique
        assert session.query(models.Universe.name.distinct()).count() == count
        assert session.query(models.Universe.url.distinct()).count() == count

        # cleanup
        session.close()
        self.mark_complete()


def get_attribute_data(doc):
    """Helper function: parse attribute data from a wiki html doc

    Args:
        doc (document parsed with lxml.html): parsed wiki page

    Returns:
        dict: attributes values and listed links, format ``{<key>: {'value': <value>, 'link': <link>}}``;
              only the first hyperlink listed in each attribute value is included
    """
    attributes = dict()
    for attribute_node in doc.xpath("//div[contains(@class, 'pi-data ')]"):
        # label node
        node = attribute_node.xpath(".//*[contains(@class, 'pi-data-label')]")[0]
        label = " ".join(node.itertext()).strip()

        # value node
        node = attribute_node.xpath(".//*[contains(@class, 'pi-data-value')]")[0]

        # get value, first link, and the link text
        value = " ".join(node.itertext()).strip()
        link_node = node.find('a')
        if link_node is not None:
            link = link_node.get('href')
            link_text = link_node.text
        else:
            link = None
            link_text = None

        # store result
        attributes[label] = dict(value=value,
                                 link=link,
                                 link_text=link_text)

    return attributes


class LoadCharacters(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load all characters from Marvel wikia
    """

    object_classes = [models.Character]

    def requires(self):
        yield LoadUniverses()

    def run(self):
        # make all requests via a cache instance
        request_cache = cache.get_request_cache()

        # DB session to operate in
        session = client.get_client().create_session()

        # clear completion flag for this task
        self.mark_incomplete()

        # get the list of all character pages; default limit is 25, currently (2017) there are about 50,000 pages
        # -- start documentation include: character-list-query
        content = request_cache.get("http://marvel.wikia.com/api/v1/Articles/List/"
                                    "?category=Characters&limit=100000")
        list_data = json.loads(content)
        # -- end documentation include: character-list-query

        # iterate over all pages, build a new Character object per page
        for item in list_data['items']:
            # limit ingestion to pre-defined universes, if desired (see project_config.py);
            # universe is given in character link, e.g. 'http://marvel.wikia.com/wiki/Anthony_Stark_(Earth-616)'
            # noinspection PyUnresolvedReferences
            if config.UNIVERSES is not None:
                universe = None
                match = re.search(r'\(.*?\)', item['url'])
                if match:
                    universe = match.group()[1:-1]

                # noinspection PyUnresolvedReferences
                if universe is None or universe not in config.UNIVERSES:
                    continue

            # -- start documentation include: character-page-query
            # retrieve article, keep main article content only, parse
            article = request_cache.get("http://marvel.wikia.com" + item['url'],
                                        xpath="//article[@id='WikiaMainContent']",
                                        rate_limit=0.5)
            doc = html.fromstring(article)
            # -- end documentation include: character-page-query

            # a new Character object for this page
            character = models.Character()

            # get wiki page URL (is URL-quoted in the data, un-quote it)
            # noinspection PyUnresolvedReferences
            character.url = urllib.parse.unquote(item['url'])

            # get page title = character name
            character.name = item['title']

            # parse all data attributes (the box on the right-hand side of the page) to a dict
            attributes = get_attribute_data(doc)

            # get universe name, link character to respective universe object
            try:

                # -- start documentation include: universe-object-relation
                universe = attributes['Universe']['value']

                # get associated universe object, set reference
                try:
                    universe_obj = session.query(models.Universe).filter(models.Universe.name == universe).one()
                    character.universe_id = universe_obj.id
                except NoResultFound:
                    config.logger.warn("No result found searching for universe: " + universe)
                except MultipleResultsFound:
                    config.logger.warn("Multiple results found searching for universe: " + universe)
                # -- end documentation include: universe-object-relation

                # if universe is given, try to strip ' (<universe>)' from the character name
                character.name = re.sub(r' *\(' + universe + '\)', '', character.name)
            except KeyError:
                # attribute not present, skip
                pass

            # get place of birth, create/link to Place object
            try:
                # -- start documentation include: place-object-relation
                # identify place of birth by first link given (string value for place of birth
                # may contain multiple places, e.g. city and state)
                pob_link = attributes['Place of Birth']['link']
                pob_label = attributes['Place of Birth']['link_text']

                if pob_link is not None and pob_label is not None:
                    try:
                        # try to get an existing object for the place
                        pob = session.query(models.Place).filter(models.Place.url == pob_link).one()
                    except NoResultFound:
                        # place does not exist yet, create it
                        pob = models.Place(name=pob_label,
                                           url=pob_link)
                        session.add(pob)

                        # after adding the object, we need to commit to the DB
                        # for the object to get its id! Otherwise id is None.
                        session.commit()

                    # link character to place of birth
                    character.place_of_birth_id = pob.id
                    # -- end documentation include: place-object-relation

            except KeyError:
                pass

            # set 'real name' - leave empty if 'Unknown' is given in the page
            try:
                real_name = attributes['Real Name']['value']
                if real_name.lower() != 'unknown':
                    character.real_name = real_name
            except KeyError:
                pass

            # same for 'occupation'
            try:
                occupation = attributes['Occupation']['value']
                if occupation.lower() != 'unknown':
                    character.occupation = occupation
            except KeyError:
                pass

            # same for 'gender'
            try:
                gender = attributes['Gender']['value']
                if gender.lower() != 'unknown':
                    character.gender = gender
            except KeyError:
                pass

            # parse weight, convert to kg;
            # usually weight value is given as 'NNN lbs (MMM kg)'
            try:
                weight_str = attributes['Weight']['value']
                match = re.search(r'(\d+) +lbs', weight_str)
                if match:
                    # get first matched group (weight in lbs)
                    character.weight = 0.453592 * int(match.group(1))
            except KeyError:
                pass

            # parse height, convert to m;
            # height should be given as "N'MM''", but we'll also try to find "NN foot/feet"
            try:
                height_str = attributes['Height']['value']

                # try feet/inch first
                match = re.search(r'(\d+)\' +(\d+)"', height_str)
                if match:
                    # convert to meters, store
                    character.height = 0.3048 * int(match.group(1)) + 0.0254 * int(match.group(2))
                else:
                    # try "NNN-feet/foot" or "NNN feet/foot"
                    match = re.search(r'(\d+)[ -]+f[oe][oe]t', height_str)
                    if match:
                        character.height = 0.3048 * int(match.group(1))
            except KeyError:
                pass

            # get first appearance: find table enclosing the string
            node = doc.xpath("//th[contains(text(), 'First Appearance')]/ancestor::table[1]")[0]
            if node is not None:
                # find first data value in the table
                data_node = node.xpath(".//td[contains(@class, 'pi-data-value')]")[0]
                if data_node is not None:
                    first_appearance = " ".join(data_node.itertext())
                    # parse year of first appearance, string format is like "Some Series  #3 ( November, 1994 )"
                    match = re.search(r'\(.*?(\d\d\d\d).*?\)', first_appearance)
                    if match:
                        # get first matched group (the year as string)
                        character.first_apperance_year = int(match.group(1))

            # get number of appearances: link text is "NNNN appearances..." or just "appearances" if there is just one
            node = doc.xpath("//a[contains(@href, '/Appearances')]")[0]
            if node is not None:
                words = node.text.strip().split()
                if words[0] != 'Appearances':
                    # number of appearances is first word; before converting to int strip any thousand-separator commas
                    character.number_of_appearances = int(words[0].replace(',', ''))
                else:
                    character.number_of_appearances = 1

            # store the character object
            session.add(character)

        # done, save all data, finalize task
        session.commit()
        session.close()
        self.mark_complete()


class TestCharacters(tasks.ORMTestTask):
    """Consistency checks for LoadCharacters
    """

    def requires(self):
        yield LoadCharacters()

    # noinspection PyComparisonWithNone
    def run(self):
        # initialize
        self.mark_incomplete()
        session = client.get_client().create_session()

        # more than 1000, less than 10000 objects
        count = session.query(models.Character).count()
        assert count > 1000
        assert count < 10000

        # some fields are never empty
        assert session.query(models.Character).filter(models.Character.name == None).count() == 0
        assert session.query(models.Character).filter(models.Character.url == None).count() == 0
        assert session.query(models.Character).filter(models.Character.number_of_appearances == None).count() == 0

        # URLs are unique
        assert session.query(models.Character.url.distinct()).count() == count

        # most genders are 'Male' or 'Female'
        assert session.query(models.Character) \
                   .filter(models.Character.gender.in_(['Male', 'Female'])) \
                   .count() > 0.95 * count

        # some fields are empty only for a few items
        assert session.query(models.Character) \
                   .filter(models.Character.real_name == None) \
                   .count() < 0.2 * count
        assert session.query(models.Character) \
                   .filter(models.Character.real_name == None) \
                   .count() < 0.1 * count
        assert session.query(models.Character) \
                   .filter(models.Character.universe_id == None) \
                   .count() < 0.1 * count
        assert session.query(models.Character) \
                   .filter(models.Character.first_apperance_year == None) \
                   .count() < 0.1 * count

        # first appearance years are reasonable
        years = session.query(models.Character.first_apperance_year).all()
        for year, in years:
            assert year is None or 1950 < year < 2020

        # weights are "reasonable" (there is a 25 ton character)
        weights = session.query(models.Character.weight).all()
        for weight, in weights:
            assert weight is None or 0.1 < weight < 30000

        # heights are "reasonable" (there is a 50 foot / 15 m character)
        heights = session.query(models.Character.height).all()
        for height, in heights:
            assert height is None or 0.1 < height < 20

        # cleanup
        session.close()
        self.mark_complete()


class IMDBMovieRatings(tasks.InputFileTask):
    """Input file for IMDB movie ratings, data manually extracted from IMDB

    Format: <imdb page url>, <rating>
    """

    @property
    def input_file(self):
        """Returns ``imdb_ratings.csv`` in the current directory
        """
        return path.join(path.dirname(__file__), 'imdb_ratings.csv')

    def load(self):
        """Load table

        Returns:
            pandas.DataFrame: loaded data
        """
        return pd.read_csv(self.input_file)


class LoadMovies(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load all movies from Marvel wikia
    """

    object_classes = [models.Movie]

    def requires(self):
        yield LoadCharacters()
        yield IMDBMovieRatings()

    def run(self):
        # make all requests via a cache instance
        request_cache = cache.get_request_cache()

        # DB session to operate in
        session = client.get_client().create_session()

        # clear completion flag for this task
        self.mark_incomplete()

        # load movie ratings from file
        ratings = IMDBMovieRatings().load().set_index('url')['rating']

        # get the page containing all movies
        movies_page = request_cache.get("http://marvel.wikia.com/wiki/Marvel_films",
                                        xpath="//article[@id='WikiaMainContent']")

        # find all links that contain '(...film)'; this results in duplicates, deal with those below
        movies_doc = html.fromstring(movies_page)
        movie_links = set(movies_doc.xpath("//a[contains(@href, 'film)')]"))

        # iterate over all links, build a new Movie object per page; don't import a movie twice
        seen_movies = set()
        for movie_node in movie_links:
            url = movie_node.get('href')

            if url in seen_movies:
                # seen already, skip
                continue

            if "action=edit" in url:
                # page does not exist yet, skip
                continue

            if not url.startswith("/wiki/"):
                # link to some other website, skip
                continue

            # not seen yet, continue
            seen_movies.add(url)

            # retrieve article, keep main article content only, parse
            article = request_cache.get("http://marvel.wikia.com" + url,
                                        xpath="//article[@id='WikiaMainContent']",
                                        rate_limit=0.5)
            doc = html.fromstring(article)

            # a new Movie object for this page
            movie = models.Movie()

            # store page URL and name (from node title)
            movie.url = url
            movie.name = movie_node.get('title')

            # parse all data attributes (the box on the right-hand side of the page) to a dict
            attributes = get_attribute_data(doc)

            # get release date year (take first four-digit number in the string)
            try:
                date_str = attributes['Release Date(s)']['value']
                match = re.search(r'\d\d\d\d', date_str)
                if match:
                    movie.year = int(match.group(0))
            except KeyError:
                pass

            # get budget, parse to number (find consecutive digits and commas, then extract digits only)
            try:
                budget_str = attributes['Budget']['value']
                match = re.search('[0-9,]+', budget_str)
                if match:
                    movie.budget = int(re.sub('[^0-9]*', '', match.group(0)))
                    if 'million' in budget_str:
                        movie.budget *= 1.e6
            except KeyError:
                pass

            # get imdb page link
            imdb_link_nodes = doc.xpath("//a[contains(@href, 'imdb.com/title')]")
            if len(imdb_link_nodes) > 0:
                # link found
                imdb_link = imdb_link_nodes[0].get('href')

                # # The following shows how movie ratings could be scraped from IMDB. However, the IMDB terms of use
                # # forbid the use of scrapers/robots. Therefore, the ratings were extracted manually for this example
                # # and stored in the file `imdb_ratings.csv` included in this example.
                # # Do NOT run the below code!
                #
                # # retrieve page, parse
                # imdb_page = request_cache.get(imdb_link,
                #                               rate_limit=1.0)
                # imdb_doc = html.fromstring(imdb_page)
                #
                # # extract rating
                # rating_node = imdb_doc.xpath("//span[@itemprop='ratingValue']")
                # if len(rating_node) > 0:
                #     movie.imdb_rating = float(rating_node[0].text)

                # assign the rating from the stored table
                if imdb_link in ratings:
                    movie.imdb_rating = ratings.loc[imdb_link]

            # store the movie object
            session.add(movie)

        # done, save all data, finalize task
        session.commit()
        session.close()
        self.mark_complete()


class TestMovies(tasks.ORMTestTask):
    """Consistency checks for LoadMovies
    """

    def requires(self):
        yield LoadMovies()
        yield InflationAdjustMovieBudgets()

    # noinspection PyComparisonWithNone
    def run(self):
        # initialize
        self.mark_incomplete()
        session = client.get_client().create_session()

        # more than 50, less than 200 objects
        count = session.query(models.Movie).count()
        assert count > 50
        assert count < 200

        # names, years and URLs are never empty
        assert session.query(models.Movie).filter(models.Movie.name == None).count() == 0
        assert session.query(models.Movie).filter(models.Movie.year == None).count() == 0
        assert session.query(models.Movie).filter(models.Movie.url == None).count() == 0

        # names and URLs are unique
        assert session.query(models.Movie.name.distinct()).count() == count
        assert session.query(models.Movie.url.distinct()).count() == count

        # years are reasonable
        years = session.query(models.Movie.year).all()
        for year, in years:
            assert year is None or 1940 < year < 2020

        # some fields are empty only for a few items
        assert session.query(models.Movie) \
                   .filter(models.Movie.budget == None) \
                   .count() < 0.5 * count
        assert session.query(models.Movie) \
                   .filter(models.Movie.imdb_rating == None) \
                   .count() < 0.5 * count

        # budgets are reasonable, inflation adjustment always increases amount
        budgets = session.query(models.Movie.budget, models.Movie.budget_inflation_adjusted).all()
        for budget, budget_inflation_adjusted in budgets:
            # noinspection PyTypeChecker
            assert budget is None or 1.e5 < budget < 500.e6
            # noinspection PyTypeChecker
            assert budget_inflation_adjusted is None or 1.e6 < budget_inflation_adjusted < 500.e6
            assert budget is None or budget <= budget_inflation_adjusted

        # ratings are reasonable
        ratings = session.query(models.Movie.imdb_rating).all()
        for rating, in ratings:
            assert rating is None or 1 < rating < 10

        # cleanup
        session.close()
        self.mark_complete()


class LoadMovieAppearances(tasks.ORMObjectCreatorMixin, tasks.ORMTask):
    """Load appearances of characters in movies.
    """

    object_classes = [models.MovieAppearance]

    def requires(self):
        yield LoadMovies()
        yield LoadCharacters()

    def run(self):
        """Run loading of movie appearances.

        The wiki page structure for this part cannot be easily handled by simple xpath queries.
        We need to iterate over the respective portion of the page and parse appearances.
        """

        # make all requests via a cache instance
        request_cache = cache.get_request_cache()

        # DB session to operate in
        session = client.get_client().create_session()

        # clear completion flag for this task
        self.mark_incomplete()

        # list of universes seen in character appearances
        universes = []

        # don't auto-flush the session for queries, this causes issues with the 'id' field of newly
        # created MovieAppearance instances
        with session.no_autoflush:

            # get all movies
            movies = session.query(models.Movie).all()

            # iterate over all movies and build appearance objects
            for movie in movies:

                # retrieve movie article, keep main article content only, parse
                article = request_cache.get("http://marvel.wikia.com" + movie.url,
                                            xpath="//article[@id='WikiaMainContent']",
                                            rate_limit=0.5)
                doc = html.fromstring(article)

                # find heading for appearances, this is a span inside an h2; go to the h2
                node = doc.xpath("//span[@id='Appearances']")[0]
                node = node.getparent()

                # Appearance type is given by <p><b>... some text ...</b></p> tags. Sometimes the first
                # group of appearances carries no such label, assume it's the featured characters.
                appearance_type = "Featured Characters"

                # walk along the tree; character lists are in <ul>s, labels in <p>s;
                # the next h2 ends the character listing
                node = node.getnext()
                while node is not None and node.tag != 'h2':
                    if node.tag == 'ul' and ('characters' in appearance_type.lower() or
                                                     'villains' in appearance_type.lower()):
                        # starts a new list of stuff; only enter here if the previous label was for characters;
                        # use iter() to iterate over all 'li' items (also those of nested lists)
                        for li in node.iter('li'):
                            # inside the list element, find all 'a's; iterate over child nodes, don't use iter(),
                            # since we want don't want to find 'a's of sub-elements in a nested list here
                            for a in li:
                                if a.tag != 'a':
                                    continue

                                # there are 'a's in the list that wrap imags, don't use these; also don't use
                                # links that lead to somewhere else than the wiki
                                if "image" in a.get("class", "") or not a.get("href").startswith("/wiki/"):
                                    continue

                                match = re.search(r'\(.*?\)', a.get('href'))
                                if match:
                                    universes.append(match.group()[1:-1])

                                # accept the first matching href, build a new appearance object, then skip to next li
                                try:
                                    character = session.query(models.Character) \
                                        .filter(models.Character.url == a.get("href")) \
                                        .one()

                                    # -- start documentation include: many-to-many-generation
                                    appearance = models.MovieAppearance(movie_id=movie.id,
                                                                        character_id=character.id,
                                                                        appearance_type=appearance_type)
                                    session.add(appearance)
                                    # -- end documentation include: many-to-many-generation

                                except NoResultFound:
                                    # none found, ignore
                                    pass

                                # break looping over 'a's once we have found one, go to next 'li'
                                break

                    elif node.tag == 'p':
                        # new character class (or label for locations, items, ...)
                        appearance_type = " ".join(node.itertext()).strip().strip(':').strip()
                    node = node.getnext()

        print("\nNumber of character appearances per universe: ")
        print(pd.Series(data=universes).value_counts())

        # done, save all data, finalize task
        session.commit()
        session.close()
        self.mark_complete()


class TestMovieAppearances(tasks.ORMTestTask):
    """Consistency checks for LoadCharacters
    """

    def requires(self):
        yield LoadMovieAppearances()

    # noinspection PyComparisonWithNone
    def run(self):
        # initialize
        self.mark_incomplete()
        session = client.get_client().create_session()

        # more than 200, less than 5000 objects
        count = session.query(models.MovieAppearance).count()
        assert count > 200
        assert count < 2000

        # some fields are never empty
        assert session.query(models.MovieAppearance).filter(models.MovieAppearance.character_id == None).count() == 0
        assert session.query(models.MovieAppearance).filter(models.MovieAppearance.movie_id == None).count() == 0

        # appearance types have known values
        assert session.query(models.MovieAppearance) \
                   .filter(models.MovieAppearance.appearance_type.in_(['Villains',
                                                                       'Supporting Characters',
                                                                       'Other Characters',
                                                                       'Featured Characters'])) \
                   .count() == count

        # cleanup
        session.close()
        self.mark_complete()


class ConsumerPriceIndexFile(tasks.InputFileTask):
    """Input file for consumer price index data.

    Downloaded from: https://data.bls.gov/timeseries/CUUR0000SA0

    Selected max date range (1913-2017), included yearly averages.
    """

    @property
    def input_file(self):
        """Returns ``ConsumerPriceIndex_bls.gov_1913-2017.xlsx`` in the current directory
        """
        return path.join(path.dirname(__file__), 'ConsumerPriceIndex_bls.gov_1913-2017.xlsx')

    def load(self):
        """Load table

        Keeps only rows with annual average defined (full year data available).

        Returns:
            pandas.DataFrame: loaded data
        """
        df = pd.read_excel(self.input_file, skiprows=11)
        df = df.dropna(subset=['Annual'])
        return df


class InflationAdjustMovieBudgets(tasks.ORMTask):
    """This task computes inflation-adjusted movie budgets

    Budgets are adjusted by the ratio of the consumer price index (CPI) in the latest available
    CPI year, relative to the CPI of the movie publication year. Result is stored in
    ``Movie.budget_inflation_adjusted``.
    """

    def clear(self):
        """Clear task output: remove value ``budget_inflation_adjusted`` from all :class:`Movie` objects.
        """
        self.mark_incomplete()
        session = client.get_client().create_session()

        movies = session.query(models.Movie)
        movies.update({'budget_inflation_adjusted': None})

        session.commit()
        session.close()

    def requires(self):
        yield LoadMovies()
        yield ConsumerPriceIndexFile()

    def run(self):
        """Compute and store inflation-adjusted movie budgets
        """
        self.mark_incomplete()
        session = client.get_client().create_session()

        # load CPI data
        cpi = ConsumerPriceIndexFile().load()

        # max year we have CPI data for
        max_cpi_year = cpi['Year'].max()

        # extract annual average only, index by year
        cpi = cpi.set_index('Year')['Annual']

        # process all movies
        for movie in session.query(models.Movie).all():
            # we can only compute an inflation-adjusted budget if we know the year and budget
            if movie.year is not None and movie.budget is not None:
                if movie.year > max_cpi_year:
                    # if movie is too new, don't inflation-adjust
                    movie.budget_inflation_adjusted = movie.budget
                else:
                    movie.budget_inflation_adjusted = movie.budget * cpi.loc[max_cpi_year] / cpi.loc[movie.year]

        # done, save all data, finalize task
        session.commit()
        session.close()
        self.mark_complete()
