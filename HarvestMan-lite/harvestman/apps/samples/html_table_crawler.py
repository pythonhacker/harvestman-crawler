
#!/usr/bin/env python

"""
html_table_crawler.py - Demonstrating custom crawler writing by
subscribing to events. This is a crawler which prints out
CDATA contained in <td> elements inside an HTML table
per page crawled.

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2010 Anand B Pillai
"""

import sys
import __init__
from harvestman.apps.spider import HarvestMan
from harvestman.lib import logger

class HtmlTableCrawler(HarvestMan):
    """ A crawler which fetches only HTML (webpage) pages """

    prefix_link = 'List_of_airports_by_IATA_code'.lower()
    
    def crawl_this_url(self, event, *args, **kwargs):
        
        url, url_string = event.url, event.url.get_full_url()

        if url.is_webpage() and url_string.lower().startswith(self.prefix_link):
            # Allow for further processing by rules...
            # otherwise we will end up crawling the entire
            # web, since no other rules will apply if we
            # return True here.
            return None
        else:
            return False

    def parse_tag_data(self, event, *args, **kwargs):
        """ Parse specific tag data """

        tag, data = kwargs['tag'], kwargs['data']
        
        if tag.lower()=='td':
            print 'URL=>',event.url,'Tag=>',tag,'Data=>',data

if __name__ == "__main__":
    spider=HtmlTableCrawler()
    spider.init()
    
    cfg = spider.get_config()
    cfg.localise = 0
    # Need to fool web-site
    cfg.USER_AGENT = 'Firefox/v3.5'
    cfg.add(url='http://en.wikipedia.org/wiki/List_of_airports_by_IATA_code:_A')
    spider.bind_event('before_craw_url', spider.crawl_this_url)
    spider.bind_event('before_tag_data', spider.parse_tag_data)

    cfg.setup()
    spider.main()
