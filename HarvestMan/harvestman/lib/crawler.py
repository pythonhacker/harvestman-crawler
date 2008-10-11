# -- coding: utf-8
""" crawler.py - Module which does crawling and downloading
    of urls from the web. This module is part of HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>

    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Modification history (Trimmed on Dec 14 2004)

    Aug 22 2006  Anand    Changes for fixing single-thread mode.
    Nov 9 2006   Anand    Added support to download imported stylesheets.

    Jan 2007     Anand    Support for META robot tags.
    Feb 17 2007  Anand    Modified return type of process_url in
                          HarvestManUrlFetcher class to return the data.
                          This is required for the modified swish-e
                          plugin.
    Feb 26 2007 Anand     Figured out the problem with 'disappearing' URLs.
                          The error is in the crawl_url method which was
                          checking whether a source URL was crawled. This
                          happens when a page redefines its base URL as
                          something else and when that URL is already crawled.
                          We need to modify our logic of applying base URLs.
    Mar 06 2007 Anand     Reset the logic of url-server to old one (only
                          crawlers send data to url server). This is because
                          sending both data to the server causes it to fail
                          in a number of ways.

                          NOTE: Decided not to use url server anymore since
                          it is not yet stable. I think I need to go the
                          Twisted way if this has to be done right.

    Apr 06 2007  Anand    Added check to make sure that threads are not
                          re-started for the same recurring problem.

    Oct 21 2007  Anand    Added states for the crawler state machine.
    
 Copyright (C) 2004 Anand B Pillai.
   
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import os, sys
import socket
import time
import threading
import random
import exceptions
import sha
from sgmllib import SGMLParseError

from harvestman.lib.common.common import *
from harvestman.lib.common.macros import *
from harvestman.lib.urltypes import *
from harvestman.lib.urlcollections import *

from harvestman.lib.methodwrapper import MethodWrapperMetaClass
from harvestman.lib.js.jsparser import JSParser, JSParserException

from harvestman.lib import urlparser
from harvestman.lib import pageparser
from harvestman.lib.common import netinfo 


# Defining pluggable functions
# Plugin name is the key and value is <class>:<function>

__plugins__ = { 'fetcher_process_url_plugin': 'HarvestManUrlFetcher:process_url',
                'crawler_crawl_url_plugin': 'HarvestManUrlCrawler:crawl_url' }

# Defining functions with pre & post callbacks
# Callback name is the key and value is <class>:<function>
__callbacks__ = { 'fetcher_process_url_callback' : 'HarvestManUrlFetcher:process_url',
                  'crawler_crawl_url_callback' : 'HarvestManUrlCrawler:crawl_url',
                  'fetcher_push_buffer_callback' : 'HarvestManUrlFetcher:push_buffer',
                  'crawler_push_buffer_callback' : 'HarvestManUrlCrawler:push_buffer',
                  'fetcher_terminate_callback' : 'HarvestManUrlFetcher:terminate',
                  'crawler_terminate_callback' : 'HarvestManUrlCrawler:terminate' }


class HarvestManThreadState(type):
    """ A metaclass for HarvestMan thread states """

    IDX = -1
    
    def __new__(cls, name, bases=(), dct={}):
        """ Overloaded Constructor """
        
        # Automatically increment index, without we bothering
        # to assign a number to the state class...
        cls.IDX += 1
        dct['index'] = cls.IDX
        return type.__new__(cls, name, bases, dct)

    def __init__(self, name, bases=(), dct={}):
        type.__init__(self, name, bases, dct)
        
    def __repr__(self):
        return '%d: %s' % (self.index, self.about)

    def __str__(self):
        return self.__name__
    
    def __eq__(self, number):
        """ Overloaded __eq__ method to allow
        comparisons with numbers """
        
        # Makes it easy to do things like
        # THREAD_IDLE == 0 in code.
        return self.index == number
    
def DEFINE_STATE(name, description):
    """ A factory function for defining thread state classes """

    # State classes are created and automatically injected in the module's
    # global namespace using the class name.
    globals()[name] = HarvestManThreadState(name, dct={'about': description})
     
# Thread states
DEFINE_STATE('THREAD_IDLE', "Idle thread, not running")
DEFINE_STATE('THREAD_STARTED', "Thread started to run")
DEFINE_STATE('CRAWLER_WAITING', "Crawler thread waiting for data")
DEFINE_STATE('FETCHER_WAITING', "Fetcher thread waiting for data")
DEFINE_STATE('CRAWLER_GOT_DATA', "Crawler thread got new list of URLs to crawl from the queue")
DEFINE_STATE('FETCHER_GOT_DATA', "Fetcher thread got new URL information from the queue")
DEFINE_STATE('FETCHER_DOWNLOADING', "Fetcher thread downloading data")
DEFINE_STATE('FETCHER_PARSING', "Fetcher thread parsing webpage to extract new URLs")
DEFINE_STATE('CRAWLER_CRAWLING', "Crawler thread crawling a page")
DEFINE_STATE('FETCHER_PUSH_URL', "Fetcher thread pushing URL to queue")
DEFINE_STATE('CRAWLER_PUSH_URL', "Crawler thread pushing URL to queue")
DEFINE_STATE('FETCHER_PUSHED_URL', "Fetcher thread pushed URL to queue")
DEFINE_STATE('CRAWLER_PUSHED_URL', "Crawler thread pushed URL to queue")
DEFINE_STATE('THREAD_SLEEPING', "Thread sleeping")
DEFINE_STATE('THREAD_SUSPENDED', "Thread is suspended on the state machine")
DEFINE_STATE('THREAD_DIED', "Thread died due to an error")
DEFINE_STATE('THREAD_STOPPED', "Thread stopped")

class HarvestManUrlCrawlerException(Exception):
    """ An exception class for HarvestManBaseUrlCrawler and its
    derived classes """
    
    def __init__(self, value):
        """ Overloaded __init__ method """
        
        self.value = value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return str(self.value)

class HarvestManBaseUrlCrawler( threading.Thread ):
    """ Base class to do the crawling and fetching of internet/intranet urls.
    This is the base class with no actual code apart from the threading or
    termination functions. """

    __metaclass__ = MethodWrapperMetaClass
    # Last error which caused the thread to die
    _lasterror = None
    
    def __init__(self, index, url_obj = None, isThread = True):
        # Index of the crawler
        self._index = index
        # Initialize my variables
        self._initialize()
        # Am i a thread
        self._isThread = isThread
        
        if isThread:
            threading.Thread.__init__(self, None, None, self._role + str(self._index))

    def _initialize(self):
        """ Initialise my state after construction """

        # End flag
        self._endflag = False
        # Download flag
        self._download = True
        self.url = None
        self.document = None
        # Number of loops
        self._loops = 0
        # Role string
        self._role = "undefined"
        # State of the crawler
        self.stateobj = objects.queuemgr.stateobj
        # Configuration
        self._configobj = objects.config
        # Local Buffer for Objects
        # to be put in q. Maximum size is 100
        self.buffer = Ldeque(100)
        # Flag for pushing to buffer
        self._pushflag = self._configobj.fastmode and (not self._configobj.blocking)
        # Resume flag - for resuming from a saved state
        self.resuming = False
        # Last exception
        self.exception = None
        # Sleep event
        if self._configobj.randomsleep:
            self.evnt = RandomSleepEvent(self._configobj.sleeptime)
        else:
            self.evnt = SleepEvent(self._configobj.sleeptime)            
        
    def __str__(self):
        return self.getName()

    def get_url(self):
        """ Return my url """

        return self.url

    def set_download_flag(self, val = True):
        """ Set the download flag """
        self._download = val

    def set_url_object(self, obj):
        """ Set the url object of this crawler """

        self.url = obj
        return True

    def set_index(self, index):
        self._index = index

    def get_index(self):
        return self._index
    
    def get_url_object(self):
        """ Return the url object of this crawler """

        return self.url

    def get_current_url(self):
        """ Return the current url """

        return self.url.get_full_url()
    
    def action(self):
        """ The action method, to be overridden by
        sub classes to provide action """

        pass
        
    def run(self):
        """ The overloaded run method of threading.Thread class """

        try:
            self.stateobj.set(self, THREAD_STARTED)
            self.action()
        except Exception, e:
        #    # print 'Exception',e,self
            self.exception = e
            self.stateobj.set(self, THREAD_DIED)                

    def stop(self):
        self.join()
        
    def join(self):
        """ Stop this crawler thread """

        self._endflag = True
        self.set_download_flag(False)
        threading.Thread.join(self, 1.0)
        self.stateobj.set(self, THREAD_STOPPED)
        # raise HarvestManUrlCrawlerException, "%s: Stopped" % self.getName()
    
    def sleep(self):

        self.stateobj.set(self, THREAD_SLEEPING)
        self.evnt.sleep()
        
    def crawl_url(self):
        """ Crawl a web page, recursively downloading its links """

        pass

    def process_url(self):
        """ Download the data for a web page or a link and
        manage its data """

        pass
        
    def push_buffer(self):
        """ Try to push items in local buffer to queue """

        # Try to push the last item
        stuff = self.buffer[-1]

        if objects.queuemgr.push(stuff, self._role):
            # Remove item
            self.buffer.remove(stuff)

class HarvestManUrlCrawler(HarvestManBaseUrlCrawler):
    """ The crawler class which crawls urls and fetches their links.
    These links are posted to the url queue """

    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManBaseUrlCrawler.__init__(self, index, url_obj, isThread)
        # Not running yet
        self.stateobj.set(self, THREAD_IDLE)
        
    def _initialize(self):
        HarvestManBaseUrlCrawler._initialize(self)
        self._role = "crawler"
        self.links = []

    def set_url_object(self, obj):

        # Reset
        self.links = []
        
        if not obj:
            return False

        prior, coll, document = obj
        url_index = coll.getSourceURL()
        url_obj = objects.datamgr.get_url(url_index)
        
        if not url_obj:
            return False
        
        self.links = [objects.datamgr.get_url(index) for index in coll.getAllURLs()]
        self.document = document
        
        return HarvestManBaseUrlCrawler.set_url_object(self, url_obj)

    def action(self):
        
        if self._isThread:
            
            if not self.resuming:
                self._loops = 0

            while not self._endflag:

                if not self.resuming:
                    if self.buffer and self._pushflag:
                        self.push_buffer()

                    self.stateobj.set(self, CRAWLER_WAITING)
                    obj = objects.queuemgr.get_url_data( "crawler" )
                    
                    if not obj:
                        if self._endflag: break

                        if self.buffer and self._pushflag:
                            debug('Trying to push buffer...')
                            self.push_buffer()

                        debug('OBJECT IS NONE,CONTINUING...',self)
                        continue

                    self.set_url_object(obj)

                    if self.url==None:
                        debug('NULL URLOBJECT',self)
                        continue

                    # We needs to do violates check here also
                    if self.url.violates_rules():
                        extrainfo("Filtered URL",self.url)
                        continue

                # Do a crawl to generate new objects
                # only after trying to push buffer
                # objects.
                self.crawl_url()
                self._loops += 1
                # Sleep for some time
                self.sleep()

                # If I had resumed from a saved state, set resuming flag
                # to false
                self.resuming = False
        else:
            self.process_url()
            self.crawl_url()


    def apply_url_priority(self, url_obj):
        """ Apply priority to url objects """

        cfg = objects.config
        
        # Set initial priority to previous url's generation
        url_obj.priority = self.url.generation

        # Get priority
        curr_priority = url_obj.priority

        # html files (webpages) get higher priority
        if url_obj.is_webpage():
            curr_priority -= 1

        # Apply any priorities specified based on file extensions in
        # the config file.
        pr_dict1, pr_dict2 = cfg.urlprioritydict, cfg.serverprioritydict
        # Get file extension
        extn = ((os.path.splitext(url_obj.get_filename()))[1]).lower()
        # Skip the '.'
        extn = extn[1:]

        # Get domain (server)
        domain = url_obj.get_domain()

        # Apply url priority
        if extn in pr_dict1:
            curr_priority -= int(pr_dict1[extn])

        # Apply server priority, this allows a a partial
        # key match 
        for key in pr_dict2:
            # Apply the first match
            if domain.find(key) != -1:
                curr_priority -= int(pr_dict2[domain])
                break
            
        # Set priority again
        url_obj.priority = curr_priority
        
        return HARVESTMAN_OK

    def crawl_url(self):
        """ Crawl a web page, recursively downloading its links """

        # Raise before crawl event...
        if objects.eventmgr.raise_event('beforecrawl', self.url, self.document)==False:
            extrainfo('Not crawling this url',self.url)
            return
        
        if not self._download:
            debug('DOWNLOAD FLAG UNSET!',self)
            return None

        self.stateobj.set(self, CRAWLER_CRAWLING)                    
        info('Fetching links for url', self.url)
        
        priority_indx = 0

        # print self.links
        
        for url_obj in self.links:

            # Check for status flag to end loop
            if self._endflag: break
            if not url_obj: continue

            url_obj.generation = self.url.generation + 1
            typ = url_obj.get_type()

            # Type based filtering
            if typ == 'javascript':
                if not self._configobj.javascript:
                    continue
            elif typ == 'javaapplet':
                if not self._configobj.javaapplet:
                    continue
                
            # Check for basic rules of download
            if url_obj.violates_rules():
                extrainfo("Filtered URL",url_obj.get_full_url())
                continue

            priority_indx += 1
            self.apply_url_priority( url_obj )

            if not objects.queuemgr.push( url_obj, "crawler" ):
                if self._pushflag: self.buffer.append(url_obj)

        objects.eventmgr.raise_event('aftercrawl', self.url, self.document)
        
class HarvestManUrlFetcher(HarvestManBaseUrlCrawler):
    """ This is the fetcher class, which downloads data for a url
    and writes its files. It also posts the data for web pages
    to a data queue """

    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManBaseUrlCrawler.__init__(self, index, url_obj, isThread)
        self._fetchtime = 0
        self.stateobj.set(self, THREAD_IDLE)
        
    def _initialize(self):
        HarvestManBaseUrlCrawler._initialize(self)
        self._role = "fetcher"

    def make_html_parser(self, choice=0):

        wp = None
        
        if choice==0:
            wp = pageparser.HarvestManSimpleParser()
        elif choice==1:
            try:
                wp = pageparser.HarvestManSGMLOpParser()
            except ImportError:
                wp = pageparser.HarvestManSimpleParser()


        # Enable/disable features
        if wp != None:
            for feat, val in self._configobj.htmlfeatures:
                # int feat,'=>',val
                if val: wp.enable_feature(feat)
                else: wp.disable_feature(feat)

        return wp
        
    def get_fetch_timestamp(self):
        """ Return the time stamp before fetching """

        return self._fetchtime
    
    def set_url_object(self, obj):

        if not obj: return False
        
        try:
            prior, url_obj = obj
            # url_obj = GetUrlObject(indx)
        except TypeError:
            url_obj = obj

        return HarvestManBaseUrlCrawler.set_url_object(self, url_obj)

    def action(self):
        
        if self._isThread:

            if not self.resuming:
                self._loops = 0            

            while not self._endflag:
                    
                if not self.resuming:
                    if self.buffer and self._pushflag:
                        debug('Trying to push buffer...')
                        self.push_buffer()

                    self.stateobj.set(self, FETCHER_WAITING)                    
                    obj = objects.queuemgr.get_url_data("fetcher" )
                    
                    if not obj:
                        if self._endflag: break

                        if self.buffer and self._pushflag:
                            debug('Trying to push buffer...')
                            self.push_buffer()

                        continue

                    if not self.set_url_object(obj):
                        debug('NULL URLOBJECT',self)
                        if self._endflag: break
                        continue

                # Process to generate new objects
                # only after trying to push buffer
                # objects.
                self.process_url()

                # Raise "afterfetch" event
                objects.eventmgr.raise_event('afterfetch', self.url)
                
                self._loops += 1

                # Sleep for some random time
                self.sleep()

                # Set resuming flag to False
                self.resuming = False
        else:
            self.process_url()
            self.crawl_url()

    def offset_links(self, links):
        """ Calculate a new list by applying any offset params
        on the list of links """

        n = len(links)
        # Check for any links offset params - if so trim
        # the list of links to the supplied offset values
        offset_start = self._configobj.linksoffsetstart
        offset_end = self._configobj.linksoffsetend
        # Check for negative values for end offset
        # This is considered as follows.
        # -1 => Till and including end of list
        # -2 => Till and including (n-1) element
        # -3 => Till and including (n-2) element
        # like that... upto -(n-1)...
        if offset_end < 0:
            offset_end = n - (offset_end + 1)
        # If we still get negative value for offset end
        # discard it and use list till end
        if offset_end < 0:
            offset_end = n

        # Start offset should not have negative values
        if offset_start >= 0:
            return links[offset_start:offset_end]
        else:
            return links[:offset_end]
        
    def process_url(self):
        """ This function downloads the data for a url and writes its files.
        It also posts the data for web pages to a data queue """

        data = ''
        # Raise "beforefetch" event...
        if objects.eventmgr.raise_event('beforefetch', self.url)==False:
            return 
        
        if self.url.qstatus==urlparser.URL_NOT_QUEUED:
            info('Downloading file for url', self.url.get_full_url())
            # About to fetch
            self._fetchtime = time.time()
            self.stateobj.set(self, FETCHER_DOWNLOADING)
            data = objects.datamgr.download_url(self, self.url)
            
        # Add webpage links in datamgr, if we managed to
        # download the url
        url_obj = self.url

        if self.url.is_webpage() and data:
            # Create a HarvestMan document with all data we have...

            # Create a document and keep updating it -this is useful to provide
            # information to events...
            document = url_obj.make_document(data, [], '', [])
            
            # Raise "beforeparse" event...
            if objects.eventmgr.raise_event('beforeparse', self.url, document)==False:
                return 
            
            # Check if this page was already crawled
            url = self.url.get_full_url()
            sh = sha.new(data)
            # Set this hash on the URL object itself
            self.url.pagehash = str(sh.hexdigest())

            extrainfo("Parsing web page", self.url)

            self.stateobj.set(self, FETCHER_PARSING)
        
            links = []

            # Perform any Javascript based redirection etc
            if self._configobj.javascript:
                skipjsparse = False
                # Raise "beforejsparse" event...
                if objects.eventmgr.raise_event('beforejsparse', self.url, document)==False:
                    # Don't return, skip this...
                    skipjsparse = True

                if not skipjsparse:
                    try:
                        parser = JSParser()
                        parser.parse(data)
                        if parser.locnchanged:
                            redirect_url = parser.getLocation().href
                            extrainfo("Javascript redirection to", redirect_url)
                            links.append((urlparser.URL_TYPE_ANY, redirect_url))

                        # DOM modification parsing logic is rudimentary and will
                        # screw up original page data most of the time!
                        
                        #elif parser.domchanged:
                        #    extrainfo("Javascript modified page DOM, using modified data to construct URLs...")
                        #    # Get new content
                        #    datatemp = repr(parser.getDocument())
                        #    # Somehow if data is NULL, don't use it
                        #    if len(datatemp) !=0:
                        #        data = datatemp
                        #    # print data
                    except JSParserException, e:
                        error("Javascript parsing error =>", e)            

                    # Raise "afterjsparse" event
                    objects.eventmgr.raise_event('afterjsparse', self.url, document, links=links)

            wp = self.make_html_parser()

            while True:
                try:
                    wp.reset()
                    wp.set_url(self.url)
                    wp.feed(data)
                    # Bug Fix: If the <base href="..."> tag was defined in the
                    # web page, relative urls must be constructed against
                    # the url provided in <base href="...">

                    if wp.base_url_defined():
                        url = wp.get_base_url()
                        if not self.url.is_equal(url):
                            debug("Base url defined, replacing",self.url)
                            # Construct a url object
                            url_obj = urlparser.HarvestManUrl(url,
                                                              URL_TYPE_BASE,
                                                              0,
                                                              self.url,
                                                              self._configobj.projdir)

                            # Change document
                            objects.datamgr.add_url(url_obj)
                            document.set_url(url_obj)

                    wp.close()
                    break
                except (SGMLParseError, IOError), e:
                    error('SGML parse error:',str(e))
                    error('Error in parsing web-page %s' % self.url)

                    if wp.typ==0:
                        # Parse error occurred with Python parser
                        debug('Trying to reparse using the HarvestManSGMLOpParser...')
                        wp = self.make_html_parser(choice=1)
                    else:
                        break
                except ValueError, e:
                    break
                except Exception, e:
                    break

            if self._configobj.robots:
                # Check for NOFOLLOW tag
                if not wp.can_follow:
                    extrainfo('URL %s defines META Robots NOFOLLOW flag, not following its children...' % self.url)
                    return data

            links.extend(wp.links)
            debug('LINKS=>',len(wp.links))
            #for typ, link in links:
            #    print 'Link=>',link
                
            # Let us update some stuff on the document...
            document.keywords = wp.keywords[:]
            document.description = wp.description
            document.title = wp.title
            
            # Raise "afterparse" event...
            objects.eventmgr.raise_event('afterparse', self.url, document, links=links)
            
            # Some times image links are provided in webpages as regular <a href=".."> links.
            # So in order to filer images fully, we need to check the wp.links list also.
            # Sample site: http://www.sheppeyseacadets.co.uk/gallery_2.htm
            if self._configobj.images:
                links += wp.images
            else:
                # Filter any links with image extensions out from links
                links = [(type, link) for type, link in links if link[link.rfind('.'):].lower() not in \
                         netinfo.image_extns] 

            #for typ, link in links:
            #    print 'Link=>',link
                
            wp.reset()
            del wp
            
            # Filter like that for video & audio
            if not self._configobj.movies:
                # Filter any links with video extension out from links...
                links = [(type, link) for type, link in links if link[link.rfind('.'):].lower() not in \
                         netinfo.movie_extns]

            if not self._configobj.sounds:
                # Filter any links with audio extension out from links...
                links = [(type, link) for type, link in links if link[link.rfind('.'):].lower() not in \
                         netinfo.sound_extns]                

            if not self._configobj.documents:
                # Filter any links with popular documents extension out from links...
                links = [(type, link) for type, link in links if link[link.rfind('.'):].lower() not in \
                         netinfo.document_extns]                
            
            links = self.offset_links(links)

            # Create collection object
            coll = HarvestManAutoUrlCollection(url_obj)

            children = []
            for typ, url in links:
                
                is_cgi, is_php = False, False

                # Not sure of the logical validity of the following 2 lines anymore...!
                # This is old code...
                if url.find('php?') != -1: is_php = True
                if typ == 'form' or is_php: is_cgi = True

                if not url or len(url)==0: continue
                # print 'URL=>',url,url_obj.get_full_url()
                
                try:
                    child_urlobj = urlparser.HarvestManUrl(url,
                                                           typ,
                                                           is_cgi,
                                                           url_obj)

                    # print url, child_urlobj.get_full_url()
                    
                    if objects.datamgr.check_exists(child_urlobj):
                        continue
                    else:
                        objects.datamgr.add_url(child_urlobj)
                        coll.addURL(child_urlobj)
                        children.append(child_urlobj)
                    
                except urlparser.HarvestManUrlError, e:
                    error('URL Error:', e)
                    continue

            # objects.queuemgr.endloop(True)
            
            # Update the document again...
            for child in children:
                document.add_child(child)
                    
            if not objects.queuemgr.push((url_obj.priority, coll, document), 'fetcher'):
                if self._pushflag: self.buffer.append((url_obj.priority, coll, document))

            # Update links called here
            objects.datamgr.update_links(url_obj, coll)

            
            return data
        
        elif self.url.is_stylesheet() and data:

            # Parse stylesheet to find all contained URLs
            # including imported stylesheets, if any.

            # Create a document and keep updating it -this is useful to provide
            # information to events...
            document = url_obj.make_document(data, [], '', [])

            # Raise "beforecssparse" event...
            if objects.eventmgr.raise_event('beforecssparse', self.url, document)==False:
                # Dont do anything with this URL...
                return
            
            sp = pageparser.HarvestManCSSParser()
            sp.feed(data)

            objects.eventmgr.raise_event('aftercssparse', self.url, links=sp.links)
            
            links = self.offset_links(sp.links)
            
            # Filter the CSS URLs also w.r.t rules
            # Filter any links with image extensions out from links
            if not self._configobj.images:
                links = [link for link in links if link[link.rfind('.'):].lower() not in netinfo.image_extns]
                
            children = []
             
            # Create collection object
            coll = HarvestManAutoUrlCollection(self.url)
            
            # Add these links to the queue
            for url in links:
                if not url: continue
                
                # There is no type information - so look at the
                # extension of the URL. If ending with .css then
                # add as stylesheet type, else as generic type.

                if url.lower().endswith('.css'):
                    urltyp = URL_TYPE_STYLESHEET
                else:
                    urltyp = URL_TYPE_ANY
                    
                try:
                    child_urlobj =  urlparser.HarvestManUrl(url,
                                                            urltyp,
                                                            False,
                                                            self.url)


                    if objects.datamgr.check_exists(child_urlobj):
                        continue
                    else:
                        objects.datamgr.add_url(child_urlobj)
                        coll.addURL(child_urlobj)                    
                        children.append(child_urlobj)
                        
                except urlparser.HarvestManUrlError:
                    continue

            # Update the document...
            for child in children:
                document.add_child(child)
            
            if not objects.queuemgr.push((self.url.priority, coll, document), 'fetcher'):
                if self._pushflag: self.buffer.append((self.url.priority, coll, document))

            # Update links called here
            objects.datamgr.update_links(self.url, coll)

            # Successful return returns data
            return data
        else:
            # Dont do anything
            return None


class HarvestManUrlDownloader(HarvestManUrlFetcher, HarvestManUrlCrawler):
    """ This is a mixin class which does both the jobs of crawling webpages
    and download urls """

    def __init__(self, index, url_obj = None, isThread=True):
        HarvestManUrlFetcher.__init__(self, index, url_obj, isThread)
        self.set_url_object(url_obj)
        
    def _initialize(self):
        HarvestManUrlFetcher._initialize(self)
        HarvestManUrlCrawler._initialize(self)        
        self._role = 'downloader'

    def set_url_object(self, obj):
        HarvestManUrlFetcher.set_url_object(self, obj)

    def set_url_object2(self, obj):
        HarvestManUrlCrawler.set_url_object(self, obj)        

    def exit_condition(self, caller):

        # Exit condition for single thread case
        if caller=='crawler':
            return (objects.queuemgr.data_q.qsize()==0)
        elif caller=='fetcher':
            return (objects.queuemgr.url_q.qsize()==0)

        return False

    def is_exit_condition(self):

        return (self.exit_condition('crawler') and self.exit_condition('fetcher'))
    
    def action(self):

        if self._isThread:
            self._loops = 0

            while not self._endflag:
                obj = objects.queuemgr.get_url_data("downloader")
                if not obj: continue
                
                self.set_url_object(obj)
                
                self.process_url()
                self.crawl_url()

                self._loops += 1
                self.sleep()
        else:
            while True:
                self.process_url()

                obj = objects.queuemgr.get_url_data( "crawler" )
                if obj: self.set_url_object2(obj)
                
                if self.url.is_webpage():
                    self.crawl_url()

                obj = objects.queuemgr.get_url_data("fetcher" )
                self.set_url_object(obj)
                    
                if self.is_exit_condition():
                    break

    def process_url(self):

        # First process urls using fetcher's algorithm
        HarvestManUrlFetcher.process_url(self)

    def crawl_url(self):
        HarvestManUrlCrawler.crawl_url(self)
        


