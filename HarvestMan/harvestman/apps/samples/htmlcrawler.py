#!/usr/bin/env python

"""
htmlcrawler.py - Demonstrating custom crawler writing by
subscribing to events. This is a crawler which fetches
only web pages from the web.

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2008 Anand B Pillai
"""

import sys
import __init__
from harvestman.apps.spider import HarvestMan

class HtmlCrawler(HarvestMan):
    """ A crawler which fetches only HTML (webpage) pages """
    
    def include_this_link(self, event, *args, **kwargs):
        
        url = event.url
        if url.is_webpage():
            # Allow for further processing by rules...
            # otherwise we will end up crawling the entire
            # web, since no other rules will apply if we
            # return True here.
            return None
        else:
            return False

if __name__ == "__main__":
    spider=HtmlCrawler()
    spider.initialize()
    spider.bind_event('includelinks', spider.include_this_link)
    spider.main()
