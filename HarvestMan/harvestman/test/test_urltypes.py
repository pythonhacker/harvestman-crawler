# -- coding: utf-8
""" Unit test for urltypes module

Created: Anand B Pillai <abpillai@gmail.com> Jul 17 2008

Copyright (C) 2008, Anand B Pillai.
"""

import test_base
import unittest

test_base.setUp()
from lib.urltypes import *

class TestHarvestManUrlTypes(unittest.TestCase):
    """ Unit test class for all classes in urltypes module """
    
    def test_urltypes(self):
        assert( URL_TYPE_ANY == 'generic')
        assert( URL_TYPE_WEBPAGE == 'webpage')
        assert( URL_TYPE_BASE == 'base')
        assert( URL_TYPE_ANCHOR == 'anchor')
        assert( URL_TYPE_QUERY == 'query')
        assert( URL_TYPE_FORM == 'form')
        assert( URL_TYPE_IMAGE == 'image')
        assert( URL_TYPE_STYLESHEET == 'stylesheet')
        assert( URL_TYPE_JAVASCRIPT == 'javascript')
        assert( URL_TYPE_JAPPLET == 'javaapplet')
        assert( URL_TYPE_JAPPLET_CODEBASE == 'appletcodebase')
        assert( URL_TYPE_FILE == 'file')
        assert( URL_TYPE_DOCUMENT == 'document')
        assert( URL_TYPE_ANY in ('generic','webpage'))
        assert( issubclass(URL_TYPE_ANCHOR, URL_TYPE_WEBPAGE))
        assert( issubclass(URL_TYPE_BASE, URL_TYPE_WEBPAGE))    
        assert( URL_TYPE_ANCHOR.isA(URL_TYPE_WEBPAGE))
        assert( URL_TYPE_ANCHOR.isA(URL_TYPE_ANY))
        assert( not URL_TYPE_IMAGE.isA(URL_TYPE_WEBPAGE))
        assert( URL_TYPE_ANY.isA(URL_TYPE_ANY))
        assert( URL_TYPE_IMAGE in ('image','stylesheet'))       

def run(result):
    return test_base.run_test(TestHarvestManUrlTypes, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrlTypes)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()
        
