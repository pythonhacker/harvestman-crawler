# -- coding: utf-8
""" urlthread.py - Url thread downloader module.
    Has two classes, one for downloading of urls and another
    for managing the url threads.

    This module is part of the HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    Modification History

    Jan 10 2006  Anand  Converted from dos to unix format (removed Ctrl-Ms).
    Jan 20 2006  Anand  Small change in printing debug info in download
                        method.

    Mar 05 2007  Anand  Implemented http 304 handling in notify(...).

    Apr 09 2007  Anand  Added check to make sure that threads are not
                        re-started for the same recurring problem.
    
    Copyright (C) 2004 Anand B Pillai.

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import os, sys
import math
import time
import threading
import copy
import random
import sha
import urlparser

from mirrors import HarvestManMirrorManager
from collections import deque
from Queue import Queue, Full, Empty
from common.common import *
from common.macros import *

class HarvestManUrlThreadInterrupt(Exception):
    """ Interrupt raised to kill a harvestManUrlThread class's object """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class HarvestManUrlThread(threading.Thread):
    """ Class to download a url in a separate thread """

    # The last error which caused a thread instance to die
    _lasterror = None
    
    def __init__(self, name, timeout, threadpool):
        """ Constructor, the constructor takes a url, a filename
        , a timeout value, and the thread pool object pooling this
        thread """

        # url Object (This is an instance of urlPathParser class)
        self._urlobject = None
        # thread queue object pooling this thread
        self._pool = threadpool
        # max lifetime for the thread
        self._timeout = timeout
        # start time of thread
        self._starttime = 0
        # start time of a download
        self._dstartime = 0
        # sleep time
        self._sleepTime = 1.0
        # error object
        self._error = None
        # download status 
        self._downloadstatus = 0
        # busy flag
        self._busyflag = False
        # end flag
        self._endflag = False
        # Url data, only used for CONNECTOR_DATA_MODE_INMEM
        self._data = ''
        # Url temp file, used for mode CONNECTOR_DATA_MODE_FLUSH
        self._urltmpfile = ''
        # Current connector
        self._conn = None
        # initialize threading
        threading.Thread.__init__(self, None, None, name)

    def __str__(self):
        return self.getName()
    
    def get_error(self):
        """ Get error object of this thread """

        return self._error

    def get_status(self):
        """ Get the download status of this thread """

        return self._downloadstatus

    def get_data(self):
        """ Return the data of this thread """

        return self._data

    def get_tmpfname(self):
        """ Return the temp filename if any """

        return self._urltmpfile

    def set_tmpfname(self, filename):
        """ Set the temporary filename """

        # Typically called by connector objects
        self._urltmpfile = filename
        
    def set_status(self, status):
        """ Set the download status of this thread """

        self._downloadstatus = status

    def is_busy(self):
        """ Get busy status for this thread """

        return self._busyflag

    def set_busy_flag(self, flag):
        """ Set busy status for this thread """

        self._busyflag = flag

    def join(self):
        """ The thread's join method to be called
        by other threads """

        threading.Thread.join(self, self._timeout)

    def terminate(self):
        """ Kill this thread """

        self.stop()
        msg = 'Download thread, ' + self.getName() + ' killed!'
        raise HarvestManUrlThreadInterrupt, msg

    def stop(self):
        """ Stop this thread """

        # If download was not completed, push-back object
        # to the pool.
        if self._downloadstatus==0 and self._urlobject:
            self._pool.push(self._urlobject)
            
        self._endflag = True

    def download(self, url_obj):
        """ Download this url """

        # Set download status
        self._downloadstatus = 0
        self._dstartime = time.time()
        
        url = url_obj.get_full_url()

        if not url_obj.trymultipart:
            # print 'Gewt URL=>',url,self
            if url_obj.is_image():
                extrainfo('Downloading image ...', url)
            else:
                extrainfo('Downloading url ...', url)
        else:
            startrange = url_obj.range[0]
            endrange = url_obj.range[-1]
            # print "Got URL",url,self
            extrainfo('%s: Downloading url %s, byte range(%d - %d)' % (str(self),url,startrange,endrange))

        # This call will block if we exceed the number of connections
        self._conn = objects.connfactory.create_connector()
        mode = self._conn.get_data_mode()
        
        if not url_obj.trymultipart:
            res = self._conn.save_url(url_obj)
        else:
            # print 'Downloading URL',url,self
            res = self._conn.wrapper_connect(url_obj)
            # print 'Connector returned',self,url_obj.get_full_url()
            
            if mode == CONNECTOR_DATA_MODE_FLUSH:
                self._urltmpfile = self._conn.get_tmpfname()
            elif mode == CONNECTOR_DATA_MODE_INMEM:
                self._data = self._conn.get_data()

        # Add page hash to URL object
        data = self._conn.get_data()
        # Update pagehash on the URL object
        if data: 
            url_obj.pagehash = sha.new(data).hexdigest()
            
        # Remove the connector from the factory
        objects.connfactory.remove_connector(self._conn)
        
        # Set this as download status
        self._downloadstatus = res
        
        # get error flag from connector
        self._error = self._conn.get_error()

        self._conn = None
        
        # Notify thread pool
        self._pool.notify(self)

        if SUCCESS(res):
            if not url_obj.trymultipart:            
                extrainfo('Finished download of ', url)
            else:
                startrange = url_obj.range[0]
                endrange = url_obj.range[-1]                            
                debug('Finished download of byte range(%d - %d) of %s' % (startrange,endrange, url))
        elif self._error.number != 304:
            error('Failed to download URL',url)

        objects.datamgr.update_url(url_obj)
        
    def run(self):
        """ Run this thread """

        while not self._endflag:
            try:
                self._starttime=time.time()

                # print 'Waiting for next URL task',self
                url_obj = self._pool.get_next_urltask()

                # Dont do duplicate checking for multipart...
                if not url_obj.trymultipart and self._pool.check_duplicates(url_obj):
                    print 'Is duplicate',url_obj.get_full_url()
                    continue

                if not url_obj:
                    time.sleep(0.1)
                    continue

                # set busy flag to 1
                self._busyflag = True

                # Save reference
                self._urlobject = url_obj
                # print 'Got url=>',url_obj.get_full_url()
                
                filename, url = url_obj.get_full_filename(), url_obj.get_full_url()
                if not filename and not url:
                    return

                # Perf fix: Check end flag
                # in case the program was terminated
                # between start of loop and now!
                if not self._endflag: self.download(url_obj)
                # reset busyflag
                # print 'Setting busyflag to False',self
                self._busyflag = False
            except Exception, e:
                raise
                error('Worker thread Exception',e)
                # Now I am dead - so I need to tell the pool
                # object to migrate my data and produce a new thread.
                
                # See class for last error. If it is same as
                # this error, don't do anything since this could
                # be a programming error and will send us into
                # a loop...

                # Set busyflag to False
                self._busyflag = False
                # Remove the connector from the factory
                
                if self._conn and (not self._conn.is_released()):
                    objects.connfactory.remove_connector(self._conn)
                
                if str(self.__class__._lasterror) == str(e):
                    debug('Looks like a repeating error, not trying to restart worker thread %s' % (str(self)))
                else:
                    self.__class__._lasterror = e
                    # self._pool.dead_thread_callback(self)
                    error('Worker thread %s has died due to error: %s' % (str(self), str(e)))
                    error('Worker thread was downloading URL %s' % url_obj.get_full_url())

    def get_url(self):

        if self._urlobject:
            return self._urlobject.get_full_url()

        return ""

    def get_filename(self):

        if self._urlobject:
            return self._urlobject.get_full_filename()

        return ""

    def get_urlobject(self):
        """ Return this thread's url object """

        return self._urlobject

    def get_connector(self):
        """ Return the connector object """

        return self._conn
    
    def set_urlobject(self, urlobject):
            
        self._urlobject = urlobject
        
    def get_start_time(self):
        """ Return the start time of current download """

        return self._starttime

    def set_start_time(self, starttime):
        """ Return the start time of current download """

        self._starttime = starttime
    
    def get_elapsed_time(self):
        """ Get the time taken for this thread """

        now=time.time()
        fetchtime=float(math.ceil((now-self._starttime)*100)/100)
        return fetchtime

    def get_elapsed_download_time(self):
        """ Return elapsed download time for this thread """

        fetchtime=float(math.ceil((time.time()-self._dstartime)*100)/100)
        return fetchtime
        
    def long_running(self):
        """ Find out if this thread is running for a long time
        (more than given timeout) """

        # if any thread is running for more than <timeout>
        # time, return TRUE
        return (self.get_elapsed_time() > self._timeout)

    def set_timeout(self, value):
        """ Set the timeout value for this thread """

        self._timeout = value

    def close_file(self):
        """ Close temporary file objects of the connector """

        # Currently used only by hget
        if self._conn:
            reader = self._conn.get_fileobj()
            if reader: reader.close()
        
