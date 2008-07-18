# -- coding: utf-8
""" Unit test wrapper module

Created: Anand B Pillai <abpillai@gmail.com> Jun 02 2008

Copyright (C) 2008, Anand B Pillai.
"""

import unittest
import test_base
import glob
import os, sys

# FIXME: Add a unit-test log for failures with complete tracebacks
def run_all_tests():
    """ Run all unit tests in this folder """

    test_base.setUp()
    # Get location of this module
    curdir = os.path.abspath(os.path.dirname(test_base.__file__))
    sys.path.append(curdir)
    # Comment following line and uncomment line after it before checking in code...
    # test_modules = glob.glob(os.path.join(curdir, 'test_[!base|connector]*.py'))
    test_modules = glob.glob(os.path.join(curdir, 'test_[!base]*.py'))    
    result = unittest.TestResult()

    for module in test_modules:
        try:
            print 'Running unit-test for %s...' % module
            modpath, modfile = os.path.split(module)
            m = __import__(modfile.replace('.py',''))
            m.run(result)
        except ImportError,e :
            raise
            pass
        
    test_base.clean_up()
    return result

def run_test_connector():
    import test_connector

    print 'Running test_connector...'
    suite = unittest.makeSuite(test_connector.TestHarvestManUrlConnector)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result

def run_test_urlparser():
    import test_urlparser

    print 'Running test_urlparser...'
    suite = unittest.makeSuite(test_urlparser.TestHarvestManUrl)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result

def run_test_logger():
    import test_logger
    
    print 'Running test_logger...'
    suite = unittest.makeSuite(test_logger.TestHarvestManLogger)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result

def run_test_urltypes():
    import test_urltypes
    
    print 'Running test_urltypes...'
    suite = unittest.makeSuite(test_urltypes.HarvestManUrlTypes)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result

def run_test_pageparser():
    import test_pageparser
    
    print 'Running test_pageparser...'
    suite = unittest.makeSuite(test_pageparser.TestHarvestManPageParser)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result


if __name__=="__main__":
    print run_all_tests()
