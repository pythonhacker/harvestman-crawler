# -- coding: utf-8
"""
document.py - Provides HarvestManDocument class which provides
an abstraction over a webpage with attributes such as URL,
content, child URLs, HTTP headers, lastmodified value and
other attributes.

Created by Anand B Pillai <abpillai at gmail dot com> Feb 26 2008

Copyright (C) 2008 Anand B Pillai.
"""

from common.common import *

class HarvestManDocument(object):
    """ Web document class """

    def __init__(self, urlobj):
        # Store only index for conserving memory
        self.urlindex = urlobj.index
        # Also, list of children is actually list of
        # child indices to save memory...
        self.children = []
        self.content = ''
        self.content_hash = ''
        self.headers = {}
        # Only valid for webpages
        self.description = ''
        # Only valid for webpages        
        self.keywords = []
        # Only valid for webpages
        self.title = ''
        self.lastmodified = ''
        self.etag = ''
        #self.httpstatus = ''
        #self.httpreason = ''
        self.content_type = ''
        self.content_encoding = ''
        self.error = None
        
    def get_url(self):
        return objects.datamgr.get_url(self.urlindex)

    def set_url(self, urlobj):
        self.urlindex = urlobj.index

    def add_child(self, urlobj):
        self.children.append(urlobj.index)
        
    def get_links(self):
        # Links are already "normalized"
        return [objects.datamgr.get_url(index) for index in self.children]

    def get_content(self):
        return self.content

    def set_content(self, data):
        self.content = data
        
    def get_content_hash(self):
        return self.content_hash

    def get_zipped_content(self):
        # Return the content, gzipped
        pass

    def get_bzipped_content(self):
        # Return the content, bzipped
        pass

    

        
