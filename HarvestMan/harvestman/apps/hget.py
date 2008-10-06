#! /usr/bin/env python
# -- coding: utf-8

""" Hget - Extensible, modular, multithreaded Internet
    downloader program in the spirit of wget, using
    HarvestMan codebase, with HTTP multipart support.
    
    Version      - 1.0 beta 1.

    Author: Anand B Pillai <abpillai at gmail dot com>

    HGET is free software. See the file LICENSE.txt for information
    on the terms and conditions of usage, and a DISCLAIMER of ALL WARRANTIES.

 Modification History

    Created: April 19 2007 Anand B Pillai

     April 20 2007 Added more command-line options   Anand
     April 24 2007 Made connector module to flush data  Anand
                   to tempfiles when run with hget.
     April 25 2007 Implementation of hget features is  Anand
                   completed!
     April 30 2007 Many fixes/enhancements to hget.
                   1. Reconnection of a lost connection does not
                   lose already downloaded data.
                   2. Closing of files of threads when download is
                   aborted.
                   3. Thread count shows current number of threads
                   which are actually doing downloads, reflecting
                   the activity.
                   4. Final printing of time taken, average bandwidth
                   and file size.

     May 10 2007   Added support for sf.net mirrors in multipart.
     Aug    2007   Fixed bugs in resetting state of various objects
                   when doing many multipart downloads one after other.
     
Copyright(C) 2007, Anand B Pillai

"""

import __init__
import sys, os
import re
import shutil

from harvestman.lib import connector
from harvestman.lib import urlparser
from harvestman.lib import config
from harvestman.lib import logger
from harvestman.lib import datamgr
from harvestman.lib import urlthread
from harvestman.lib import mirrors
from harvestman.lib.methodwrapper import MethodWrapperMetaClass

from harvestman.lib.common.common import *
from harvestman.lib.common.macros import *

# Current dir - okay
from spider import HarvestMan

VERSION='0.1'
MATURITY='beta 1'