class HarvestManUrlThreadPool(Queue):
    """ Thread group/pool class to manage download threads """

    def __init__(self):
        """ Initialize this class """

        # list of spawned threads
        self._threads = []
        # list of url tasks
        self._tasks = []
        self._cfg = objects.config
        # Maximum number of threads spawned
        self._numthreads = self._cfg.threadpoolsize
        self._timeout = self._cfg.timeout
        
        # Last thread report time
        self._ltrt = 0.0
        # Local buffer
        self.buffer = []
        # Data dictionary for multi-part downloads
        # Keys are URLs and value is the data
        self._multipartdata = {}
        # Status of URLs being downloaded in
        # multipart. Keys are URLs
        self._multipartstatus = {}
        # Flag that is set when one of the threads
        # in a multipart download fails
        self._multiparterror = False
        # Number of parts
        self._parts = self._cfg.numparts
        # Condition object
        self._cond = threading.Condition(threading.Lock())
        # Condition object for waiting on end condition
        self._endcond = threading.Condition(threading.Lock())
        # Monitor object, used with hget
        self._monitor = None
        
        Queue.__init__(self, self._numthreads + 5)
        
    def start_threads(self):
        """ Start threads if they are not running """

        for t in self._threads:
            try:
                t.start()
            except AssertionError, e:
                pass
            
    def spawn_threads(self):
        """ Start the download threads """

        for x in range(self._numthreads):
            name = 'Worker-'+ str(x+1)
            fetcher = HarvestManUrlThread(name, self._timeout, self)
            fetcher.setDaemon(True)
            # Append this thread to the list of threads
            self._threads.append(fetcher)
            # print 'Starting thread',fetcher
            fetcher.start()

    def download_urls(self, listofurlobjects):
        """ Method to download a list of urls.
        Each member is an instance of a urlPathParser class """

        for urlinfo in listofurlobjects:
            self.push(urlinfo)

    def _get_num_blocked_threads(self):

        blocked = 0
        for t in self._threads:
            if not t.is_busy(): blocked += 1

        return blocked

    def is_blocked(self):
        """ The queue is considered blocked if all threads
        are waiting for data, and no data is coming """

        blocked = self._get_num_blocked_threads()

        if blocked == len(self._threads):
            return True
        else:
            return False

    def push(self, urlObj):
        """ Push the url object and start downloading the url """

        # print 'Pushed',urlObj.get_full_url()
        # unpack the tuple
        try:
            filename, url = urlObj.get_full_filename(), urlObj.get_full_url()
        except:
            return

        # Wait till we have a thread slot free, and push the
        # current url's info when we get one
        try:
            self.put( urlObj )
            urlObj.qstatus = urlparser.URL_IN_QUEUE            
            # If this URL was multipart, mark it as such
            self._multipartstatus[url] = MULTIPART_DOWNLOAD_QUEUED
        except Full:
            self.buffer.append(urlObj)
        
    def get_next_urltask(self):

        # Insert a random sleep in range
        # of 0 - 0.5 seconds
        # time.sleep(random.random()*0.5)
        try:
            if len(self.buffer):
                # Get last item from buffer
                item = buffer.pop()
                return item
            else:
                # print 'Waiting to get item',threading.currentThread()
                item = self.get()
                return item
            
        except Empty:
            return None

    def notify(self, thread):
        """ Method called by threads to notify that they
        have finished """

        try:
            self._cond.acquire()

            # Mark the time stamp (last thread report time)
            self._ltrt = time.time()

            urlObj = thread.get_urlobject()
            
            # See if this was a multi-part download
            if urlObj.trymultipart:
                status = thread.get_status()
                if status == CONNECT_YES_DOWNLOADED:
                    extrainfo('Thread %s reported %s' % (thread, urlObj.get_full_url()))
                    # For flush mode, get the filename
                    # for memory mode, get the data
                    datamode = self._cfg.datamode

                    fname, data = '',''
                    if datamode == CONNECTOR_DATA_MODE_FLUSH:
                        fname = thread.get_tmpfname()
                        datalen = os.path.getsize(fname)
                    else:
                        data = thread.get_data()
                        datalen = len(data)
                        

                    # See if the data was downloaded fully...,else reschedule this piece
                    expected = (urlObj.range[-1] - urlObj.range[0]) + 1
                    if datalen != expected:
                        extrainfo("Expected: %d, Got: %d" % (expected, datalen))
                        extrainfo("Thread %s did only a partial download, rescheduling this piece..." % thread)
                        if self._monitor:
                            # print 'Notifying failure',thread
                            self._monitor.notify_failure(urlObj, thread)
                            return
                        
                    index = urlObj.mirror_url.index
                    # print 'Index=>',index
                    
                    if index in self._multipartdata:
                        infolist = self._multipartdata[index]
                        if data:
                            infolist.append((urlObj.range[0],data))
                        elif fname:
                            infolist.append((urlObj.range[0],fname))                        
                    else:
                        infolist = []
                        if data:
                            infolist.append((urlObj.range[0],data))
                        elif fname:
                            infolist.append((urlObj.range[0],fname))
                        #else:
                        #    self._parts -= 1 # AD-HOC

                        self._multipartdata[index] = infolist

                    # print 'Length of data list is',len(infolist),self._parts
                    if len(infolist)==self._parts:
                        # Sort the data list  according to byte-range
                        infolist.sort()
                        # Download of this URL is complete...
                        logconsole('Download of %s is complete...' % urlObj.get_full_url())

                        if datamode == CONNECTOR_DATA_MODE_INMEM:
                            data = ''.join([item[1] for item in infolist])
                            self._multipartdata['data:' + str(index)] = data
                        else:
                            pass

                        self._multipartstatus[index] = MULTIPART_DOWNLOAD_COMPLETED
                else:
                    # Currently when a thread reports an error, we abort the download
                    # In future, we can inspect whether the error is fatal or not
                    # and resume download in another thread etc...
                    extrainfo('Thread %s reported error => %s' % (str(thread), str(thread.get_error())))
                    if self._monitor:
                        # print 'Notifying failure',thread
                        self._monitor.notify_failure(urlObj, thread)
                        # print 'Notified failure',thread
                        
            # if the thread failed, update failure stats on the data manager
            err = thread.get_error()

            tstatus = thread.get_status()

            # Either file was fetched or file was uptodate
            if err.number in (0, 304):
                # thread succeeded, increment file count stats on the data manager
                objects.datamgr.update_file_stats( urlObj, tstatus)

        finally:
            self._cond.release()

    def has_busy_threads(self):
        """ Return whether I have any busy threads """

        val=0
        for thread in self._threads:
            if thread.is_busy():
                val += 1
                break
            
        return val

    def get_busy_threads(self):
        """ Return a list of busy threads """

        return [thread for thread in self._threads if thread.is_busy()]

    def get_busy_count(self):
        """ Return a count of busy threads """

        return len(self.get_busy_threads())

    def get_busy_figure(self):

        s=''
        for t in self._threads:
            if t.is_busy():
                s=s + t.getName().split('-')[-1] + ' '

        return s

    def wait(self, period, timeout):

        # Wait for the pool to signal that there
        # are no more busy threads

        # Note: timeout must be > period
        count = 0.0
        while self.has_busy_threads():
            self._endcond.acquire()
            
            try:
                self._endcond.wait(period)
                count += period
                self.end_hanging_threads()
            except IOError, e:
                break

            self._endcond.release()
            if count>=timeout:
                break
    
    def locate_thread(self, url):
        """ Find a thread which downloaded a certain url """

        for x in self._threads:
            if not x.is_busy():
                if x.get_url() == url:
                    return x

        return None

    def locate_busy_threads(self, url):
        """ Find all threads which are downloading a certain url """

        threads=[]
        for x in self._threads:
            if x.is_busy():
                if x.get_url() == url:
                    threads.append(x)

        return threads

    def check_duplicates(self, urlobj):
        """ Avoid downloading same url file twice.
        It can happen that same url is linked from
        different web pages """

        filename = urlobj.get_full_filename()
        url = urlobj.get_full_url()

        # First check if any thread is in the process
        # of downloading this url.
        if self.locate_thread(url):
            debug('Another thread is downloading %s' % url)
            return True

        return False

    def end_hanging_threads(self):
        """ If any download thread is running for too long,
        kill it, and remove it from the thread pool """

        pool=[]
        for thread in self._threads:
            if thread.long_running(): pool.append(thread)

        for thread in pool:
            extrainfo('Killing hanging thread ', thread)
            # remove this thread from the thread list
            self._threads.remove(thread)
            # kill it
            try:
                thread.terminate()
            except HarvestManUrlThreadInterrupt:
                pass

            del thread

    def end_all_threads(self):
        """ Kill all running threads """

        try:
            self._cond.acquire()
            for t in self._threads:
                try:
                    t.terminate()
                    t.join()
                except HarvestManUrlThreadInterrupt, e:
                    debug(str(e))
                    pass

            self._threads = []
        finally:
            self._cond.release()

    def stop_all_threads(self):
        """ Stop all running threads """

        # Same as end_all_threads but only that
        # we don't print the killed message.
        try:
            self._cond.acquire()
            for t in self._threads:
                try:
                    t.terminate()
                    t.join()
                except HarvestManUrlThreadInterrupt, e:
                    pass

            self._threads = []
        finally:
            self._cond.release()

    def remove_finished_threads(self):
        """ Clean up all threads that have completed """

        for thread in self._threads:
            if not thread.is_busy():
                self._threads.remove(thread)
                del thread

    def last_thread_report_time(self):
        """ Return the last thread reported time """

        return self._ltrt
    
    def get_multipart_download_status(self, url):
        """ Get status of multipart downloads """

        # If a thread has failed, signal exit
        if self._multiparterror:
            return MULTIPART_DOWNLOAD_ERROR
        else:
            return self._multipartstatus.get(url.index, MULTIPART_DOWNLOAD_STATUS_UNKNOWN)

    def get_multipart_url_data(self, url):
        """ Return data for multipart downloads """

        return self._multipartdata.get('data:'+ str(url.index), '')

    def get_multipart_url_info(self, url):
        """ Return information for multipart downloads """

        return self._multipartdata.get(url.index, '')

    def dead_thread_callback(self, t):
        """ Call back function called by a thread if it
        dies with an exception. This class then creates
        a fresh thread, migrates the data of the dead
        thread to it """

        try:
            self._cond.acquire()
            new_t = HarvestManUrlThread(t.getName(), self._timeout, self)
            # Migrate data and start thread
            if new_t:
                new_t.set_urlobject(t.get_urlobject())
                # Replace dead thread in the list
                idx = self._threads.index(t)
                self._threads[idx] = new_t
                new_t.start()
            else:
                # Could not make new thread, remove
                # current thread anyway
                self._threads.remove(t)
        finally:
            self._cond.release()                
                    
    def get_threads(self):
        """ Return the list of thread objects """

        return self._threads

    def get_thread_urls(self):
        """ Return a list of current URLs being downloaded """

        # This returns a list of URL objects, not URL strings
        urlobjs = []

        for t in self._threads:
            if t.is_busy():
                urlobj = t.get_urlobject()
                if urlobj: urlobjs.append(urlobj)

        return urlobjs

    def reset_multipart_data(self):
        """ Reset multipart related state """

        self._multiparterror = False
        self._multipartdata.clear()
        self._multipartdata = {}
        self._multipartstatus.clear()
        self._multipartstatus = {}
        
        
