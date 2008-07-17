# -- coding: utf-8
""" mirrors.py - Module which provides support for managing
mirrors for domains, for hget.

Author - Anand B Pillai <abpillai at gmail dot com>

Created,  Anand B Pillai 14/08/07.
Modified  Anand B Pillai 10/10/07  Added file mirror support
Modified  Anand B Pillai 12/11/07  Added logic to retry mirrors which
                                   did not fail wi th fatal error.
                                   Replaced duplicate mirroring code with
                                   HarvestManMirror class.
Modified Anand B Pillai 6/02/08    Added mirror search logic (Successfully
                                   download tested apache ant binary using
                                   findfiles.com mirrors).

Copyright (C) 2007 Anand B Pillai.
    
"""

import random
import urlparser
import connector
import re

from common.common import *
from common.macros import *
from common.singleton import Singleton
from pyparsing import *

def test_parse():
    print urls

class HTMLTableParser(object):

    def __init__(self):
        self.grammar = Literal("<table") + ZeroOrMore(Word(alphas) + Literal("=") + Word(alphanums + "%" + '"')) + Literal(">") + \
                       ZeroOrMore(Literal("<tr>") + SkipTo(Literal("</tr>"))) + SkipTo(Literal("</table>"))
        #self.grammar = Literal("<table") + ZeroOrMore(Word(alphas) + Literal("=") + Word(alphanums + "%" + '"')) + Literal(">") + \
        #               OneOrMore(Literal("<tr>") + ZeroOrMore(Literal("<td") + ZeroOrMore(Word(alphas) + Literal("=") + Word(alphanums + "%%" + '"')) + Literal(">") + SkipTo(Literal("</td>"))) + SkipTo(Literal("</tr>"))) + SkipTo(Literal("</table>"))

    def parse(self, data):

        # data='<table class="tinner" width="100%" cellspacing="0" cellpadding="0" cellpadding="4"><tr><td></td></tr></table>'
        for item in self.grammar.scanString(data):
            print item
        
        
        
class HarvestManMirror(object):
    """ Class representing a URL mirror """

    def __init__(self, url, absolute=False):
        self.url = url
        self.absolute = absolute
        # Url object
        self.urlobj = urlparser.HarvestManUrl(self.url)
        # By default mirror URLs are assumed to be directory URLs.
        # if this is an absolute file URL, then don't do anything
        if not absolute:
            self.urlobj.set_directory_url()
        
        # Reliability factor - FUTURE
        self.reliability = 1.0
        # Geo location - FUTURE
        self.geoloc = 0
        # Count of number of times
        # this mirror was used
        self.usecnt = 0

    def __str__(self):
        return self.url

    def __repr__(self):
        return str(self)
    
    def calc_relative_path(self, urlobj):

        relpath = urlobj.get_relative_url()

        # Global configuration object
        if objects.config.mirroruserelpath:
            if objects.config.mirrorpathindex:
                items = relpath.split('/')
                # Trim again....
                items = [item for item in items if item != '']
                relpath = '/'.join(items[cfg.mirrorpathindex:])
        else:
            # Do not use relative paths, return the filename
            # of the URL...
            relpath = urlobj.get_filename()

        if is_sourceforge_url(urlobj):
            relpath = 'sourceforge' + relpath
        else:
            if relpath[0] == '/':
                relpath = relpath[1:]
                
        return relpath

    
    def mirror_url(self, urlobj):
        """ Return mirror URL for the given URL """

        if not self.absolute:
            relpath = self.calc_relative_path(urlobj)
            newurlobj = urlparser.HarvestManUrl(relpath, baseurl=self.urlobj)
        else:
            newurlobj = self.urlobj
            
        # Set mirror_url attribute
        newurlobj.mirror_url = urlobj
        # Set another attribute indicating the mirror is different
        newurlobj.mirrored = True
        newurlobj.trymultipart = True

        self.usecnt += 1
        # print '\t=>',newurlobj.get_full_url()
        # logconsole("Mirror URL %d=> %s" % (x+1, newurlobj.get_full_url()))
        return newurlobj

    def new_mirror_url(self, urlobj):
        """ Return new mirror URL for an already mirrored URL """

        # Typically called when errors are seen with mirrors
        orig_urlobj = urlobj.mirror_url
        newurlobj = self.mirror_url(orig_urlobj)
        newurlobj.clength = urlobj.clength
        newurlobj.range = urlobj.range
        newurlobj.mindex = urlobj.mindex

        self.usecnt += 1
        
        return newurlobj

