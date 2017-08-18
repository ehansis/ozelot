"""Caching mechanisms
"""
from builtins import str
from builtins import object

from os import path, remove
import requests
import datetime
import time

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm.exc import NoResultFound
# noinspection PyPackageRequirements
from lxml import html

from ozelot import config, client
from ozelot.orm import base


# a singleton cache instance
_request_cache = None


# custom error codes for request errors
ERROR_CONNECTION_ERROR = 999
ERROR_XPATH_NOT_FOUND = 998


def reset_request_cache():
    """Clear singleton :class:`RequestCache` instance
    """
    global _request_cache

    if _request_cache is not None:
        _request_cache.close()
        _request_cache.clear()
        _request_cache = None


def get_request_cache():
    """Get a singleton :class:`RequestCache` instance
    """
    global _request_cache

    if _request_cache is None:
        _request_cache = RequestCache()

    return _request_cache


class CachedRequest(base.Base):
    """ORM object class for cached URL request data
    """

    url = Column(String(2048), index=True)
    xpath = Column(String(512), index=True)
    content = Column(String)
    status_code = Column(Integer)
    queried_on = Column(DateTime)


class RequestCache(object):
    """A simple cache for (HTTP) requests.

    Uses an SQLite DB (and a simple ORM) to store cached request results.

    .. warning:: This implementation is NOT thread-safe!
    """

    STATUS_CODE_SUFFIX = '___status_code'

    def __init__(self):
        """Initialize the cache
        """
        self.db_path = config.REQUEST_CACHE_PATH

        connection_string = "sqlite:///" + self.db_path

        # timestamp of last query
        self.last_query = None

        if path.exists(self.db_path):
            # if file exists, assume that the DB is initialized
            config.logger.debug("Opening an existing request cache file " + self.db_path)
            self.client = client.Client(connection_string=connection_string)
        else:
            # create and initialize a new request cache DB
            config.logger.debug("Creating a new request cache file " + self.db_path)
            self.client = client.Client(connection_string=connection_string)
            CachedRequest().create_table(self.client)

        self.session = self.client.create_session()

    def __del__(self):
        """Clean up - close DB connection
        """
        self.close()

    def close(self):
        """Close the cache's DB
        """
        if self.session is not None:
            self.session.close()
            self.session = None

    def _query(self, url, xpath):
        """Base query for an url and xpath

        Args:
            url (str): URL to search
            xpath (str): xpath to search (may be ``None``)
        """
        return self.session.query(CachedRequest).filter(CachedRequest.url == url).filter(CachedRequest.xpath == xpath)

    def get(self, url, store_on_error=False, xpath=None, rate_limit=None):
        """Get a URL via the cache.

        If the URL exists in the cache, return the cached value. Otherwise perform the request,
        store the resulting content in the cache and return it.

        Throws a :class:`RuntimeError` if the request results in an error.

        Args:
            url (str): URL to request
            store_on_error (bool): If True, store request results in cache even if request results in an
                an error. Otherwise (default) do not store results when an error occurs. Cached content
                equals exception message.
            xpath (str): If given (default is None), parses the response content to html, searches the first
                node matching the given xpath and returns only that node (as UTF8-encoded html). Also, only
                stores this node's html in the cache. Raises a ``RuntimeError`` if the xpath cannot be found
                in the response.
            rate_limit (float): If not None (default), wait at least this many seconds between the previous
                request and the current one (this does not apply to cache hits).

        Returns:
            str: request content
        """

        try:
            # get cached request - if none is found, this throws a NoResultFound exception
            cached = self._query(url, xpath).one()
            config.logger.info("Request cache hit: " + url)

            # if the cached value is from a request that resulted in an error, throw an exception
            if cached.status_code != requests.codes.ok:
                raise RuntimeError("Cached request returned an error, code " + str(cached.status_code))
        except NoResultFound:
            config.logger.info("Request cache miss: " + url)

            # perform the request
            try:

                # rate limit
                if rate_limit is not None and self.last_query is not None:
                    to_sleep = rate_limit - (datetime.datetime.now() - self.last_query).total_seconds()
                    if to_sleep > 0:
                        time.sleep(to_sleep)

                self.last_query = datetime.datetime.now()

                response = requests.get(url)
                status_code = response.status_code
                # get 'text', not 'content', because then we are sure to get unicode
                content = response.text
                response.close()

                if xpath is not None:
                    doc = html.fromstring(content)
                    nodes = doc.xpath(xpath)
                    if len(nodes) == 0:
                        # xpath not found; set content and status code, exception is raised below
                        content = "xpath not found: " + xpath
                        status_code = ERROR_XPATH_NOT_FOUND
                    else:
                        # extract desired node only
                        content = html.tostring(nodes[0], encoding='unicode')

            except requests.ConnectionError as e:
                # on a connection error, write exception information to a response object
                status_code = ERROR_CONNECTION_ERROR
                content = str(e)

            # a new request cache object
            cached = CachedRequest(url=str(url),
                                   content=content,
                                   status_code=status_code,
                                   xpath=xpath,
                                   queried_on=datetime.datetime.now())

            # if desired, store the response even if an error occurred
            if status_code == requests.codes.ok or store_on_error:
                self.session.add(cached)
                self.session.commit()

            if status_code != requests.codes.ok:
                raise RuntimeError("Error processing the request, " + str(status_code) + ": " + content)

        return cached.content

    def clear(self, url=None, xpath=None):
        """Clear cache

        Args:
            url (str): If given, clear specific item only. Otherwise remove the DB file.
            xpath (str): xpath to search (may be ``None``)
        """
        if url is not None:
            query = self._query(url, xpath)
            if query.count() > 0:
                query.delete()
                self.session.commit()
            else:
                raise KeyError("Cannot clear URL, not in cache: " + str(url) + " xpath:" + str(xpath))
        else:
            # remove the DB file
            self.close()
            if path.exists(self.db_path):
                remove(self.db_path)

    def has(self, url, xpath=None):
        """Check if a URL (and xpath) exists in the cache

        If DB has not been initialized yet, returns ``False`` for any URL.

        Args:
            url (str): If given, clear specific item only. Otherwise remove the DB file.
            xpath (str): xpath to search (may be ``None``)

        Returns:
            bool: ``True`` if URL exists, ``False`` otherwise
        """
        if not path.exists(self.db_path):
            return False

        return self._query(url, xpath).count() > 0

    def get_timestamp(self, url, xpath=None):
        """Get time stamp of cached query result.

        If DB has not yet been initialized or url/xpath has not been queried yet, return None.

        Args:
            url (str): If given, clear specific item only. Otherwise remove the DB file.
            xpath (str): xpath to search (may be ``None``)

        Returns:
            datetime.datetime: cached response timestamp, None if not available
        """
        if not path.exists(self.db_path):
            return None

        if self._query(url, xpath).count() > 0:
            return self._query(url, xpath).one().queried_on
