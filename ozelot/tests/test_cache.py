"""Unit tests for :mod:`ozelot.cache`"""

import unittest
from os import path
import time
import requests
import datetime

from ozelot import config
from ozelot.cache import RequestCache, get_request_cache, reset_request_cache


class RequestCacheTest(unittest.TestCase):
    """Unit tests for :class:`ozelot.cache.RequestCache`
    """

    def setUp(self):
        # override test DB location to be next to this file
        config.REQUEST_CACHE_PATH = path.join(path.dirname(__file__), '.test_web_cache')
        # always get a new request cache (get_request_cache() would re-use cache from module-level variable)
        self.cache = RequestCache()

    def tearDown(self):
        self.cache.close()
        self.cache.clear()

    def test01(self):
        """Store and retrieve an URL
        """
        # an URL that changes its content every second
        url = "http://www.unixtimestamp.com/"

        # get content, wait a bit, then get it from the cache
        r1 = self.cache.get(url)
        queried_on = self.cache.get_timestamp(url)
        self.assertLess((datetime.datetime.now() - queried_on).total_seconds(), 1)
        time.sleep(1.5)
        r2 = self.cache.get(url)
        self.assertEqual(r1, r2)
        self.assertEqual(queried_on, self.cache.get_timestamp(url))

        # clear the cache contents, get URL again, should be different now
        self.cache.clear(url)
        r3 = self.cache.get(url)
        self.assertNotEqual(r1, r3)

    def test02(self):
        """Get a few URLs, selective clear, then clear all
        """
        url1 = "https://en.wikipedia.org/wiki/Berlin"
        url2 = "https://en.wikipedia.org/wiki/Hamburg"
        url3 = "https://en.wikipedia.org/wiki/Boston"
        self.cache.get(url1)
        self.cache.get(url2)
        self.cache.get(url3)

        # clear one URL
        self.cache.clear(url1)
        self.assertFalse(self.cache.has(url1))

        # try clearing a non-existent URL
        self.assertRaises(KeyError, self.cache.clear, "not://in.cache")

        # clear all URLs
        self.cache.clear()
        self.assertFalse(self.cache.has(url2))
        self.assertFalse(self.cache.has(url3))

    def test03(self):
        """Compare results when getting a page from the cache and directly
        """
        url = "https://static.vee24.com/"
        r1 = self.cache.get(url)
        r2 = requests.get(url).text
        self.assertEquals(r1, r2)

    def test04(self):
        """Get a non-existent URL, should not be stored in cache
        """
        url = "http://this.site.does.not.exist"
        self.assertRaises(RuntimeError, self.cache.get, url)
        self.assertFalse(self.cache.has(url))

    def test05(self):
        """When an option is set, also requests with errors are cached, but re-raise an error when retrieved
        """
        url = "http://this.site.does.not.exist"
        self.assertRaises(RuntimeError, self.cache.get, url, store_on_error=True)
        self.assertTrue(self.cache.has(url))
        self.assertRaises(RuntimeError, self.cache.get, url)

    def test06(self):
        """Test caching using an xpath to select content to cache
        """
        url = "https://en.wikipedia.org/wiki/Berlin"
        xpath = "//table[contains(@class, 'infobox geography')]"

        # get full page and xpath excerpt only
        full = self.cache.get(url)
        part = self.cache.get(url, xpath=xpath)

        self.assertTrue(self.cache.has(url))
        self.assertTrue(self.cache.has(url, xpath=xpath))
        self.assertLess(len(part), len(full))
        self.assertTrue(full.startswith('<!DOCTYPE html>'))
        self.assertTrue(part.startswith('<table'))

        # get again, from cache
        full = self.cache.get(url)
        part = self.cache.get(url, xpath=xpath)

        self.assertLess(len(part), len(full))
        self.assertTrue(full.startswith('<!DOCTYPE html>'))
        self.assertTrue(part.startswith('<table'))

    def test07a(self):
        """Clear xpath entry
        """
        url = "https://en.wikipedia.org/wiki/Berlin"
        xpath = "//table[contains(@class, 'infobox geography')]"

        # get full page and xpath excerpt only
        self.cache.get(url)
        self.cache.get(url, xpath=xpath)

        self.assertTrue(self.cache.has(url))
        self.assertTrue(self.cache.has(url, xpath=xpath))

        # clear xpath only
        self.cache.clear(url, xpath=xpath)
        self.assertTrue(self.cache.has(url))
        self.assertFalse(self.cache.has(url, xpath=xpath))

    def test07b(self):
        """Clear full query, keep xpath entry
        """
        url = "https://en.wikipedia.org/wiki/Berlin"
        xpath = "//table[contains(@class, 'infobox geography')]"

        # get full page and xpath excerpt only
        self.cache.get(url)
        self.cache.get(url, xpath=xpath)

        self.assertTrue(self.cache.has(url))
        self.assertTrue(self.cache.has(url, xpath=xpath))

        # clear xpath only
        self.cache.clear(url)
        self.assertFalse(self.cache.has(url))
        self.assertTrue(self.cache.has(url, xpath=xpath))

    def test08a(self):
        """Getting a non-existent node via xpath raises an exception (and does not store result)
        """
        url = "https://en.wikipedia.org/wiki/Berlin"
        xpath = "//thisnodedoesnotexist"

        self.assertRaises(RuntimeError, self.cache.get, url, xpath=xpath)
        self.assertFalse(self.cache.has(url, xpath=xpath))

    def test08b(self):
        """Getting a non-existent node via xpath raises an error, but result can be stored
        """
        url = "https://en.wikipedia.org/wiki/Berlin"
        xpath = "//thisnodedoesnotexist"

        self.assertRaises(RuntimeError, self.cache.get, url, xpath=xpath, store_on_error=True)
        self.assertTrue(self.cache.has(url, xpath=xpath))

    def test09a(self):
        """Rate limiting
        """
        url1 = "https://en.wikipedia.org/wiki/Berlin"
        url2 = "https://en.wikipedia.org/wiki/Hamburg"
        url3 = "https://en.wikipedia.org/wiki/Boston"
        start = datetime.datetime.now()
        self.cache.get(url1, rate_limit=5)
        self.cache.get(url2, rate_limit=5)
        self.cache.get(url3, rate_limit=5)
        end = datetime.datetime.now()

        self.assertGreaterEqual((end - start).total_seconds(), 10.)

    def test09b(self):
        """Complementary test for rate limiting
        """
        url1 = "https://en.wikipedia.org/wiki/Berlin"
        url2 = "https://en.wikipedia.org/wiki/Hamburg"
        url3 = "https://en.wikipedia.org/wiki/Boston"
        start = datetime.datetime.now()
        self.cache.get(url1)
        self.cache.get(url2)
        self.cache.get(url3)
        end = datetime.datetime.now()

        self.assertLess((end - start).total_seconds(), 10.)

    def test10(self):
        """Cache to the module-level singleton
        """
        url = "https://www.google.de"

        reset_request_cache()
        cache2 = get_request_cache()
        self.assertFalse(cache2.has(url))
        cache2.get(url)
        self.assertTrue(cache2.has(url))

        # get singleton instance
        cache3 = get_request_cache()
        self.assertTrue(cache3.has(url))
        cache3.close()

        # get another cache using the same file
        cache4 = RequestCache()
        self.assertTrue(cache4.has(url))
        cache4.close()

        reset_request_cache()

    def test11a(self):
        """Get non-existent time stamp
        """
        self.assertIsNone(self.cache.get_timestamp("not.yet.there"))

    def test11b(self):
        """Get time stamp from non-existent DB file
        """
        self.cache.close()
        self.cache.clear()
        self.assertIsNone(self.cache.get_timestamp("not.yet.there"))
