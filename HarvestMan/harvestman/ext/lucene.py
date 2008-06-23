# -- coding: utf-8
""" Lucene plugin to HarvestMan. This plugin modifies the
behaviour of HarvestMan to create an index of crawled
webpages by using PyLucene.

Author: Anand B Pillai <abpillai at gmail dot com>

Created  Aug 7 2007     Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import PyLucene
import sys, os
import time

from lib import hooks
from lib.common.common import *

class PorterStemmerAnalyzer(object):

    def tokenStream(self, fieldName, reader):

        result = PyLucene.StandardTokenizer(reader)
        result = PyLucene.StandardFilter(result)
        result = PyLucene.LowerCaseFilter(result)
        result = PyLucene.PorterStemFilter(result)
        result = PyLucene.StopFilter(result, PyLucene.StopAnalyzer.ENGLISH_STOP_WORDS)

        return result

def create_index(self, arg):
    """ Post download setup callback for creating a lucene index """

    moreinfo("Creating lucene index")
    storeDir = "index"
    if not os.path.exists(storeDir):
        os.mkdir(storeDir)

    store = PyLucene.FSDirectory.getDirectory(storeDir, True)
    
    self.lucene_writer = PyLucene.IndexWriter(store, PyLucene.StandardAnalyzer(), True)
    # Uncomment this line to enable a PorterStemmer analyzer
    # self.lucene_writer = PyLucene.IndexWriter(store, PorterStemmerAnalyzer(), True)    
    self.lucene_writer.setMaxFieldLength(1048576)
    
    count = 0

    urllist = []
    
    for node in self._urldb.preorder():
        urlobj = node.get()

        # Only index if web-page or document
        if not urlobj.is_webpage() and not urlobj.is_document(): continue
        
        filename = urlobj.get_full_filename()
        url = urlobj.get_full_url()

        try:
            urllist.index(urlobj.index)
            continue
        except ValueError:
            urllist.append(urlobj.index)

        if not os.path.isfile(filename): continue
        
        data = ''

        moreinfo('Adding index for URL',url)

        try:
            data = unicode(open(filename).read(), 'iso-8859-1')
        except UnicodeDecodeError, e:
            data = ''

        try:
            doc = PyLucene.Document()
            doc.add(PyLucene.Field("name", 'file://' + filename,
                                   PyLucene.Field.Store.YES,
                                   PyLucene.Field.Index.UN_TOKENIZED))
            doc.add(PyLucene.Field("path", url,
                                   PyLucene.Field.Store.YES,
                                   PyLucene.Field.Index.UN_TOKENIZED))
            if data and len(data) > 0:
                doc.add(PyLucene.Field("contents", data,
                                       PyLucene.Field.Store.YES,
                                       PyLucene.Field.Index.TOKENIZED))
            else:
                extrainfo("warning: no content in %s" % filename)

            self.lucene_writer.addDocument(doc)
        except PyLucene.JavaError, e:
            print e
            
        count += 1

    moreinfo('Created lucene index for %d documents' % count)
    moreinfo('Optimizing lucene index')
    self.lucene_writer.optimize()
    self.lucene_writer.close()
        
def apply_plugin():
    """ Apply the plugin - overrideable method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook/plugin function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.

    cfg = objects.config

    hooks.register_post_callback_method('datamgr:post_download_setup_callback',
                                        create_index)
    #logger.disableConsoleLogging()
    # Turn off session-saver feature
    cfg.savesessions = False
    # Turn off interrupt handling
    # cfg.ignoreinterrupts = True
    # No need for localising
    cfg.localise = 0
    # Turn off image downloading
    cfg.images = 0
    # Turn off caching
    cfg.pagecache = 0
