#!/usr/bin/env python

"""
taganalyzer.py - Demonstrating custom crawler writing by
subscribing to events. This is a crawler which allows
you to subscribe to HTML tag parsing events and to
take actions. 

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2008 Anand B Pillai
"""

import sys
import __init__

from harvestman.apps.spider import HarvestMan
from harvestman.lib.common.common import CaselessDict

class TagAnalyzingCrawler(HarvestMan):
    """ A crawler which can perform custom tag analysis """

    def __init__(self):
        # Dictionary for storing information
        self.d = {'images_no_alt': [], 'csslinks': []}
        super(TagAnalyzingCrawler, self).__init__()

    def write_this_url(self, event, *args, **kwargs):
        # Since we are doing only tag analysis, don't write anything..
        return False
    
    def analyze_this_tag(self, event, *args, **kwargs):

        tag = kwargs.get('tag','')
        attrs = kwargs.get('attrs',None)

        # This performs a check on images not having the 'alt' attribute...
        if tag.lower() == 'img':
            d = CaselessDict(attrs)
            if not 'alt' in d:
                imgurl = d['src'] or d['href']
                self.d['images_no_alt'].append(imgurl)

        
    def finish_event_cb(self, event, *args, **kwargs):

        print self.d
        info = open('tagsinfo.txt','w')
        
        if len(self.d['images_no_alt']):
            info.write('Image URLs without "alt" attribute\n')
            for url in self.d['images_no_alt']:
                info.write(url + '\n')

        info.close()

if __name__ == "__main__":
    spider=TagAnalyzingCrawler()
    spider.initialize()
    config = spider.get_config()
    # Disable caching
    config.pagecache = 0
    spider.bind_event('save_this_url', spider.write_this_url)
    spider.bind_event('before_tag_parse', spider.analyze_this_tag)
    spider.bind_event('before_finish_project', spider.finish_event_cb)
    spider.main()
