
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
    prev_tag = ''
    tag_data = []
    count = 0
    
    def crawl_this_url(self, event, *args, **kwargs):
        
        url, url_string = event.url, event.url.origurl
        
        if url.is_webpage() and url_string.lower().find(self.prefix_link) != -1:
            return None
        else:
            return False

    def download_this_url(self, event, *args, **kwargs):
        
        url, url_string = event.url, event.url.origurl
        
        if url.is_webpage() and url_string.lower().find(self.prefix_link) != -1:
            return None
        else:
            return False        

    def parse_tag(self, event, tag, attrs, **kwargs):
        """ Parse tag """

        if tag.lower()=='a' and self.prev_tag=='td':
            self.count += 1
            print event.url,':',self.tag_data[-2:],'=>',attrs


        if self.count>=2:
            self.tag_data = []
            self.count = 0
            
        # Reset tag_data
        self.prev_tag = tag
        
        
    def parse_tag_data(self, event, tag, data, **kwargs):
        """ Parse specific tag data """

        if tag.lower()=='td':
            # Need to append tag data since there are two <td> elements i.e
            # 2 columns before the <a ...> tags come.
            self.tag_data.append(data)
            
            
        self.prev_tag = tag

if __name__ == "__main__":
    spider=HtmlTableCrawler()
    spider.init()
    
    cfg = spider.get_config()
    cfg.localise = 0
    # Need to fool web-site
    cfg.USER_AGENT = 'Firefox/v3.5'
    cfg.add(url='http://en.wikipedia.org/wiki/List_of_airports_by_IATA_code:_A')

    spider.register('before_crawl_url', spider.crawl_this_url)
    spider.register('before_download_url', spider.download_this_url)    
    spider.register('before_tag_data', spider.parse_tag_data)
    spider.register('before_tag_parse', spider.parse_tag)    

    cfg.setup()
    spider.main()
