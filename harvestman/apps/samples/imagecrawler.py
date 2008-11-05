#!/usr/bin/env python

"""
imagecrawler.py - Demonstrating custom crawler writing by
subscribing to events. This is a crawler which downloads
only images from the web.

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2008 Anand B Pillai
"""

import sys
import __init__
from harvestman.apps.spider import HarvestMan
from harvestman.lib.common.macros import *

class ImageCrawler(HarvestMan):
    """ A crawler which saves only images to disk """
    
    def write_this_url(self, event, *args, **kwargs):
        
        url = event.url
        if url.is_image() or url.starturl:
            return True
        else:
            return False

    def include_links(self, event, *args, **kwargs):

        url = event.url
        if url.is_image():
            return True
        else:
            pass

if __name__ == "__main__":
    spider=ImageCrawler()
    spider.initialize()
    config = spider.get_config()
    config.robots = 0 # You might want to re-enable this!
    config.verbosity = 3
    # Need in-mem data mode to obtain data for
    # web-page URLs to parse them!
    config.datamode = CONNECTOR_DATA_MODE_INMEM 
    spider.bind_event('writeurl', spider.write_this_url)
    spider.bind_event('includelinks', spider.include_links)
    spider.main()
