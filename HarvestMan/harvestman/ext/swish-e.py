# -- coding: utf-8
""" Swish-e plugin to HarvestMan. This plugin modifies the
behaviour of HarvestMan to work as an external crawler program
for the swish-e search engine {http://swish-e.org}

The data format is according to the guidelines given
at http://swish-e.org/docs/swish-run.html#indexing.

Author: Anand B Pillai <abpillai at gmail dot com>

Created  Feb 8 2007     Anand B Pillai <abpillai at gmail dot com>
Modified Feb 17 2007    Anand B Pillai Modified logic to use callbacks
                                       instead of hooks. The logic is
                                       in a post callback registered
                                       at context crawler:fetcher_process_url_callback.

Copyright (C) 2007 Anand B Pillai

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import sys, os
import time

from lib import hooks
from lib.common.common import *
from types import StringTypes

urllist = []

def process_url(self, data):
    """ Post process url callback for swish-e """

    if (type(data) in StringTypes) and len(data):
        global urllist
        urllist.append(self._urlobject.get_full_url())
        
        try:
            data = data.encode('ascii', 'ignore')
            l = len(data)
            s = ''
            
            # Code which works for www.python.org/doc/current/tut/tut.html
            # and for swish-e.org/docs
            # if len(data) != len(data.strip()):
            #    data = data.strip()
            #    l = len(data) + 1

            add = 0
            if l != len(data.strip()):
                # print l, len(data.strip()), self._urlobject.get_full_url()
                data = data.strip()
                l = len(data) + 1
                # print l

            if self.wp.can_index:
                s ="Path-Name:%s\nContent-Length:%d\n\n%s" % (self._urlobject.get_full_url(),
                                                             l,
                                                             data)
                # Swish-e seems to be very sensitive to any additional
                # blank lines between content and headers. So stripping
                # the data of trailing and preceding newlines is important.
                # print data.strip()
                try:
                    print str(s)
                except IOError, e:
                    # global urllist
                    # open('err.out','w').write('\n'.join(urllist))
                    objects.queuemgr.endloop()

            return data
        except UnicodeDecodeError, e:
            # open('uni.out','a').write(self._urlobject.get_full_url() + '\n')
            return data

    return data

    
def apply_plugin():
    """ Apply the plugin - overrideable method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook/plugin function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.

    cfg = objects.config

    # Makes sense to activate the callback only if swish-integration
    # is enabled.
    hooks.register_post_callback_method('crawler:fetcher_process_url_callback',
                                        process_url)
    # Turn off caching, since no files are saved
    cfg.pagecache = 0
    # Turn off console-logging
    logger = objects.logger
    #logger.disableConsoleLogging()
    # Turn off session-saver feature
    cfg.savesessions = False
    # Turn off interrupt handling
    # cfg.ignoreinterrupts = True
    # No need for localising
    cfg.localise = 0
    # Turn off image downloading
    cfg.images = 0
    # Increase sleep time
    cfg.sleeptime = 1.0
    # sys.stderr = open('swish-errors.txt','wb')
    # cfg.maxtrackers = 2
    cfg.usethreads = 0