class HarvestManMirrorSearch(object):
    """ Search mirror sites for files """

    # Mirror sites and their search URLs
    sites = {'filewatcher':  ('http://www.filewatcher.com/_/?q=%s',),
             'freewareweb':  ('http://www.freewareweb.com/cgi-bin/ftpsearch.pl?q=%s',),
             'filesearching': ('http://www.filesearching.com/cgi-bin/s?q=%s&l=en',),
             'findfiles' : ('http://www.findfiles.com/list.php?string=%s&db=Mirrors&match=Exact&search=',) }
    
    quotes_re = re.compile(r'[\'\"]')
    filename_re = '%s[\?a-zA-Z0-9-_]*'

    def __init__(self):
        self.tried = []
        self.valid = ('findfiles',)
        self.cache = []


    def make_urls(self, grammar, data, filename):

        urls = []
        rc = re.compile(self.filename_re % filename)
        
        for match in grammar.scanString(data):

            if not match: continue
            if len(match) != 3: continue
            if len(match[0])==0: continue
            if len(match[0][-1])==0: continue         
            url = self.quotes_re.sub('', match[0][-1])
            if url not in urls:
                # Currently we cannot support FTP mirror URLs
                #if url.startswith('ftp://') or \
                #   url.startswith('http://') or \
                #   url.startswith('https://'):
                if url.startswith('http://') or \
                   url.startswith('https://'):                    
                
                    if url.endswith(filename):
                        urls.append(url)
                    elif rc.search(url):
                        # Prune any characters after filename
                        idx = url.find(filename)
                        if idx != -1: urls.append(url[:idx+len(filename)])
                    
        return urls

    def search_filewatcher(self, filename):

        # Note: this grammar could change if the site changes its templates
        grammar = Literal("<p>") + Literal("<big>") + Literal("<a") + Literal("href") + Literal("=") + \
                  SkipTo(Literal(">"))

        urls = []
        search_url = self.sites['filewatcher'][0] % filename
        
        conn = connector.HarvestManUrlConnector()
        data = conn.get_url_data(search_url)

        return self.make_urls(grammar, data, filename)

    def search_findfiles(self, filename):

        print 'Searching http://www.findfiles.com for mirrors of file %s...' % filename

        # Note: this grammar could change if the site changes its templates        
        content1 = Literal("<h1") + SkipTo(Literal("Advanced Search"))
        content2 = Literal("<a") + Literal("href") + Literal("=") + SkipTo(Literal(">"))
        
        search_url = self.sites['findfiles'][0] % filename
        
        conn = connector.HarvestManUrlConnector()
        data = conn.get_url_data(search_url)
        # print data
        matches = []
        
        for match in content1.scanString(data):
            matches.append(match)
            
        # There will be only one match
        if matches:
            data = matches[0][0][-1]
            idx1 = data.find('<table')
            if idx1 != -1:
                idx2 = data.find('</table>',idx1)
                if idx2 != -1:
                    data = data[idx1:idx2+8]
                    return self.make_urls(content2, data, filename)
                
        return []

    def search_freewareweb(self, filename):

        # TODO
        pass

    def search_filesearching(self, filename):

        # TODO
        pass    
    

    def can_search(self):
        """ Return whether we can search for new mirrors """
        
        # This queries whether we have used up all the mirror search sites
        self.tried.sort()
        l = list(self.valid)
        l.sort()
        return not (self.tried == l)
        
    def search(self, urlobj):
        filename = urlobj.get_filename()
        print 'Searching mirrors for %s...' % filename
        
        # Searching in other mirror search sites returns mostly
        # FTP urls. We can currently do mirror downloads only
        # for HTTP URLs.
        # return self.search_filewatcher(filename)
        for item in self.valid:
            if item not in self.tried:
                func = getattr(self,'search_' + item)
                self.tried.append(item)
                mirror_urls = func(filename)
                if mirror_urls:
                    mirrors = [HarvestManMirror(url, True) for url  in mirror_urls]
                    self.cache = mirrors
                    return mirrors
            
             
