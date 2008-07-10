# -- coding: utf-8
""" Unit test wrapper module

Created: Anand B Pillai <abpillai@gmail.com> Jun 02 2008

Copyright (C) 2008, Anand B Pillai.
"""

import unittest
import test_connector
import test_urlparser
import test_base

def run_all_tests():
    """ Run all unit tests in this folder """

    print 'Running test_connector...'
    suite = unittest.makeSuite(test_connector.TestHarvestManUrlConnector)
    result = unittest.TestResult()
    suite.run(result)
    print result.errors
    print result.failures    
    print 'Running test_urlparser...'    
    suite = unittest.makeSuite(test_urlparser.TestHarvestManUrl)
    suite.run(result)
    
    test_base.clean_up()
    return result

def run_test_connector():
    print 'Running test_connector...'
    suite = unittest.makeSuite(test_connector.TestHarvestManUrlConnector)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result

def run_test_urlparser():
    print 'Running test_urlparser...'
    suite = unittest.makeSuite(test_urlparser.TestHarvestManUrl)
    result = unittest.TestResult()
    suite.run(result)

    test_base.clean_up()    
    return result


if __name__=="__main__":
    print run_all_tests()
