# -- coding: utf-8
""" Unit test for connector module

Created: Anand B Pillai <abpillai@gmail.com> May 21 2008

Copyright (C) 2008, Anand B Pillai.
"""

import test_base
import unittest
import sys, os
import time
import random

test_base.setUp()
from lib.connector import HarvestManUrlConnector
from lib.urlparser import HarvestManUrl    
from lib.common.macros import *
from lib.common.common import objects

urls = ['http://www.google.com','http://www.yahoo.com','http://www.python.org', 'ftp.gnu.org']

class TestHarvestManUrlConnector(unittest.TestCase):
    """ Unit test class for HarvestManUrlConnector class """

    etag = ''
    lmt = ''

    # Turn caching etc off
    objects.config.pagecache = 0
    objects.config.rawsave = True
    
    def test_connect(self):
        conn = HarvestManUrlConnector()
        url = random.choice(urls)
        res = conn.connect(HarvestManUrl(url))
        error = conn.get_error()
        if error.number==0:        
            assert(res == CONNECT_YES_DOWNLOADED)
            assert(conn.get_content_length()>0)
            content_type = conn.get_content_type()
            assert(content_type == 'text/html')
            fo = conn.get_fileobj()
            assert(fo != None)
            assert(fo.get_data() == '')        
            # Since default is flushing to file, the file
            # object should not be None
            assert(fo.get_tmpfile() != None)
        else:
            print 'Error in fetching data, skipping tests...'
            
        # Now set connector to in-mem mode and test again
        objects.config.datamode = CONNECTOR_DATA_MODE_INMEM

        conn = HarvestManUrlConnector()
        url = random.choice(urls)
        res = conn.connect(HarvestManUrl(url))
        # There could be an error...
        error = conn.get_error()
        if error.number==0:
            assert(res == CONNECT_YES_DOWNLOADED)
            assert(conn.get_content_length()>0)
            content_type = conn.get_content_type()
            assert(content_type == 'text/html')
            fo = conn.get_fileobj()
            assert(fo != None)
            assert(fo.get_data() != '')
            assert(fo.get_tmpfile() == None)
        else:
            print 'Error in fetching data, skipping tests...'

    def test_saveurl(self):
        conn = HarvestManUrlConnector()
        url = random.choice(urls)
        res = conn.save_url(HarvestManUrl(url))
        if conn.get_error().number==0:
            assert(res==DOWNLOAD_YES_OK)
            if os.path.isfile('index.html'):
                os.remove('index.html')
        else:
            print 'Error in fetching data, skipping tests...'                

    def test_urltofile(self):
        
        objects.config.showprogress = False
        conn = HarvestManUrlConnector()
        url = random.choice(urls)
        res = conn.url_to_file(HarvestManUrl(url))
        if conn.get_error().number==0:
            assert(res==URL_DOWNLOAD_OK)
            if os.path.isfile('index.html'):
                os.remove('index.html')
        else:
            print 'Error in fetching data, skipping tests...'                
        
    def test_connfactory(self):
        pass

def run(result):
    return test_base.run_test(TestHarvestManUrlConnector, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrlConnector)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()
