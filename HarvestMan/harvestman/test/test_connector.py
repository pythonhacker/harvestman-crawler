# -- coding: utf-8
""" Unit test for connector module

Created: Anand B Pillai <abpillai@gmail.com> May 21 2008

Copyright (C) 2008, Anand B Pillai.
"""

import test_base
import unittest
import sys, os
import time

test_base.setUp()
from lib.connector import HarvestManUrlConnector
from lib.urlparser import HarvestManUrl    
from lib.common.macros import *

class TestHarvestManUrlConnector(unittest.TestCase):
    """ Unit test class for HarvestManUrlConnector class """

    etag = ''
    lmt = ''

    def test_connect(self):
        print 'test_connect...'
        conn = HarvestManUrlConnector()
        res = conn.connect(HarvestManUrl("http://www.python.org"))
        assert(res > 0)
        assert(conn.get_content_length()>0)
        self.__class__.etag = conn.get_etag()
        assert(self.__class__.etag != '')
        self.__class__.lmt = conn.get_last_modified_time()
        assert(self.__class__.lmt != '')

    def test_connect_etag(self):
        print 'test_connect_etag...'
        conn = HarvestManUrlConnector()
        res = conn.connect(HarvestManUrl("http://www.python.org"), etag=self.__class__.etag)
        # This should produce a 304 error
        assert(conn._error.number==304)
        assert(res==CONNECT_NO_UPTODATE)
        assert(conn.get_content_length()==0)


    def test_connect_lmt(self):
        print 'test_connect_lmt...'
        conn = HarvestManUrlConnector()
        lmt = time.mktime( time.strptime(self.__class__.lmt, "%a, %d %b %Y %H:%M:%S GMT"))
        res = conn.connect(HarvestManUrl("http://www.python.org"), lastmodified=lmt)
        # This should produce a 304 error
        assert(conn._error.number==304)
        assert(res==CONNECT_NO_UPTODATE)
        assert(conn.get_content_length()==0)

def run(result):
    return test_base.run_test(TestHarvestManUrlConnector, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrlConnector)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()
