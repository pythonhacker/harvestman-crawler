# -- coding: utf-8
"""
configparser.py - Module which contains routines to parse
the XML configuration file of HarvestMan

This module contains a single class HarvestManConfigParser which acts
as a class for parsing HarvestMan XML configuration files
using pyexpat.

This module is part of the HarvestMan program.

Author: Anand B Pillai <<abpillai at gmail dot com>>

Created xx-xx-xxxx  Anand

Added this comment header                         10-1-06 Anand
Fixes for handling URLs with '&amp;' correctly    10/1/06 jkleven 
Renamed class to HarvestManConfigParser and       11/04/07 Anand
module to configparser.

Copyright (C) 2004 Anand B Pillai.

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import os
import xml.parsers.expat
from common.macros import *

class HarvestManConfigParser(object):
    """ Class whose function is used to parse the XML configuration
    file of HarvestMan """
    
    def __init__(self, config):
        """ Overloaded __init__ method """
        
        self.cfg = config
        self._node = ''
        self._data = ''
        
    def start_element(self, name, attrs):
        """ Callback handler for StartElementHandler """
        
        # reset character and node data, we're starting new element
        self._data = ''
        
        if attrs:
            # If the element has attributes
            # it does not have CDATA. So set
            # curr elem to null.
            self._node = ''
            
            for key, value in attrs.iteritems():
                # Form key name in xml map
                xmlkey = "".join((name, "_", key))
                # Set value
                if self.cfg:
                    # print 'Setting option for',xmlkey,value,attrs                    
                    self.cfg.set_option_xml_attr(xmlkey, value, attrs)
                else:
                   print key, value
        else:
            # If element has no attributes, the
            # value will be in CDATA. Store the
            # element name so that we can use it
            # in cdata callback.
            self._node = name

    def end_element(self, name):
        """ Callback handler for EndElementHandler """
        
        # This is called after the closing tag of an XML element was found
        # When this is called we know that char_data now truly has all the data
        # that was between the element start and end tag.        
        
        # jkleven: 10/1/06 - this function exists because we weren't 
        # parsing strings in config file 
        # with '&amp;' (aka '&') correctly.  Now we are.
        
        if self._data != '':
            # This was an element with data between an opening and closing tag
            # ... now that we're guaranteed to have it all, lets add it to the config
            # print 'Setting option for %s %s ' % (self._node, self._data)
            if self.cfg:
                self.cfg.set_option_xml(self._node, self._data)
            else:
                print self._data
                
        # reset these because we'll be encountering a new element node 
        # name soon, and our char data will then be useless as well.
        self._node = ''
        self._data  = ''            
            
    def char_data(self, data):
        """ Callback handler for CharacterDataHandler """
        
        # This will be called after the
        # start element is called. Simply
        # record all the data passed in and
        # then in the end element callback
        # we will actually add the whole
        # string to the internal config structure

        self._data += data.strip()

def parse_xml_config_file(configobj, configfile):
    """ Function to parse an XML configuration file 'configfile'.
    The first argument is the configuration object of HarvestMan """

    # Create config parser
    c = HarvestManConfigParser(configobj)
    p = xml.parsers.expat.ParserCreate()

    p.StartElementHandler = c.start_element
    p.CharacterDataHandler = c.char_data
    p.EndElementHandler = c.end_element

    if not os.path.isfile(configfile):
        print 'Error: file %s does not exist' % configfile
        return CONFIG_FILE_DOES_NOT_EXIST
    
    try:
        p.Parse(open(configfile).read())
        return CONFIG_FILE_PARSE_OK
    except (IOError, OSError, xml.parsers.expat.ExpatError), e:
        print e
        return CONFIG_FILE_PARSE_ERROR
    
if __name__=="__main__":
    p = xml.parsers.expat.ParserCreate()
    c = HarvestManConfigParser(None)
    
    p.StartElementHandler = c.start_element
    p.CharacterDataHandler = c.char_data
    p.EndElementHandler = c.end_element

    try:
        p.Parse(open('config.xml').read())
    except xml.parsers.expat.ExpatError, e:
        print e
        
