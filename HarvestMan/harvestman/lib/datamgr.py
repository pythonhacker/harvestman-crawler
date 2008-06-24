# -- coding: utf-8
""" datamgr.py - Data manager module for HarvestMan.
    This module is part of the HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    Oct 13 2006     Anand          Removed data lock since it is not required - Python GIL
                                   automatically locks byte operations.

    Feb 2 2007      Anand          Re-added function parse_style_sheet which went missing.

    Feb 26 2007      Anand          Fixed bug in check_duplicate_download for stylesheets.
                                   Also rewrote logic.

    Mar 05 2007     Anand          Added method get_last_modified_time_and_data to support
                                   server-side cache checking using HTTP 304. Fixed a small
                                   bug in css url handling.
    Apr 19 2007     Anand          Made to work with URL collections. Moved url mapping
                                   dictionary here. Moved CSS parsing logic to pageparser
                                   module.
    Feb 13 2008     Anand          Replaced URL dictionary with disk caching binary search
                                   tree. Other changes done later -> Got rid of many
                                   redundant lists which were wasting memory. Need to trim
                                   this further.

   Feb 14 2008      Anand          Many changes. Replaced/removed datastructures. Merged
                                   cache updating functions. Details in doc/Datastructures.txt .

   April 4 2008     Anand          Added update_url method and corresponding update method
                                   in bst.py to update state of URLs after download. Added
                                   statement to print broken links information at end.
   
   Copyright (C) 2004 Anand B Pillai.
    
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import os, sys
import shutil
import time
import math
import re
import sha
import copy
import random
import shelve
import tarfile
import zlib

import threading 
# Utils
import utils
import urlparser

from mirrors import HarvestManMirrorManager
from db import HarvestManDbManager

from urlthread import HarvestManUrlThreadPool
from connector import *
from methodwrapper import MethodWrapperMetaClass

from common.common import *
from common.macros import *
from common.bst import BST
from common.pydblite import Base


# Defining pluggable functions
__plugins__ = { 'download_url_plugin': 'HarvestManDataManager:download_url',
                'post_download_setup_plugin': 'HarvestManDataManager:post_download_setup',
                'print_project_info_plugin': 'HarvestManDataManager:print_project_info',
                'dump_url_tree_plugin': 'HarvestManDataManager:dump_url_tree'}

# Defining functions with callbacks
__callbacks__ = { 'download_url_callback': 'HarvestManDataManager:download_url',
                  'post_download_setup_callback' : 'HarvestManDataManager:post_download_setup' }

class HarvestManDataManager(object):
    """ The data manager cum indexer class """

    # For supporting callbacks
    __metaclass__ = MethodWrapperMetaClass
    alias = 'datamgr'        

    def __init__(self):
        self.reset()

    def reset(self):
        # URLs which failed with any error
        self._numfailed = 0
        # URLs which failed even after a re-download
        self._numfailed2 = 0
        # URLs which were retried
        self._numretried = 0
        self.cache = None
        self.savedfiles = 0
        self.reposfiles = 0
        self.cachefiles = 0
        self.filteredfiles = 0
        # Config object
        self._cfg = objects.config
        # Dictionary of servers crawled and
        # their meta-data. Meta-data is
        # a dictionary which currently
        # has only one entry.
        # i.e accept-ranges.
        self._serversdict = {}
        # URL database, a BST with disk-caching
        self._urldb = BST()
        self._urldb.set_auto(2)
        # Collections database, a BST with disk-caching        
        self.collections = BST()
        self.collections.set_auto(2)
        # byte count
        self.bytes = 0L
        # Redownload flag
        self._redownload = False
        # Mirror manager
        self.mirrormgr = HarvestManMirrorManager.getInstance()
        # Condition object for synchronization
        self.cond = threading.Condition(threading.Lock())        
        
    def initialize(self):
        """ Do initializations per project """

        # Url thread group class for multithreaded downloads
        if self._cfg.usethreads and self._cfg.fastmode:
            self._urlThreadPool = HarvestManUrlThreadPool()
            self._urlThreadPool.spawn_threads()
        else:
            self._urlThreadPool = None

        # Load any mirrors
        self.mirrormgr.load_mirrors(self._cfg.mirrorfile)
        # Set mirror search flag
        self.mirrormgr.mirrorsearch = self._cfg.mirrorsearch

    def get_urldb(self):
        return self._urldb
    
    def add_url(self, urlobj):
        """ Add urlobject urlobj to the local dictionary """

        # print 'Adding %s with index %d' % (urlobj.get_full_url(), urlobj.index)
        self._urldb.insert(urlobj.index, urlobj)
        
    def update_url(self, urlobj):
        """ Update urlobject urlobj in the local dictionary """

        # print 'Adding %s with index %d' % (urlobj.get_full_url(), urlobj.index)
        self._urldb.update(urlobj.index, urlobj)
        
    def get_url(self, index):

        # return self._urldict[str(index)]
        return self._urldb.lookup(index)

    def get_original_url(self, urlobj):

        # Return the original URL object for
        # duplicate URLs. This is useful for
        # processing URL objects obtained from
        # the collection object, because many
        # of them might be duplicate and would
        # not have any post-download information
        # such a headers etc.
        if urlobj.refindex != -1:
            return self.get_url(urlobj.refindex)
        else:
            # Return the same URL object to avoid
            # an <if None> check on the caller
            return urlobj
        
    def get_proj_cache_filename(self):
        """ Return the cache filename for the current project """

        # Note that this function does not actually build the cache directory.
        # Get the cache file path
        if self._cfg.projdir and self._cfg.project:
            cachedir = os.path.join(self._cfg.projdir, "hm-cache")
            cachefilename = os.path.join(cachedir, 'cache')

            return cachefilename
        else:
            return ''

    def get_proj_cache_directory(self):
        """ Return the cache directory for the current project """

        # Note that this function does not actually build the cache directory.
        # Get the cache file path
        if self._cfg.projdir and self._cfg.project:
            return os.path.join(self._cfg.projdir, "hm-cache")
        else:
            return ''        

    def get_server_dictionary(self):
        return self._serversdict

    def supports_range_requests(self, urlobj):
        """ Check whether the given url object
        supports range requests """

        # Look up its server in the dictionary
        server = urlobj.get_full_domain()
        if server in self._serversdict:
            d = self._serversdict[server]
            return d.get('accept-ranges', False)

        return False
        
    def read_project_cache(self):
        """ Try to read the project cache file """

        # Get cache filename
        moreinfo('Reading Project Cache...')
        cachereader = utils.HarvestManCacheReaderWriter(self.get_proj_cache_directory())
        obj, found = cachereader.read_project_cache()
        self._cfg.cachefound = found
        self.cache = obj
        if not found:
            # Fresh cache - create structure...
            self.cache.create('url','last_modified','etag', 'updated','location','checksum',
                              'content_length','data','headers')
            
            # Create an index on URL
            self.cache.create_index('url')
        else:
            pass

    def write_file_from_cache(self, urlobj):
        """ Write file from url cache. This
        works only if the cache dictionary of this
        url has a key named 'data' """

        ret = False

        # print 'Inside write_file_from_cache...'
        url = urlobj.get_full_url()
        content = self.cache._url[url]
        
        if len(content):
            # Value itself is a dictionary
            item = content[0]
            if not item.has_key('data'):
                return ret
            else:
                urldata = item['data']
                if urldata:
                    fileloc = item['location']                    
                    # Write file
                    extrainfo("Updating file from cache=>", fileloc)
                    try:
                        if SUCCESS(self.create_local_directory(os.path.dirname(fileloc))):
                            f=open(fileloc, 'wb')
                            f.write(zlib.decompress(urldata))
                            f.close()
                            ret = True
                    except (IOError, zlib.error), e:
                        moreinfo("Error:",e)
                        debug('IO Exception', e)
                                
        return ret

    def update_cache_for_url(self, urlobj, filename, urldata, contentlen, lastmodified, tag):
        """ Method to update the cache information for the URL 'url'
        associated to file 'filename' on the disk """

        # if page caching is disabled, skip this...
        if not objects.config.pagecache:
            return
        
        url = urlobj.get_full_url()
        if urldata:
            csum = sha.new(urldata).hexdigest()
        else:
            csum = ''
            
        # Update all cache keys
        content = self.cache._url[url]
        if content:
            rec = content[0]
            self.cache.update(rec, checksum=csum, location=filename,content_length=contentlen, last_modified=lastmodified,
                              etag=tag, updated=True)
            if self._cfg.datacache:
                self.cache.update(rec,data=zlib.compress(urldata))
        else:
            # Insert as new values
            if self._cfg.datacache:
                self.cache.insert(url=url, checksum=csum, location=filename,content_length=contentlen,last_modified=lastmodified,
                                  etag=tag, updated=True,data=zlib.compress(urldata))
            else:
                self.cache.insert(url=url, checksum=csum, location=filename,content_length=contentlen, last_modified=lastmodified,
                                  etag=tag, updated=True)                
        

    def get_url_cache_data(self, urlobj):
        """ Get cached data for the URL from disk """

        # This is returned as Unix time, i.e number of
        # seconds since Epoch.

        # This will be called from connector to avoid downloading
        # URL data using HTTP 304. However, we support this only
        # if we have data for the URL.
        if (not self._cfg.pagecache) or (not self._cfg.datacache):
            return ''

        url = urlobj.get_full_url()

        content = self.cache._url[url]
        if content:
            item = content[0]
            # Check if we have the data for the URL
            data = item.get('data','')
            if data:
                try:
                    return zlib.decompress(data)
                except zlib.error, e:
                    extrainfo('Error:',e)
                    return ''

        return ''

    def get_last_modified_time(self, urlobj):
        """ Return last-modified-time and data of the given URL if it
        was found in the cache """

        # This is returned as Unix time, i.e number of
        # seconds since Epoch.

        # This will be called from connector to avoid downloading
        # URL data using HTTP 304. 
        if (not self._cfg.pagecache):
            return ''

        url = urlobj.get_full_url()

        content = self.cache._url[url]
        if content:
            return content[0].get('last_modified', '')
        else:
            return ''

    def get_etag(self, urlobj):
        """ Return the etag of the given URL if it was found in  the cache """

        # This will be called from connector to avoid downloading
        # URL data using HTTP 304. 
        if (not self._cfg.pagecache):
            return ''

        url = urlobj.get_full_url()

        content = self.cache._url[url]
        if content:
            return content[0].get('etag', '')
        else:
            return ''        

    def is_url_cache_uptodate(self, urlobj, filename, urldata, contentlen=0, last_modified=0, etag=''):
        """ Check with project cache and find out if the
        content needs update """
        
        # If page caching is not enabled, return False
        # straightaway!

        # print 'Inside is_url_cache_uptodate...'
        
        if not self._cfg.pagecache:
            return (False, False)

        # Return True if cache is uptodate(no update needed)
        # and False if cache is out-of-date(update needed)
        # NOTE: We are using an comparison of the sha checksum of
        # the file's data with the sha checksum of the cache file.
        
        # Assume that cache is not uptodate apriori
        uptodate, fileverified = False, False

        url = urlobj.get_full_url()
        content = self.cache._url[url]

        if content:
            cachekey = content[0]
            cachekey['updated']=False

            fileloc = cachekey['location']
            if os.path.exists(fileloc) and os.path.abspath(fileloc) == os.path.abspath(filename):
                fileverified=True

            # Use a cascading logic - if last_modified is available use it first
            if last_modified:
                if cachekey['last_modified']:
                    # Get current modified time
                    cmt = cachekey['last_modified']
                    # print cmt,'=>',lmt
                    # If the latest page has a modified time greater than this
                    # page is out of date, otherwise it is uptodate
                    if last_modified<=cmt:
                        uptodate=True

            # Else if etag is available use it...
            elif etag:
                if cachekey['etag']:
                    tag = cachekey['etag']
                    if etag==tag:
                        uptodate = True
            # Finally use a checksum of actual data if everything else fails
            elif urldata:
                if cachekey['checksum']:
                    cachesha = cachekey['checksum']
                    digest = sha.new(urldata).hexdigest()
                    
                    if cachesha == digest:
                        uptodate=True
        
        if not uptodate:
            # Modified this logic - Anand Jan 10 06            
            self.update_cache_for_url(urlobj, filename, urldata, contentlen, last_modified, etag)

        return (uptodate, fileverified)

    def conditional_cache_set(self):
        """ A utility function to conditionally enable/disable
        the cache mechanism """

        # If already page cache is disabled, do not do anything
        if not self._cfg.pagecache:
            return
        
        # If the cache file exists for this project, disable
        # cache, else enable it.
        cachefilename = self.get_proj_cache_filename()

        if os.path.exists(cachefilename) and os.path.getsize(cachefilename):
            self._cfg.writecache = False
        else:
            self._cfg.writecache = True

    def post_download_setup(self):
        """ Actions to perform after project is complete """

        # Loop through URL db, one by one and then for those
        # URLs which were downloaded but did not succeed, try again.
        # But make sure we don't download links which were not-modified
        # on server-side (HTTP 304) and hence were skipped.
        failed = []
        # Broken links (404)
        nbroken = 0
        
        for node in self._urldb.preorder():
            urlobj = node.get()
            # print 'URL=>',urlobj.get_full_url()
            
            if urlobj.status == 404:
                # print 'BROKEN', urlobj.get_full_url()
                nbroken += 1
            elif urlobj.qstatus == urlparser.URL_DONE_DOWNLOAD and \
                   urlobj.status != 0 and urlobj.status != 304:
                failed.append(urlobj)
                    
        self._numfailed = len(failed)
        # print 'BROKEN=>', nbroken
        
        if self._cfg.retryfailed:
            moreinfo(' ')

            # try downloading again
            if self._numfailed:
                moreinfo('Redownloading failed links...',)
                self._redownload=True
                
                for urlobj in failed:
                    if urlobj.fatal or urlobj.starturl: continue
                    moreinfo('Re-downloading',urlobj.get_full_url())
                    self._numretried += 1
                    self.thread_download(urlobj)
                    
                # Wait for the downloads to complete...
                if self._numretried:
                    extrainfo("Waiting for the re-downloads to complete...")
                    self._urlThreadPool.wait(10.0, self._cfg.timeout)

                worked = 0
                # Let us calculate the failed rate again...
                for urlobj in failed:
                    if urlobj.status == 0:
                        # Download was done
                        worked += 1

                self._numfailed2 = self._numfailed - worked

        # Stop the url thread pool
        # Stop worker threads
        self._urlThreadPool.stop_all_threads()
                    
        # bugfix: Moved the time calculation code here.
        t2=time.time()

        self._cfg.endtime = t2

        # Write cache file
        if self._cfg.pagecache and self._cfg.writecache:
            cachewriter = utils.HarvestManCacheReaderWriter(self.get_proj_cache_directory())
            self.add_headers_to_cache()
            cachewriter.write_project_cache(self.cache)

        # If url header dump is enabled, dump it
        if self._cfg.urlheaders:
            self.dump_headers()

        if self._cfg.localise:
            self.localise_links()

        # Write archive file...
        if self._cfg.archive:
            self.archive_project()
            
        # dump url tree (dependency tree) to a file
        if self._cfg.urltreefile:
            self.dump_urltree(self._cfg.urltreefile)

        if not self._cfg.project: return

        nlinks = self._urldb.size
        # print stats of the project
        nservers, ndirs, nfiltered = objects.rulesmgr.get_stats()
        nfailed = self._numfailed
        numstillfailed = self._numfailed2

        numfiles = self.savedfiles
        numfilesinrepos = self.reposfiles
        numfilesincache = self.cachefiles

        numretried = self._numretried
        
        fetchtime = float((math.modf((self._cfg.endtime-self._cfg.starttime)*100.0)[1])/100.0)
        
        statsd = { 'links' : nlinks,
                   'filtered': nfiltered,
                   'processed': nlinks - nfiltered,
                   'broken': nbroken,
                   'extservers' : nservers,
                   'extdirs' : ndirs,
                   'failed' : nfailed,
                   'fatal' : numstillfailed,
                   'files' : numfiles,
                   'filesinrepos' : numfilesinrepos,
                   'filesincache' : numfilesincache,
                   'retries' : numretried,
                   'bytes': self.bytes,
                   'fetchtime' : fetchtime,
                }

        self.print_project_info(statsd)

        objects.eventmgr.raise_event('postdownload', None)
        
    def check_exists(self, urlobj):

        # Check if this URL object exits (is a duplicate)
        return self._urldb.lookup(urlobj.index)
        
    def update_bytes(self, count):
        """ Update the global byte count """

        self.bytes += count

    def update_file_stats(self, urlObject, status):
        """ Add the passed information to the saved file list """

        if not urlObject: return NULL_URLOBJECT_ERROR

        filename = urlObject.get_full_filename()

        if status == DOWNLOAD_YES_OK:
            self.savedfiles += 1
        elif status == DOWNLOAD_NO_UPTODATE:
            self.reposfiles += 1
        elif status == DOWNLOAD_NO_CACHE_SYNCED:
            self.cachefiles += 1
        elif status == DOWNLOAD_NO_WRITE_FILTERED:
            self.filteredfiles += 1                        
        
        return HARVESTMAN_OK
    
    def update_links(self, source, collection):
        """ Update the links dictionary for this collection """
        
        self.collections.insert(source.index, collection)

    def thread_download(self, url):
        """ Schedule download of this web document in a separate thread """

        # Add this task to the url thread pool
        if self._urlThreadPool:
            url.qstatus = urlparser.URL_QUEUED
            self._urlThreadPool.push(url)

    def has_download_threads(self):
        """ Return true if there are any download sub-threads
        running, else return false """

        if self._urlThreadPool:
            num_threads = self._urlThreadPool.has_busy_threads()
            if num_threads:
                return True

        return False

    def last_download_thread_report_time(self):
        """ Get the time stamp of the last completed
        download (sub) thread """

        if self._urlThreadPool:
            return self._urlThreadPool.last_thread_report_time()
        else:
            return 0

    def kill_download_threads(self):
        """ Terminate all the download threads """

        if self._urlThreadPool:
            self._urlThreadPool.end_all_threads()

    def create_local_directory(self, directory):
        """ Create the directories on the disk named 'directory' """

        # new in 1.4.5 b1 - No need to create the
        # directory for raw saves using the nocrawl
        # option.
        if self._cfg.rawsave:
            return CREATE_DIRECTORY_OK
        
        try:
            # Fix for EIAO bug #491
            # Sometimes, however had we try, certain links
            # will be saved as files, whereas they might be
            # in fact directories. In such cases, check if this
            # is a file, then create a folder of the same name
            # and move the file as index.html to it.
            path = directory
            while path:
                if os.path.isfile(path):
                    # Rename file to file.tmp
                    fname = path
                    os.rename(fname, fname + '.tmp')
                    # Now make the directory
                    os.makedirs(path)
                    # If successful, move the renamed file as index.html to it
                    if os.path.isdir(path):
                        fname = fname + '.tmp'
                        shutil.move(fname, os.path.join(path, 'index.html'))
                    
                path2 = os.path.dirname(path)
                # If we hit the root, break
                if path2 == path: break
                path = path2
                
            if not os.path.isdir(directory):
                os.makedirs( directory )
                extrainfo("Created => ", directory)
            return CREATE_DIRECTORY_OK
        except OSError:
            moreinfo("Error in creating directory", directory)
            return CREATE_DIRECTORY_NOT_OK

        return CREATE_DIRECTORY_OK

    def download_multipart_url(self, urlobj, clength):
        """ Download a URL using HTTP/1.1 multipart download
        using range headers """

        # First add entry of this domain in
        # dictionary, if not there
        domain = urlobj.get_full_domain()
        orig_url = urlobj.get_full_url()
        
        try:
            self._serversdict[domain]
        except KeyError:
            self._serversdict[domain] = {'accept-ranges': True}

        if self.mirrormgr.mirrors_available(urlobj):
            return self.mirrormgr.download_multipart_url(urlobj, clength, self._cfg.numparts, self._urlThreadPool)
        
        parts = self._cfg.numparts
        # Calculate size of each piece
        piecesz = clength/parts
        
        # Calculate size of each piece
        pcsizes = [piecesz]*parts
        # For last URL add the reminder
        pcsizes[-1] += clength % parts 
        # Create a URL object for each and set range
        urlobjects = []
        for x in range(parts):
            urlobjects.append(copy.deepcopy(urlobj))

        prev = 0
        for x in range(parts):
            curr = pcsizes[x]
            next = curr + prev
            urlobject = urlobjects[x]
            # Set mirror_url attribute
            urlobject.mirror_url = urlobj
            urlobject.trymultipart = True
            urlobject.clength = clength
            urlobject.range = (prev, next-1)
            urlobject.mindex = x
            prev = next
            self._urlThreadPool.push(urlobject)
            
        # Push this URL objects to the pool
        return URL_PUSHED_TO_POOL

    def download_url(self, caller, url):

        no_threads = (not self._cfg.usethreads) or \
                     url.is_webpage() or \
                     url.is_stylesheet()

        data=""
        if no_threads:
            # This call will block if we exceed the number of connections
            url.qstatus = urlparser.URL_QUEUED            
            conn = objects.connfactory.create_connector()

            # Set status to queued
            url.qstatus = urlparser.URL_IN_QUEUE            
            res = conn.save_url( url )
            
            objects.connfactory.remove_connector(conn)

            filename = url.get_full_filename()
            if res != CONNECT_NO_ERROR:
                filename = url.get_full_filename()

                if res==DOWNLOAD_YES_OK:
                    moreinfo("Saved to",filename)

                self.update_file_stats( url, res )
                data = conn.get_data()

            else:
                fetchurl = url.get_full_url()
                extrainfo( "Failed to download url", fetchurl)

            self._urldb.update(url.index, url)
            
        else:
            # debug("Scheduling %s for thread download: %s..." % (urlobj.get_full_url(), caller))
            # Set status to queued
            self.thread_download( url )
            # debug("Scheduled %s for thread download: %s" % (urlobj.get_full_url(), caller))

        return data

    def clean_up(self):
        """ Purge data for a project by cleaning up
        lists, dictionaries and resetting other member items"""

        # Reset byte count
        self.bytes = 0L
        #try:
        #if 1:
            ## moreinfo("Stats for urldb BST...")
##             moreinfo("Size left=>", self._urldb.size_lhs())
##             moreinfo("Size right=>", self._urldb.size_rhs())        
##             moreinfo('BST stats=>',self._urldb.stats())
##             moreinfo("BST diskcache stats=>",self._urldb.diskcache.get_stats())
##             moreinfo("Stats for collections BST...")
##             moreinfo("Size left=>", self.collections.size_lhs())
##             moreinfo("Size right=>", self.collections.size_rhs())        
##             moreinfo('BST stats=>',self.collections.stats())        
##             moreinfo("BST diskcache stats=>",self.collections.diskcache.get_stats())        
        self._urldb.clear()
        self.collections.clear()
        self.reset()
        #except TypeError:
        #    pass
        #except Exception:
        #    pass

    def archive_project(self):
        """ Archive project files into a tar archive file.
        The archive will be further compressed in gz or bz2
        format. New in 1.4.5 """

        extrainfo("Archiving project files...")
        # Get project directory
        projdir = self._cfg.projdir
        # Get archive format
        if self._cfg.archformat=='bzip':
            format='bz2'
        elif self._cfg.archformat=='gzip':
            format='gz'
        else:
            extrainfo("Archive Error: Archive format not recognized")
            return INVALID_ARCHIVE_FORMAT

        # Create tarfile name
        ptarf = os.path.join(self._cfg.basedir, "".join((self._cfg.project,'.tar.',format)))
        cwd = os.getcwd()
        os.chdir(self._cfg.basedir)

        # Create tarfile object
        tf = tarfile.open(ptarf,'w:'+format)
        # Projdir base name
        pbname = os.path.basename(projdir)

        # Add directories
        for item in os.listdir(projdir):
            # Skip cache directory, if any
            if item=='hm-cache':
                continue
            # Add directory
            fullpath = os.path.join(projdir,item)
            if os.path.isdir(fullpath):
                tf.add(os.path.join(pbname,item))
        # Dump the tarfile
        tf.close()

        os.chdir(cwd)            
        # Check whether writing was done
        if os.path.isfile(ptarf):
            extrainfo("Wrote archive file",ptarf)
            return FILE_WRITE_OK
        else:
            extrainfo("Error in writing archive file",ptarf)
            return FILE_WRITE_ERROR
            
    def add_headers_to_cache(self):
        """ Add original URL headers of urls downloaded
        as an entry to the cache file """
        
        # Navigate in pre-order, i.e in the order of insertion...
        for node in self.collections.preorder():
            coll = node.get()

            # Get list of links for this collection
            for urlobjidx in coll.getAllURLs():
                urlobj = self.get_url(urlobjidx)
                if urlobj==None: continue
                
                url = urlobj.get_full_url()
                # Get headers
                headers = urlobj.get_url_content_info()
                
                if headers:
                    content = self.cache._url[url]
                    if content:
                        urldict = content[0]
                        urldict['headers'] = headers


    def dump_headers(self):
        """ Dump the headers of the web pages
        downloaded, into a DBM file """
        
        # print dbmfile
        extrainfo("Writing url headers database")        
        
        headersdict = {}
        for node in self.collections.preorder():
            coll = node.get()
            
            for urlobjidx in coll.getAllURLs():
                urlobj = self.get_url(urlobjidx)
                
                if urlobj:
                    url = urlobj.get_full_url()
                    # Get headers
                    headers = urlobj.get_url_content_info()
                    if headers:
                        headersdict[url] = str(headers)
                        
        cache = utils.HarvestManCacheReaderWriter(self.get_proj_cache_directory())
        return cache.write_url_headers(headersdict)
    
    def localise_links(self):
        """ Localise all links (urls) of the downloaded html pages """

        # Dont confuse 'localising' with language localization.
        # This means just converting the outward (Internet) pointing
        # URLs in files to local files.

        info('Localising links of downloaded web pages...',)

        count = 0
        localized = []
        
        for node in self.collections.preorder():
            coll = node.get()
            
            sourceurl = self.get_url(coll.getSourceURL())
            childurls = [self.get_url(index) for index in coll.getAllURLs()]
            filename = sourceurl.get_full_filename()

            if (not filename in localized) and os.path.exists(filename):
                info('Localizing links for',filename)
                if SUCCESS(self.localise_file_links(filename, childurls)):
                    count += 1
                    localized.append(filename)

        extrainfo('Localised links of',count,'web pages.')

    def localise_file_links(self, filename, links):
        """ Localise links for this file """

        data=''
        
        try:
            fw=open(filename, 'r+')
            data=fw.read()
            fw.seek(0)
            fw.truncate(0)
        except (OSError, IOError),e:
            return FILE_TRUNCATE_ERROR

        # Regex1 to replace ( at the end
        r1 = re.compile(r'\)+$')
        r2 = re.compile(r'\(+$')        
        
        # MOD: Replace any <base href="..."> line
        basehrefre = re.compile(r'<base href=.*>', re.IGNORECASE)
        if basehrefre.search(data):
            data = re.sub(basehrefre, '', data)
        
        for u in links:
            if not u: continue
            
            url_object = u
            typ = url_object.get_type()

            if url_object.is_image():
                http_str="src"
            else:
                http_str="href"

            v = url_object.get_original_url()
            if v == '/': continue

            # Somehow, some urls seem to have an
            # unbalanced parantheses at the end.
            # Remove it. Otherwise it will crash
            # the regular expressions below.
            v = r1.sub('', v)
            v2 = r2.sub('', v)
            
            # Bug fix, dont localize cgi links
            if typ != 'base':
                if url_object.is_cgi(): 
                    continue
                
                fullfilename = os.path.abspath( url_object.get_full_filename() )
                #extrainfo('Url=>',url_object.get_full_url())
                #extrainfo('Full filename=>',fullfilename)
                urlfilename=''

                # Modification: localisation w.r.t relative pathnames
                if self._cfg.localise==2:
                    urlfilename = url_object.get_relative_filename()
                elif self._cfg.localise==1:
                    urlfilename = fullfilename

                # replace '\\' with '/'
                urlfilename = urlfilename.replace('\\','/')

                newurl=''
                oldurl=''
            
                # If we cannot get the filenames, replace
                # relative url paths will full url paths so that
                # the user can connect to them.
                if not os.path.exists(fullfilename):
                    # for relative links, replace it with the
                    # full url path
                    fullurlpath = url_object.get_full_url_sans_port()
                    newurl = "href=\"" + fullurlpath + "\""
                else:
                    # replace url with urlfilename
                    if typ == 'anchor':
                        anchor_part = url_object.get_anchor()
                        urlfilename = "".join((urlfilename, anchor_part))
                        # v = "".join((v, anchor_part))

                    if self._cfg.localise == 1:
                        newurl= "".join((http_str, "=\"", "file://", urlfilename, "\""))
                    else:
                        newurl= "".join((http_str, "=\"", urlfilename, "\""))

            else:
                newurl="".join((http_str,"=\"","\""))

            if typ != 'img':
                oldurl = "".join((http_str, "=\"", v, "\""))
                try:
                    oldurlre = re.compile("".join((http_str,'=','\\"?',v,'\\"?')))
                except Exception, e:
                    debug(str(e))
                    continue
                    
                # Get the location of the link in the file
                try:
                    if oldurl != newurl:
                        # info('Replacing %s with %s...' % (oldurl, newurl))
                        data = re.sub(oldurlre, newurl, data,1)
                except Exception, e:
                    debug(str(e))
                    continue
            else:
                try:
                    oldurlre1 = "".join((http_str,'=','\\"?',v,'\\"?'))
                    oldurlre2 = "".join(('href','=','\\"?',v,'\\"?'))
                    oldurlre = re.compile("".join(('(',oldurlre1,'|',oldurlre2,')')))
                except Exception, e:
                    debug(str(e))
                    continue
                
                http_strs=('href','src')
            
                for item in http_strs:
                    try:
                        oldurl = "".join((item, "=\"", v, "\""))
                        if oldurl != newurl:
                            info('Replacing %s with %s...' % (oldurl, newurl))                            
                            data = re.sub(oldurlre, newurl, data,1)
                    except:
                        pass

        try:
            fw.write(data)
            fw.close()
        except IOError, e:
            logconsole(e)
            return HARVESTMAN_FAIL

        return HARVESTMAN_OK

    def print_project_info(self, statsd):
        """ Print project information """

        nlinks = statsd['links']
        nservers = statsd['extservers'] + 1
        nfiles = statsd['files']
        ndirs = statsd['extdirs'] + 1
        numfailed = statsd['failed']
        nretried = statsd['retries']
        fatal = statsd['fatal']
        fetchtime = statsd['fetchtime']
        nfilesincache = statsd['filesincache']
        nfilesinrepos = statsd['filesinrepos']
        nbroken = statsd['broken']
        
        # Bug fix, download time to be calculated
        # precisely...

        dnldtime = fetchtime

        strings = [('link', nlinks), ('server', nservers),
                   ('file', nfiles), ('file', nfilesinrepos),
                   ('directory', ndirs), ('link', numfailed), ('link', fatal),
                   ('link', nretried), ('file', nfilesincache), ('link', nbroken) ]

        fns = map(plural, strings)
        info(' ')

        if fetchtime and nfiles:
            fps = (float(nfiles/dnldtime))
            fps = float((math.modf(fps*100.0))[1]/100.0)
        else:
            fps=0.0

        bytes = self.bytes

        ratespec='KB/sec'
        if bytes and dnldtime:
            bps = (float(bytes/dnldtime))/100.0
            bps = float((math.modf(bps*100.0))[1]/1000.0)
            if bps<1.0:
                bps *= 1000.0
                ratespec='bytes/sec'
        else:
            bps = 0.0

        if self._cfg.simulate:
            info("HarvestMan crawl simulation of",self._cfg.project,"completed in",fetchtime,"seconds.")
        else:
            info('HarvestMan mirror',self._cfg.project,'completed in',fetchtime,'seconds.')
            
        if nlinks: info(nlinks,fns[0],'scanned in',nservers,fns[1],'.')
        else: info('No links parsed.')
        if nfiles: info(nfiles,fns[2],'written.')
        else:info('No file written.')
        
        if nfilesinrepos:
            info(nfilesinrepos,fns[3],wasOrWere(nfilesinrepos),'already uptodate in the repository for this project and',wasOrWere(nfilesinrepos),'not updated.')
        if nfilesincache:
            info(nfilesincache,fns[8],wasOrWere(nfilesincache),'updated from the project cache.')

        if nbroken: info(nbroken,fns[9],wasOrWere(nbroken),'were broken.')
        if fatal: info(fatal,fns[5],'had fatal errors and failed to download.')
        if bytes: info(bytes,' bytes received at the rate of',bps,ratespec,'.\n')
        info('*** Log Completed ***\n')
        
        # get current time stamp
        s=time.localtime()

        tz=(time.tzname)[0]

        format='%b %d %Y '+tz+' %H:%M:%S'
        tstamp=time.strftime(format, s)

        if not self._cfg.simulate:
            # Write statistics to the crawl database
            HarvestManDbManager.add_stats_record(statsd)
            logconsole('Done.')

            # No longer writing a stats file...
            # Write stats to a stats file
            #statsfile = self._cfg.project + '.hst'
            #statsfile = os.path.abspath(os.path.join(self._cfg.projdir, statsfile))
            #logconsole('Writing stats file ', statsfile , '...')
            # Append to files contents
            #sf=open(statsfile, 'a')

            # Write url, file count, links count, time taken,
            # files per second, failed file count & time stamp
            #infostr='url:'+self._cfg.url+','
            #infostr +='files:'+str(nfiles)+','
            #infostr +='links:'+str(nlinks)+','
            #infostr +='dirs:'+str(ndirs)+','
            #infostr +='failed:'+str(numfailed)+','
            #infostr +='refetched:'+str(nretried)+','
            #infostr +='fatal:'+str(fatal)+','
            #infostr +='elapsed:'+str(fetchtime)+','
            #infostr +='fps:'+str(fps)+','
            #infostr +='kbps:'+str(bps)+','
            #infostr +='timestamp:'+tstamp
            #infostr +='\n'
            
            #sf.write(infostr)
            #sf.close()

    def dump_urltree(self, urlfile):
        """ Dump url tree to a file """

        # This function provides a little
        # more functionality than the plain
        # dump_urls in the rules module.
        # This creats an html file with
        # each url and its children below
        # it. Each url is a hyperlink to
        # itself on the net if the file
        # is an html file.

        try:
            if os.path.exists(urlfile):
                os.remove(urlfile)
        except OSError, e:
            logconsole(e)

        moreinfo('Dumping url tree to file', urlfile)
        fextn = ((os.path.splitext(urlfile))[1]).lower()        
        
        try:
            f=open(urlfile, 'w')
            if fextn in ('', '.txt'):
                self.dump_urltree_textmode(f)
            elif fextn in ('.htm', '.html'):
                self.dump_urltree_htmlmode(f)
            f.close()
        except Exception, e:
            logconsole(e)
            return DUMP_URL_ERROR

        debug("Done.")

        return DUMP_URL_OK

    def dump_urltree_textmode(self, stream):
        """ Dump urls in text mode """

        for node in self.collections.preorder():
            coll = node.get()

            idx = 0
            links = [self.get_url(index) for index in coll.getAllURLs()]
            children = []
            
            for link in links:
                if not link: continue

                # Get base link, only for first
                # child url, since base url will
                # be same for all child urls.
                if idx==0:
                    children = []
                    base_url = link.get_parent_url().get_full_url()
                    stream.write(base_url + '\n')

                childurl = link.get_full_url()
                if childurl and childurl not in children:
                    stream.write("".join(('\t',childurl,'\n')))
                    children.append(childurl)

                idx += 1


    def dump_urltree_htmlmode(self, stream):
        """ Dump urls in html mode """

        # Write html header
        stream.write('<html>\n')
        stream.write('<head><title>')
        stream.write('Url tree generated by HarvestMan - Project %s'
                     % self._cfg.project)
        stream.write('</title></head>\n')

        stream.write('<body>\n')

        stream.write('<p>\n')
        stream.write('<ol>\n')
        
        for node in self.collections.preorder():
            coll = node.get()
            
            idx = 0
            links = [self.get_url(index) for index in coll.getAllURLs()]            

            children = []
            for link in links:
                if not link: continue

                # Get base link, only for first
                # child url, since base url will
                # be same for all child urls.
                if idx==0:
                    children = []                   
                    base_url = link.get_parent_url().get_full_url()
                    stream.write('<li>')                    
                    stream.write("".join(("<a href=\"",base_url,"\"/>",base_url,"</a>")))
                    stream.write('</li>\n')
                    stream.write('<p>\n')
                    stream.write('<ul>\n')
                                 
                childurl = link.get_full_url()
                if childurl and childurl not in children:
                    stream.write('<li>')
                    stream.write("".join(("<a href=\"",childurl,"\"/>",childurl,"</a>")))
                    stream.write('</li>\n')                    
                    children.append(childurl)
                    
                idx += 1                


            # Close the child list
            stream.write('</ul>\n')
            stream.write('</p>\n')
            
        # Close top level list
        stream.write('</ol>\n')        
        stream.write('</p>\n')
        stream.write('</body>\n')
        stream.write('</html>\n')

    def get_url_threadpool(self):
        """ Return the URL thread-pool object """

        return self._urlThreadPool

class HarvestManController(threading.Thread):
    """ A controller class for managing exceptional
    conditions such as file limits. Right now this
    is written with the sole aim of managing file
    & time limits, but could get extended in future
    releases. """

    def __init__(self):
        self._dmgr = objects.datamgr
        self._tq =  objects.queuemgr
        self._cfg = objects.config
        self._exitflag = False
        self._conn = {}
        threading.Thread.__init__(self, None, None, 'HarvestMan Control Class')

    def run(self):
        """ Run in a loop looking for
        exceptional conditions """

        while not self._exitflag:
            # Wake up every second and look
            # for exceptional conditions
            time.sleep(1.0)
            self._manage_time_limits()
            self._manage_file_limits()
            self._manage_maxbytes_limits()
            
    def stop(self):
        """ Stop this thread """

        self._exitflag = True

    def terminator(self):
        """ The function which terminates the program
        in case of an exceptional condition """

        # This somehow got deleted in HarvestMan 1.4.5
        self._tq.endloop()
        
    def _manage_time_limits(self):
        """ Manage limits on time for the project """

        # If time limit is not set, return
        if self._cfg.timelimit == -1:
            return HARVESTMAN_FAIL
        
        t2=time.time()

        timediff = float((math.modf((t2-self._cfg.starttime)*100.0)[1])/100.0)
        timemax = self._cfg.timelimit
        
        if timediff >= timemax -1:
            moreinfo('Specified time limit of',timemax ,'seconds reached!')            
            self.terminator()

        return HARVESTMAN_OK

    def _manage_file_limits(self):
        """ Manage limits on maximum file count """

        lsaved = self._dmgr.savedfiles
        lmax = self._cfg.maxfiles

        if lsaved < lmax:
            return HARVESTMAN_FAIL
        
        if lsaved == lmax:
            moreinfo('Specified file limit of',lmax ,'reached!')
            self.terminator()
            
        return HARVESTMAN_OK

    def _manage_maxbytes_limits(self):
        """ Manage limits on maximum bytes a crawler should download in total per job. """

        lsaved = self._dmgr.bytes
        lmax = self._cfg.maxbytes

        if lsaved < lmax:
            return HARVESTMAN_FAIL

        if lsaved >= lmax:
            moreinfo('Specified maxbytes limit of',lmax ,'reached!')
            self.terminator()   

        return HARVESTMAN_OK
        
                    
