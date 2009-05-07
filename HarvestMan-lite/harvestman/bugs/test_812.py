# Demoing fix for EIAO bug #812.
# 812: Crawler does not identify links with arguments containing "#".
# Bug: http://trac.eiao.net/cgi-bin/trac.cgi/ticket/812

import sys
sys.path.append('..')
from lib import pageparser
from lib import config
from lib import logger
from lib.common.common import *
from lib import urltypes

class Url(str):

    def __init__(self, link):
        self.url = link[1]
        self.typ = link[0]

    def __eq__(self, item):
        return item == self.url
    
SetAlias(config.HarvestManStateObject())
SetAlias(logger.HarvestManLogger())

cfg = objects.config
cfg.getquerylinks = True

p = pageparser.HarvestManSGMLOpParser()
p.feed(open('soskut_hu_index.html').read())

urls = []
for link in p.links:
    urls.append(Url(link))

print urls

test_urls = ['?module=municip#MIDDLE',
             '?module=institutes#MIDDLE',
             '?module=regulations#MIDDLE',
             '?module=events#MIDDLE']

for turl in test_urls:
    print 'Asserting',turl
    assert(turl in urls)

for url in urls:
    if url in test_urls:
        print 'Asserting type of',turl        
        assert(url.typ ==  urltypes.URL_TYPE_ANY and url.typ != urltypes.URL_TYPE_ANCHOR)
