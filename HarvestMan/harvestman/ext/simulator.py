# -- coding: utf-8
""" Simulator plugin for HarvestMan. This
plugin changes the behaviour of HarvestMan
to only simulate crawling without actually
downloading anything.

Author: Anand B Pillai <abpillai at gmail dot com>

Created Feb 7 2007  Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai
   
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

from lib import hooks
from lib.common.common import *

def save_url(self, urlobj):

    # For simulation, we need to modify the behaviour
    # of save_url function in HarvestManUrlConnector class.
    # This is achieved by injecting this function as a plugin
    # Note that the signatures of both functions have to
    # be the same.

    url = urlobj.get_full_url()
    self.connect(url, urlobj, True, self._cfg.retryfailed)

    return 6

def apply_plugin():
    """ All plugin modules need to define this method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.
    
    cfg = objects.config
    cfg.simulate = True
    cfg.localise = 0
    hooks.register_plugin_function('connector:save_url_plugin', save_url)
    # Turn off caching, since no files are saved
    cfg.pagecache = 0
    # Turn off header dumping, since no files are saved
    cfg.urlheaders = 0
    logconsole('Simulation mode turned on. Crawl will be simulated and no files will be saved.')
