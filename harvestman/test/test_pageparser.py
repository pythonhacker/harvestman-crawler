# -- coding: utf-8
""" Unit test for pageparser module

Created: Anand B Pillai <abpillai@gmail.com> Jul 17 2008

Copyright (C) 2008, Anand B Pillai.
"""

import test_base
import unittest
import sys, os
import time

test_base.setUp()
from harvestman.lib.pageparser import HarvestManSimpleParser, HarvestManSGMLOpParser, HarvestManCSSParser
from harvestman.lib.urlparser import HarvestManUrl    
from harvestman.lib.common.macros import *
from harvestman.lib.urltypes import *
from sgmllib import SGMLParseError

curdir = os.path.abspath(os.path.dirname(test_base.__file__))

class Link:

    def __init__(self, typ, url):
        self.typ = typ
        self.url = url

    def __eq__(self, link):
        return link==self.url
        
def Linkify(links):

    Links = []
    for typ,url in links:
        Links.append(Link(typ, url))
    return Links

class TestHarvestManPageParser(unittest.TestCase):
    """ Unit test class for all classes in pageparser module """

    # Supported tags
    tags = ('a','frame','img','form','link','body','script',
            'applet','area','meta','embed','object','option')
    
    def test_simpleparser(self):
        # Test features (tags)
        for tag in self.tags:
            assert(tag in HarvestManSimpleParser.features)

        # Parse test
        p=HarvestManSimpleParser()
        p.feed(open(os.path.join(curdir, 'pass.html')).read())
        # There should be 29 links and 4 images
        assert(len(p.links)==29)
        assert(len(p.images)==4)
        assert(p.keywords==['crawler', 'spider', 'bot', 'web-bot', 'robot', 'offline', 'browser', 'web', 'internet', 'harvest', 'harvestman', 'http', 'browsing', 'searching', 'python', 'tools', 'aggregator', 'mining', 'intelligent', 'agents', 'agent-based computing', 'autonomous', 'documents'])
        assert(p.description=="Project page of the HarvestMan WebCrawler")
        assert(p.title=='The HarvestMan WebCrawler')
        
        link_urls = Linkify(p.links)
        # There should be a stylesheet link
        assert('style.css' in link_urls)
        # There will be an anchor link
        l = link_urls.index('download.html#latest')
        assert(link_urls[l].typ==URL_TYPE_ANCHOR)

        image_urls = Linkify(p.images)
        assert('images/HarvestMan_s.jpg' in image_urls)
        p.reset()
        try:
            # This page shoud fail the parser...
            p.feed(open(os.path.join(curdir, 'fail.html')).read())
            assert()
        except SGMLParseError:
            pass

    def test_sgmlopparser(self):

        # There is only one test, i.e the fail page
        # should parse with this parser.
        try:
            p=HarvestManSGMLOpParser()
            # This page shoud not fail the parser...
            p.feed(open(os.path.join(curdir, 'fail.html')).read())
            assert(len(p.links)==4)
        except Exception:
            assert()
            pass


    def test_cssparser(self):

        p = HarvestManCSSParser()
        p.feed(open(os.path.join(curdir, 'pass.css')).read())
        assert(p.links==['css1.css','css2.css','fancybullet.gif'])
        assert(p.csslinks==['css1.css','css2.css'])
        
def run(result):
    return test_base.run_test(TestHarvestManPageParser, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManPageParser)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()
        
