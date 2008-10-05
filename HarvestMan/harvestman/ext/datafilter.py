# -- coding: utf-8
""" Data filter plugin example based on the
simulator plugin for HarvestMan. This
plugin changes the behaviour of HarvestMan
to only simulate crawling without actually
downloading anything. In addition, it shows 
how to get access to the data downloaded by the crawler,
to implement various kinds of data filters.

Author: Anand B Pillai <abpillai at gmail dot com>

Created Feb 7 2007  Anand B Pillai <abpillai at gmail dot com>
Modified Nov 2 2007 by: Nils Ulltveit-Moe <nils at u-moe dot no>


Copyright (C) 2007 Anand B Pillai

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

from harvestman.lib import hooks
from harvestman.lib.common.common import *

from HTMLParser import HTMLParser

class MyHTMLParser(HTMLParser):
    # Example on a HTML parser, to filter img tags

    def handle_starttag(self, tag, attrs):

        # This just prints the image tag and its attributes
        if tag=="img":
            print tag,attrs

def process_url(self, data):
    """ Post process url callback test """
    # This shows how to get access to the
    # downloaded HTML document that is being processed.
    # Data is either HTML document or None
    if data:
        p = MyHTMLParser()
        p.feed(data)

    return data

def save_url(self, urlobj):

    # For simulation, we need to modify the behaviour
    # of save_url function in HarvestManUrlConnector class.
    # This is achieved by injecting this function as a plugin
    # Note that the signatures of both functions have to
    # be the same.
    url = urlobj.get_full_url()
    self.connect(urlobj, True, self._cfg.retryfailed)

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

    # Dummy function that does not really write the mirrored files.
    hooks.register_plugin_function('connector:save_url_plugin', save_url)

    # Hook to get access to the downloaded data after process_url has been called.
    hooks.register_post_callback_method('crawler:fetcher_process_url_callback',
                                            process_url)
    # Turn off caching, since no files are saved
    cfg.pagecache = 0
    # Turn off header dumping, since no files are saved
    cfg.urlheaders = 0
    logconsole('Simulation mode turned on. Crawl will be simulated and no files will be saved.')
