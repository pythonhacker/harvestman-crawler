#!/usr/bin/env python

"""
searchingcrawler.py - Demonstrating custom crawler writing by
subscribing to events. This is a crawler which downloads
and crawls only pages which mention a certain keyword.

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2008 Anand B Pillai
"""

import sys
import re
import __init__
from apps.harvestmanimp import HarvestMan

class SearchingCrawler(HarvestMan):
    """ A crawler which fetches pages by searching for specific data
    This crawler can be run on a website to download only pages which
    contain a keyword or set of keywords or a regular expression """
    
    def __init__(self, regexp):
        self.rexp = regexp
        super(SearchingCrawler, self).__init__()
        
    def write_this_url(self, event, *args, **kwargs):

        if kwargs:
            data = kwargs['data']
            if self.rexp.search(data):
                return True
            else:
                return False
        else:
            return False

    def parse_this_link(self, event, *args):

        document = event.document
        url = event.url
        
        if not url.starturl and (self.rexp.search(document.content) == None):
            return False
        else:
            return True
        
    def crawl_this_link(self, event, *args):
        
        document = event.document
        url = event.url

        if document:
            # Don't forget to crawl the start URL!
            if not url.starturl:
                # Look for the keyword in the document keywords also...
                matches = [self.rexp.search(keyword) for keyword in document.keywords]
                if len(matches) or \
                   self.rexp.search(document.description) or \
                   self.rexp.search(document.content):
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

if __name__ == "__main__":
    # Search for strings "database" or "dbm" and save such pages only.
    spider=SearchingCrawler(re.compile(r'database|dbm',re.IGNORECASE))
    spider.initialize()
    config = spider.get_config()
    config.verbosity = 3

    spider.bind_event('beforecrawl', spider.crawl_this_link)
    spider.bind_event('beforeparse', spider.parse_this_link)
    spider.bind_event('writeurl', spider.write_this_url)
    spider.main()