class HarvestManUrlThreadPoolMonitor(threading.Thread):

    def __init__(self, threadpool):
        self._pool = threadpool
        self._pool._monitor = self
        self.lock = threading.Lock()
        self._failedurls = []
        self._listfailed = []
        self._flag = False
        # Mirror manager
        self.mirrormgr = HarvestManMirrorManager.getInstance()
        # initialize threading
        threading.Thread.__init__(self, None, None, "Monitor")        

    def run(self):

        while not self._flag:
            try:
                self.lock.acquire()
                items = []

                self._failedurls = self._listfailed[:]
                
                for urlobj, urlerror in self._failedurls:
                    # Reset URL to parent and try again...
                    if urlobj.mirrored:
                        # Try getting a new mirror URL
                        new_urlobj = self.mirrormgr.get_different_mirror_url(urlobj, urlerror)
                        
                        if new_urlobj:
                            extrainfo("New mirror URL=>", new_urlobj.get_full_url())
                            items.append((urlobj, urlerror))
                            self._pool.push(new_urlobj)
                        else:
                            logconsole('Could not find new working mirror. Exiting...')
                            self._pool._multiparterror = True
                            self._listfailed = []
                            break
                    else:
                        logconsole("URL is not mirrored, so no new mirrors to try. Exiting...")
                        self._pool._multiparterror = True
                        break

                for item in items:
                    self._listfailed.remove(item)

                self.lock.release()
                time.sleep(0.1)

            finally:
                pass
            
    def notify_failure(self, urlobj, thread):
        self.lock.acquire()
        self._listfailed.append((urlobj, thread.get_error()))
        self.lock.release()

    def stop(self):
        self._flag = True

    def reset(self):
        """ Reset the state """

        self._listfailed = []
        self._failedurls = []
        
