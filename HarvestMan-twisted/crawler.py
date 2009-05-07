# A prototype of harvestman crawler using twisted matrix framework.
# NOTE: This doesn't crawl yet - but acts as a simple downloader
# which recreates URL structure on the disk.

# The goal of this is to create a prototype of a crawler using
# twisted philosophies and reusing minimal number of modules
# from harvestman code-base.

from twisted.web import client
from twisted.internet import defer, reactor
import pageparser
import urlparser
import sys, os

def saveUrl(url, base=None):

    try:
        hu = urlparser.HarvestManUrl(url, baseurl=base)
    except urlparser.HarvestManUrlError, e:
        print e
        # Dummy deferred object
        return defer.Deferred()

    directory = hu.get_local_directory()
    if not os.path.exists(directory):
        os.makedirs(directory)

    return client.downloadPage(hu.get_full_url(), hu.get_full_filename())

def handleAllResults(results):
    print results
    print 'Done.'
    reactor.stop()

def handleResult(result):
    print result
    
if __name__ == "__main__":
    urls = (open('urls.txt').read()).split('\n')
    downloaders = [saveUrl(url).addCallback(handleResult) for url in urls if url != '']
    # defer.DeferredList(downloaders, consumeErrors=True).addCallback(handleAllResults)
    reactor.run()