class Hget(HarvestMan):
    """ Web getter class for HarvestMan which defines a wget like interface
    for downloading files on the command line with HTTP/1.0 Multipart support, mirror
    search and failover """

    __metaclass__ = MethodWrapperMetaClass
    
    USER_AGENT = "Python-urllib/1.16"

    def grab_url(self, url, filename=None):
        """ Download the given URL and save it to the (optional) filename """

        # If a filename is given, set outfile to it
        if filename:
            objects.config.hgetoutfile = filename
            # print 'Saving to',filename

        # We need to reset some counters and
        # data structures ...
        
        # Reset progress object
        objects.config.reset_progress()
        # Reset thread pool, multipart status
        self._pool.reset_multipart_data()
        # Reset monitor
        self._monitor.reset()
        # Reset mirror manager
        mirrormgr = mirrors.HarvestManMirrorManager.getInstance()
        mirrormgr.reset()
        
        try:
            # print objects.config.requests, objects.config.connections
            conn = connector.HarvestManUrlConnector()
            urlobj = None
            
            try:
                print '\nDownloading URL',url,'...'
                urlobj = urlparser.HarvestManUrl(url)
                ret = conn.url_to_file(urlobj)

                if urlobj.trymultipart and mirrormgr.used:
                    # Print stats if mirrors were used...
                    mirrormgr.print_stats()
                    
                return HGET_DOWNLOAD_OK
            except urlparser.HarvestManUrlError, e:
                print str(e)
                print 'Error: Invalid URL "%s"' % url

                return HGET_DOWNLOAD_ERROR
            
        except KeyboardInterrupt, e:
            print 'Caught keyboard interrupt...'
            if urlobj: self.clean_up(conn, urlobj)

            return HGET_KEYBOARD_INTERRUPT

        except Exception, e:
            print 'Caught fatal error (%s): %s' % (e.__class__.__name__, str(e))
            if urlobj: self.clean_up(conn, urlobj, e)
            print_traceback()

            return HGET_FATAL_ERROR
            
    def clean_up(self, conn, urlobj, exception=None):
        """ Perform clean up after any exception """
        
        reader = conn.get_fileobj()
        if reader: reader.stop()
        if exception==None:
            print '\n\nDownload aborted by user interrupt.'

        # If flushdata mode, delete temporary files
        if objects.config.datamode == CONNECTOR_DATA_MODE_FLUSH:
            print 'Cleaning up temporary files...'
            fname1 = conn.get_tmpfname()
            # print 'Temp fname=>',fname1
            
            fullurl = urlobj.get_full_url()
            range_request = conn._headers.get('accept-ranges','').lower()
            # If server supports range requests, then do not
            # clean up temp file, since we can start from where
            # we left off, if this file is requested again.
            if not range_request=='bytes':
                if fname1:
                    try:
                        os.remove(fname1)
                    except OSError, e:
                        print e
            elif fname1:
                # Dump an info file consisting of the header
                # information to a file, so that we can use it
                # to resume downloading from where we left off
                conn.write_url_info_file(fullurl)

            lthreads = self._pool.get_threads()
            lfiles = []
            for t in lthreads:
                fname = t.get_tmpfname()
                if fname: lfiles.append(fname)
                t.close_file()

            print 'Waiting for threads to finish...'
            self._pool.end_all_threads()

            # For currently running multipart download, clean
            # up all pieces since there is no guarantee that
            # the next request will be for the same number of
            # pieces of files, though the server supports
            # multipart downloads.
            if lfiles:
                tmpdir = os.path.dirname(lfiles[0])
            else:
                tmpdir = ''
                
            for f in lfiles:
               if os.path.isfile(f):
                   try:
                       os.remove(f)
                   except (IOError, OSError), e:
                       print 'Error: ',e

            # Commented out because this is giving a strange
            # exception on Windows.
            
            # If doing multipart, cleanup temp dir also
            #if objects.config.multipart:
            #    if not objects.config.hgetnotemp and tmpdir:
            #        try:
            #            shutil.rmtree(tmpdir)
            #        except OSError, e:
            #            print e
            print 'Done'

        print ''
        
    def create_user_directories(self):
        """ Create the initial directories for Hget application """

        super(Hget, self).create_user_directories()
        # Create temporary directory for saving files
        if not objects.config.hgetnotemp:
            try:
                tmp = GetMyTempDir()
                if not os.path.isdir(tmp):
                    os.makedirs(tmp)
                # Could not make tempdir, set hgetnotemp to True
                if not os.path.isdir(tmp):
                    objects.config.hgetnotemp = True
            except Exception, e:
                pass

    def init(self):
        """ Initialize the Hget object's state """

        objects.config.USER_AGENT = self.__class__.USER_AGENT
        # Fudge Firefox USER-AGENT string since some sites
        # dont accept our user-agent.
        # objects.config.USER_AGENT = "Firefox/2.0.0.8"
        objects.config.appname = 'Hget'
        objects.config.version = VERSION
        objects.config.maturity = MATURITY
        objects.config.nocrawl = True
        self._pool = None
        self._monitor = None
        
        # Get program options
        objects.config.parse_arguments()
        
        objects.config.threadpoolsize = 20
        # Set number of connections to two plus numparts
        objects.config.connections = 2*objects.config.numparts
        # Set socket timeout to a very low value
        objects.config.socktimeout = 30.0
        # objects.config.requests = 2*objects.config.numparts
        if objects.config.hgetverbose:
            objects.config.verbosity=logger.EXTRAINFO

        objects.logger.make_logger()        
        objects.logger.setLogSeverity(objects.config.verbosity)

        self.process_plugins()
        
        self.register_common_objects()
        self.create_user_directories()

        # Set logging format to plain
        objects.logger.setPlainFormat()

    def hget(self):
        """ Main method of Hget class. Downloads all URL(s) passed on the command
        line and saves them """

        if len(objects.config.projects)==0:
            print 'Error: No input URL/file given. Run with -h or no arguments to see usage.\n'
            return -1

        objects.datamgr.initialize()
        self._pool = objects.datamgr.get_url_threadpool()

        self._monitor = urlthread.HarvestManUrlThreadPoolMonitor(self._pool)
        self._monitor.start()
            
        for arg in objects.config.projects:
            url = arg['url']
            
            # Check if the argument is a file, if so
            # download URLs specified in the file.
            if os.path.isfile(url):
                # Open it, read URL per line and schedule download
                print 'Input file %s found, scheduling download of URLs...' % url
                try:
                    for line in file(url):
                        line = line.strip()
                        # The line can optionally contain a different output
                        # file name, in which case it should be separated by
                        # commas...
                        items = line.split(',')
                        if len(items)==2:
                            url, filename = items[0].strip(), items[1].strip()
                            if self.grab_url(url, filename) == HGET_KEYBOARD_INTERRUPT:
                                break
                        elif len(items)==1:
                            url = items[0].strip()
                            if self.grab_url(url) == HGET_KEYBOARD_INTERRUPT:
                                break
                        print ''

                #except IOError, e:
                #    print 'Error:',e
                except Exception, e:
                    raise
            else:
                self.grab_url(url)

        self._monitor.stop()

    def main(self):
        """ Main sub-routine """

        # Add help option if no arguments are given
        if len(sys.argv)<2:
            sys.argv.append('-h')
            
        self.init()
        self.hget()
        return 0

def main():
    """ Main routine """

    Hget().main()
    
if __name__ == "__main__":
    main()
    