class HarvestManMirrorManager(Singleton):
    """ Mirror manager class for HarvestMan/Hget """
    
    # Sourceforge mirror information in the form
    # of (servername, Place, Country) tuples.
    sf_mirror_info = (('easynews', 'Arizona, USA'),
                      ('internap', 'CA, USA'),
                      ('superb-east','Virginia, USA'),
                      ('superb-west','Washington, USA'),
                      ('ufpr', 'Curitiba, Brazil'),
                      ('belnet', 'Brussels, Belgium'),
                      ('switch', 'Laussane, Switzerland'),
                      ('mesh', 'Deusseldorf, Germany'),
                      ('ovh', 'Paris, France'),
                      ('dfn', 'Berlin, Germany'),
                      ('heanet', 'Dublin, Ireland'),
                      ('garr', 'Bologna, Italy'),
                      ('surfnet', 'Amsterdam, The Netherlands'),
                      ('kent', 'Kent, UK'),
                      ('optusnet', 'Sydney, Australia'),
                      ('jaist', 'Ishikawa, Japan'),
                      ('nchc', 'Tainan, Taiwan'))
                   

    sf_mirrors = tuple([HarvestManMirror('http://%s.dl.sourceforge.net' % name[0]) for name in sf_mirror_info])

    sf_mirror_domains = tuple([mirror.urlobj.get_full_domain() for mirror in sf_mirrors])
    # print sf_mirror_domains

    def __init__(self):
        # List of mirror URLs loaded from a mirror file/other source
        self.filemirrors = []
        # Flag to perform mirror search
        self.mirrorsearch = False
        # List of current mirrors in use
        self.current_mirrors = []
        # List of used mirrors
        self.used_mirrors = []
        # List of mirrors which can be retried cuz they failed with
        # non-fatal errors
        self.mirrors_to_retry = []
        # List of mirrors which failed (Includes above list)
        self.failed_mirrors = []
        # Mirror retry attempts
        self.retries = 0
        # Used flag
        self.used = False
        # Mirror search object
        self.searcher = HarvestManMirrorSearch()
        
    def find_mirror(self, urlobj):

        mirrors = self.get_mirrors(urlobj, False)
        if mirrors == None:
            return
        
        for m in mirrors:
            if m.absolute:
                if m.urlobj == urlobj:
                    return m
            elif m.urlobj == urlobj.baseurl:
                return m
    
    def load_mirrors(self, mirrorfile):
        """ Load mirror information from the mirror file """

        if mirrorfile:
            for line in file(mirrorfile):
                url = line.strip()
                if url != '':
                    self.filemirrors.append(HarvestManMirror(url))
    
    def mirrors_available(self, urlobj):
        return (is_sourceforge_url(urlobj) or len(self.filemirrors) or self.mirrorsearch)
    
    def search_for_mirrors(self, urlobj, find_new = True):

        if not find_new:
            return self.searcher.cache
        
        if self.searcher.can_search():
            mirror_urls = self.searcher.search(urlobj)
            
            if mirror_urls:
                print '%d mirror URLs found, queuing them for multipart downloads...' % len(mirror_urls)
                return mirror_urls
            else:
                return []
        else:
            print 'Cannot search for new mirrors'
            return []
        
        pass
    
    def get_mirrors(self, urlobj, find_new=True):

        if is_sourceforge_url(urlobj):
            return self.sf_mirrors
        elif self.filemirrors:
            return self.filemirrors
        elif self.mirrorsearch:
            return self.search_for_mirrors(urlobj, find_new)
        
    def create_multipart_urls(self, urlobj, numparts):

        urlobjects = []
        relpath = ''

        mirrors = self.get_mirrors(urlobj)
        if len(mirrors) < numparts:
            numparts = len(mirrors)

        if len(mirrors)==0:
            print 'No mirrors found'
            return []
        elif len(mirrors)==1:
            # Only one mirror - this is of no use
            print 'Only single mirror found'
            return []
        
        # Get a random list of servers

        # Python seems to sometimes optimize these lists to tuples...
        # This produced an error in Cygwin python, so forcefully
        # coercing them to lists...
        self.current_mirrors = list(mirrors[:numparts])
        self.used_mirrors = list(self.current_mirrors[:])

        orig_url = urlobj.get_full_url()

        for x in range(numparts):
            mirror = self.current_mirrors[x]
            newurlobj = mirror.mirror_url(urlobj)
            urlobjects.append(newurlobj)

        return urlobjects
    
    def download_multipart_url(self, urlobj, clength, numparts, threadpool):
        """ Download URL multipart from supported servers """

        logconsole('Splitting download across mirrors...\n')

        # List of servers - note that we are not doing
        # any kind of search for the nearest servers. Instead
        # a random list is created.
        # Calculate size of each piece
        piecesz = clength/numparts

        # Calculate size of each piece
        pcsizes = [piecesz]*numparts
        # For last URL add the reminder
        pcsizes[-1] += clength % numparts 
        # Create a URL object for each and set range
        urlobjects = self.create_multipart_urls(urlobj, numparts)

        if (len(urlobjects)) == 0:
            return MIRRORS_NOT_FOUND
        
        prev = 0

        for x in range(len(urlobjects)):
            curr = pcsizes[x]
            next = curr + prev
            urlobject = urlobjects[x]
            urlobject.clength = clength
            urlobject.range = (prev, next-1)
            urlobject.mindex = x
            prev = next

            # Push this URL objects to the pool
            threadpool.push(urlobject)

        self.used = True
        
        return URL_PUSHED_TO_POOL

    def get_different_mirror_url(self, urlobj, urlerror):
        """ Return a different mirror URL for a (failed) mirror URL """
        
        mirror_url = self.find_mirror(urlobj)

        if mirror_url == None:
            return None
        
        if mirror_url not in self.failed_mirrors:
            self.failed_mirrors.append(mirror_url)
            
        # If not fatal error, append to mirrors_to_retry
        if not urlerror.fatal:
            if mirror_url not in self.mirrors_to_retry:
                self.mirrors_to_retry.append(mirror_url)

        mirrors = self.get_mirrors(urlobj)
        # Get the difference of the 2 sets
        newmirrors = list(set(mirrors).difference(set(self.used_mirrors)))
        # print 'New mirrors=>',newmirrors

        if newmirrors:
            extrainfo("Returning from new mirror list...")
            # Get a random one out of it...
            new_mirror = newmirrors[0]
            # Remove the old mirror and replace it with new mirror in
            # current_mirrors
            self.current_mirrors.remove(mirror_url)
            self.current_mirrors.append(new_mirror)
            self.used_mirrors.append(new_mirror)

        elif len(self.mirrors_to_retry)>1:
            extrainfo("Returning from mirrors_to_retry...")        
            # We don't want to go back to same mirror!
            new_mirror = self.mirrors_to_retry.pop(0)
            self.current_mirrors.remove(mirror_url)
            self.current_mirrors.append(new_mirror)
            if not new_mirror in self.used_mirrors:
                self.used_mirrors.append(new_mirror)
        else:
            return None

        self.retries += 1
        
        return new_mirror.new_mirror_url(urlobj)

    def reset(self):
        """ Reset the state """

        self.current_mirrors = []
        self.used_mirrors = []
        self.mirrors_to_retry = []

    def get_stats(self):
        """ Provide statistics """

        statsd = {}
        statsd['filemirrors'] = len(self.filemirrors)
        statsd['usedmirrors'] = len(self.used_mirrors)
        statsd['failedmirrors'] = len(self.failed_mirrors)
        statsd['retries'] = self.retries

        return statsd
    
    def print_stats(self):
        """ Print statistics to console """
        
        d = self.get_stats()

        info = ''
        fmirrors = d['filemirrors']
        if fmirrors:
            logconsole("\nPrinting mirror statistics...")
            info = "%d mirrors were loaded from file, " % fmirrors

        umirrors = d['usedmirrors']
        if umirrors:
            if info: info += ', '
            info += "%d mirrors were used " % umirrors
        else:
            return
        
        fldmirrors = d['failedmirrors']
        retries  = d['retries']
        
        if fldmirrors:
            if info: info += ', '            
            if fldmirrors>1:
                info += "%d mirrors failed" % fldmirrors
            else:
                info += "%d mirror failed" % fldmirrors
            
        logconsole(info)
        
def is_multipart_download_supported(urlobj):
    """ Check whether this URL (server) supports multipart downloads """
    
    return is_sourceforge_url(urlobj)

def is_sourceforge_url(urlobj):
    """ Is this a download from sourceforge ? """
    
    ret = (urlobj.domain in ('downloads.sourceforge.net', 'prdownloads.sourceforge.net') or \
           urlobj.get_full_domain() in HarvestManMirrorManager.sf_mirror_domains )

    return ret

if __name__ == "__main__":
    import config
    import logger
    import datamgr
    
    SetAlias(config.HarvestManStateObject())
    cfg = objects.config
    cfg.verbosity = 5
    SetAlias(logger.HarvestManLogger())
    SetLogSeverity()
    SetAlias(datamgr.HarvestManDataManager())
    
    search = HarvestManMirrorSearch()
    print search.search(urlparser.HarvestManUrl('http://pv-mirror02.mozilla.org/pub/mozilla.org/firefox/releases/2.0.0.11/linux-i686/en-US/firefox-2.0.0.11.tar.gz'))

