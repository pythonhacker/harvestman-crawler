# -- coding: utf-8
"""
appbase.py - Defines the base application class for
applications using the HarvestMan framework.

Author: Anand B Pillai <abpillai at gmail dot com>

Modification History

Created: Dec 12 2007       Anand B Pillai     By moving code from
                                              harvestman.py module.
"""

import sys, os
import __init__
import atexit

from harvestman.lib import config
from harvestman.lib import logger

from harvestman.lib.common.common import *

class HarvestManAppBase(object):
    """ Base application class for applications using the HarvestMan framework """

    # All applications using HarvestMan framework should derive from this class
    # or one of its subclasses.
    
    def __init__(self):
        """ Initializer """
        
        self.prepare()
        
    def prepare(self):
        """ Creates the state and logger objects and their aliases """
        
        # Init Config Object
        SetAlias(config.HarvestManStateObject.makeInstance())
        # Initialize logger object
        SetAlias(logger.HarvestManLogger())
        
    def process_plugins(self):
        """ Loads any plugin modules specified in configuration and process them """

        import harvestman.lib
        sys.path.append(harvestman.lib.__path__)
        from harvestman.lib import hooks

        plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__init__.__file__), '..', 'ext'))
        # print plugin_dir

        if os.path.isdir(plugin_dir):
            sys.path.append(plugin_dir)
            # Load plugins specified in plugins list
            for plugin in objects.config.plugins:
                # Load plugins
                try:
                    logconsole('Loading plugin %s...' % plugin)
                    M = __import__(plugin)
                    func = getattr(M, 'apply_plugin', None)
                    if not func:
                        logconsole('Invalid plugin %s, should define function "apply_plugin"!' % plugin)
                    try:
                        logconsole('Applying plugin %s...' % plugin)
                        func()
                    except Exception, e:
                        logconsole('Error while trying to apply plugin %s' % plugin)
                        logconsole('Error is:',str(e))
                        sys.exit(0)
                except (KeyError, ImportError), e:
                    logconsole('Error importing plugin module %s' % plugin)
                    logconsole('Error is:',str(e))
                    logconsole('Invalid plugin: %s !' % plugin)
                    hexit(0)

    def get_options(self):
        """ Reads program options from command line or configuration files """
        
        # Get program options
        objects.config.get_program_options()

    
