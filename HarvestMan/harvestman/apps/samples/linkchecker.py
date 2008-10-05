#!/usr/bin/env python

"""
linkchecker.py - Demonstrating custom crawling by overriding
events. This is a crawler class which reports broken links
in a website. Broken links are those which result in HTTP
404 (not found) errors.

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2008 Anand B Pillai
"""

import __init__
import sys

from harvestman.apps.spider import HarvestMan
from harvestman.lib.common.common import objects, logconsole

class LinkChecker(HarvestMan):
    """ A crawler which checks a website/directory for broken links """

    def __init__(self,):
        self.broken = []
        super(LinkChecker, self).__init__()

    def find_broken_links(self, event, *args, **kwargs):
        urldb = objects.datamgr.get_urldb()

        for node in urldb.preorder():
            urlobj = node.get()
            if urlobj.status == 404:
                self.broken.append(urlobj.get_full_url())

        # Write to a file
        baseurl = objects.queuemgr.get_base_url()
        fname = '404#' + str(hash(baseurl)) + '.txt'
        logconsole('Writing broken links to',fname)
        f = open(fname, 'w')
        f.write("Broken links for crawl starting with URL %s\n\n" % baseurl)
        for link in self.broken:
            f.write(link + '\n')
        f.close()

        return False
    
if __name__ == "__main__":
    spider=LinkChecker()
    spider.initialize()
    spider.bind_event('beforefinish', spider.find_broken_links)
    spider.main()
