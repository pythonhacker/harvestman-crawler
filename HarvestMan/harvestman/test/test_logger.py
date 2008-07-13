# -- coding: utf-8
""" Unit test for logger module

Created: Anand B Pillai <abpillai at gmail.com> Jul 11 2007

Copyright (C) 2003-2008, Anand B Pillai.
"""

import test_base
import unittest
import sys, os

test_base.setUp()
from lib import logger

filename1='harvestman-test1.log'
filename2='harvestman-test1.log'

class TestHarvestManLogger(unittest.TestCase):
    """ Unit test class for HarvestManLogger class """

    mylogger = logger.HarvestManLogger.Instance()
    mylogger.make_logger()
    mylogger.disableConsoleLogging()
    
    def test_loglevel(self):

        mylogger = self.mylogger

        # Remove file if exists
        if os.path.isfile(filename1):
            os.remove(filename1)
            
        mylogger.addLogFile(filename1)
        
        p='HarvestMan'
        mylogger.debug("Test message 1",p)
        mylogger.extrainfo("Test message 2",p)
        mylogger.info("Test message 3",p)
        mylogger.warning("Test message 4",p)
        mylogger.error("Test message 5",p)
        mylogger.critical("Test message 6",p)
    
        # Verify file exists
        assert(os.path.isfile(filename1))
        # Check it has only 4 lines
        lines = open(filename1).readlines()
        assert(len(lines)==4)
        # Check that line 1 has 'INFO' in it
        assert(lines[0].find('INFO') != -1)
        
        # Remove this handler
        os.remove(filename1)
        mylogger.removeLogFile(filename1)
        
        # Add a new log file
        # Remove file if exists
        if os.path.isfile(filename2):
            os.remove(filename2)
            
        mylogger.addLogFile(filename2)
        mylogger.setLogSeverity(logger.EXTRAINFO)
        mylogger.debug("Test message 1",p)
        mylogger.extrainfo("Test message 2",p)
        mylogger.info("Test message 3",p)
        mylogger.warning("Test message 4",p)
        mylogger.error("Test message 5",p)
        mylogger.critical("Test message 6",p)

        # Verify file exists
        assert(os.path.isfile(filename2))
        # Check it has only 5 lines
        lines = open(filename2).readlines()
        assert(len(lines)==5)        

        # Check that line 1 has 'EXTRAINFO' in it
        assert(lines[0].find('EXTRAINFO') != -1)
        mylogger.removeLogFile(filename2)
        os.remove(filename2)
        
    def test_others(self):

        mylogger = self.mylogger
        # Test other things
         # Remove file if exists
        if os.path.isfile(filename1):
            os.remove(filename1)
            
        mylogger.addLogFile(filename1)
        mylogger.setPlainFormat()
        
        msg = "Test message"
        mylogger.info(msg)
        # Verify that the log file contains nothing more than
        # the message
        # Verify file exists
        assert(os.path.isfile(filename1))
        lines = open(filename1).readlines()
        assert(lines[0].strip()==msg)
        # Revert formatting
        mylogger.revertFormatting()
        mylogger.info(msg)
        lines = open(filename1).readlines()
        assert(lines[-1].strip()!=msg)
        os.remove(filename1)
        
if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManLogger)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()  
