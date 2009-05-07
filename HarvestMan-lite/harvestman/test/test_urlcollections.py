# -- coding: utf-8
""" Unit test for urlcollections module

Created: Anand B Pillai <abpillai@gmail.com> Jul 18 2008

Copyright (C) 2008, Anand B Pillai.
"""

import test_base
import unittest

test_base.setUp()
from harvestman.lib.urltypes import *
from harvestman.lib.urlcollections import *
from harvestman.lib.urlparser import *

class TestHarvestManUrlCollections(unittest.TestCase):
    """ Unit test class for all classes in urltypes module """
    
    def test_urlcollections(self):
        srcurl = HarvestManUrl('http://www.foo.com',urltype=URL_TYPE_WEBPAGE)
        child_url1 = HarvestManUrl('url1.html',baseurl=srcurl)
        child_url2 = HarvestManUrl('url2.html',baseurl=srcurl)        
        child_css = HarvestManUrl('test.css',urltype=URL_TYPE_STYLESHEET, baseurl=srcurl)        

        indices = [obj.index for obj in (child_url1, child_url2, child_css)]
        indices.sort()
        
        coll = HarvestManAutoUrlCollection(srcurl)
        coll.addURL(child_url1)
        coll.addURL(child_url2)
        coll.addURL(child_css)

        assert(coll.getSourceURL()==srcurl.index)
        urlindices = coll.getAllURLs()
        urlindices.sort()

        assert(urlindices == indices)
        assert(coll.getURLs(HarvestManStyleContext)==[child_css.index])
        assert(coll.getURLs(HarvestManPageContext)==[child_url1.index, child_url2.index])        

        # Now for a stylesheet containing URLs
        srccss = HarvestManUrl('http://www.foo.com/style.css',urltype=URL_TYPE_STYLESHEET)
        css_url1 = HarvestManUrl('cssurl1.html',baseurl=srccss)
        css_url2 = HarvestManUrl('cssurl2.html',baseurl=srccss)        
        css_css = HarvestManUrl('test.css',urltype=URL_TYPE_STYLESHEET, baseurl=srccss)

        indices = [obj.index for obj in (css_url1, css_url2, css_css)]
        indices.sort()

        coll = HarvestManAutoUrlCollection(srccss)
        coll.addURL(css_url1)
        coll.addURL(css_url2)
        coll.addURL(css_css)
        assert(coll.getSourceURL()==srccss.index)
        urlindices = coll.getAllURLs()
        urlindices.sort()

        assert(urlindices == indices)
        assert(coll.getURLs(HarvestManCSS2Context)==[css_css.index])
        assert(coll.getURLs(HarvestManCSSContext)==[css_url1.index, css_url2.index])                


def run(result):
    return test_base.run_test(TestHarvestManUrlCollections, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrlCollections)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()
        
