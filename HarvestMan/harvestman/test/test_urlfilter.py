# -- coding: utf-8
""" Unit test for filters module

Created: Anand B Pillai <abpillai@gmail.com> Apr 17 2007

Mod   Anand         Sep 29 08      Fix for issue #24.

Copyright (C) 2007, Anand B Pillai.
"""

import test_base
import unittest
import sys, os

test_base.setUp()

from harvestman.lib.urlparser import HarvestManUrl, HarvestManUrlError
from harvestman.lib.filters import HarvestManUrlFilter


class TestHarvestManUrlFilter(unittest.TestCase):
    """ Unit test class for HarvestManUrlFilter class """

    hfilter = HarvestManUrlFilter([(u'-/images/*+/images/public/*', 1, '')],
                                  [(u'-jpg-png+doc', 0, '')],
                                  [(u'\d+\.doc$', 0, ''), (u'\d+\.pdf$',0,'')])
    
    url1 = HarvestManUrl('http://www.yahoo.com/photos/my photo.gif')
    url2 = HarvestManUrl('http://www.foo.com/images/photo.bmp')
    url3 = HarvestManUrl('http://www.foo.com/images/public/photo.bmp')
    url4 = HarvestManUrl('http://www.foo.com/images/public/image.png')
    url5 = HarvestManUrl('http://www.foo.com/images/public/image.jpg')
    url6 = HarvestManUrl('http://www.foo.com/photos/image.jpg')
    url7 = HarvestManUrl('http://www.foo.com/photos/image.png')        
    url8 = HarvestManUrl('http://website.com/documents/mydoc.pdf')
    url9 = HarvestManUrl('http://website.com/documents/mydoc-20.pdf')
    url10 = HarvestManUrl('http://website.com/documents/mydoc-25.doc')                        

    def test_urlfilter(self):

        f = self.hfilter

        # False
        assert(f.filter(self.url1)==False)
        # True
        assert(f.filter(self.url2)==True)
        # False - inclusion
        assert(f.filter(self.url3)==False)
        assert(f.filter(self.url4)==False)
        assert(f.filter(self.url5)==False)

        # True - extn
        assert(f.filter(self.url6)==True)
        assert(f.filter(self.url7)==True)

        # False
        assert(f.filter(self.url8)==False)

        # True - regex
        assert(f.filter(self.url9)==True)

        # False - inclusion
        assert(f.filter(self.url10)==False)
        
def run(result):
    return test_base.run_test(TestHarvestManUrlFilter, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrlFilter)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()            


