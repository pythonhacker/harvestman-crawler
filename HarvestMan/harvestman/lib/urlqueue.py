# -- coding: utf-8
""" urlqueue.py - Module which controls queueing of urls
    created by crawler threads. This is part of the HarvestMan
    program.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    Modification History

     Anand Jan 12 2005 -   Created this module, by splitting urltracker.py
     Aug 11 2006  Anand    Checked in changes for reducing CPU utilization.

     Aug 22 2006  Anand    Changes for fixing single-thread mode.
     Oct 19 2007  Anand    Added a very basic state-machine for managing
                           crawler end condition.
     Oct 22 2007  Anand    Enhanced the state machine with additional states,
                           checks and a modified mainloop etc.

     April 04 2008 Anand   Fixes in state machine and mainloop.
     Jun   03 2008 Anand   Fixes in abnormal exit logic. Other fixes.
     
   Copyright (C) 2005 Anand B Pillai.     

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import bisect
import time
import threading
import sys, os
import copy

from collections import deque
from Queue import *

from harvestman.lib import crawler
from harvestman.lib import urlparser
from harvestman.lib import document
from harvestman.lib import datamgr
from harvestman.lib import urltypes

from harvestman.lib.common.common import *
from harvestman.lib.common.macros import *
from harvestman.lib.common.singleton import Singleton

class HarvestManCrawlerState(Singleton):
    """ State machine for signalling crawler end condition
    and for managing end-condition stalemates and other
    issues """

    def __init__(self, queue):
        self.reset()
        self.cond = threading.Condition(threading.Lock())
        self.queue = queue

    def reset(self):
        self.ts = {}
        # Flags
        # All threads blocked (waiting)
        self.blocked = False
        # All fetchers blocked (waiting)
        self.fblocked = False
        # All crawlers blocked (waiting)
        self.cblocked = False
        # Crawler thread transitions
        self.ctrans = 0
        # Fetcher thread transitions
        self.ftrans = 0
        # Pushes by fetcher
        self.fpush = 0
        # Pushes by crawler
        self.cpush = 0
        # Gets by fetcher
        self.fgets = 0
        # Gets by crawler
        self.cgets = 0
        # Number of crawlers
        self.numcrawlers = 0
        # Number of fetchers
        self.numfetchers = 0
        # Suspend time-stamp, initially
        # set to None. To suspend end-state
        # checking, set this to current time...
        self.st = None
        # End state message. If normal exit
        # this is not set, for abormal exit
        # this could be set...
        self.abortmsg = ''
        self.blkcnt = 0
        self.lastcheck = time.time()
        
    def set(self, thread, state):

        curr, role = None, None
        item = self.get(thread)
        if item:
            curr, role = item
            
        if curr != state:
            # print 'Thread %s changes from state %s to state %s' % (thread, curr, state)
            self.ts[thread.getName()] = state, thread._role

        self.state_callback(thread, state)

    def get(self, thread):
        return self.ts.get(thread.getName())

    def zero_thread(self):
        """ Function which returns whether any of the
        thread counts (fetcher/crawler) have gone to zero """

        return (self.numfetchers==0) or (self.numcrawlers == 0)

    def suspend(self):
        """ Suspend checks on end state. This uses a timeout
        on the suspend flag which automaticall ages the flag
        and resets if, if not set within the aging period """

        self.st = time.time()

    def unsuspend(self):
        """ Unsuspend checks on end-state. """

        self.st = None
        
    def state_callback(self, thread, state):
        """ Callbacks for taking action according to state transitions """

        self.cond.acquire()
        typ = thread._role
        
        if state == crawler.THREAD_STARTED:
            if thread.resuming:
                # Resuming threads should call unsuspend..
                self.unsuspend()
            
        # If the thread is killed, try to regenerate it...
        elif state == crawler.THREAD_DIED:
            # print 'THREAD DIED',thread
            # Don't try to regenerate threads if this is a local exception.
            e = thread.exception
            logconsole("Thread died due to exception => ", str(e))
            # See class for last error. If it is same as
            # this error, don't do anything since this could
            # be a programming error and will send us into
            # a loop...
            #if str(thread.__class__._lasterror) == str(e):
            #    debug('Looks like a repeating error, not trying to restart thread %s' % (str(thread)))
            # In this case the thread has died, so reduce local thread count
            if typ=='crawler':
                self.numcrawlers -= 1
            elif typ == 'fetcher':
                self.numfetchers -= 1
                
            del self.ts[thread.getName()]
            #else:
            #    thread.__class__._lasterror = e
            #    # Release the lock now!
            #    self.cond.release()
            #    # Set suspend flag
            #    self.suspend()
            #    
            #    del self.ts[thread]
            #    extrainfo('Tracker thread %s has died due to error: %s' % (str(thread), str(e)))
            #    self.queue.dead_thread_callback(thread)
            #    return
            
        elif state == crawler.FETCHER_PUSHED_URL:
            # Push count for fetcher threads
            self.fpush += 1
        elif state == crawler.CRAWLER_PUSHED_URL:            
            # Push count for fetcher threads
            self.cpush += 1
        elif state == crawler.FETCHER_GOT_DATA:
            # Get count for fetcher threads
            self.fgets += 1
        elif state == crawler.CRAWLER_GOT_DATA:
            # Get count for fetcher threads
            self.cgets += 1            
        elif state == crawler.THREAD_SLEEPING:
            # A sleep state can be achieved only after a work state
            # so this indicates a cycle of transitions since
            # a cycle ends with a sleep...
            if typ == 'crawler':
                # Transition count for crawler threads                
                self.ctrans += 1
            elif typ == 'fetcher':
                # Transition count for crawler threads                
                self.ftrans += 1                
                
        elif state in (crawler.FETCHER_WAITING, crawler.CRAWLER_WAITING):
            if self.end_state():
                # This is useful only if the waiter is waiting
                # using wait1(...) method. If he is waiting
                # using wait2(...) method, he needs to devise
                # his own wake-up logic.
                self.cond.notify()

        self.cond.release()


    def all_are_waiting(self):
        """ This method returns whether the threads are all starved for
        data during regular crawl, which signals an end condition for the
        program """
        
        # Time stamp of calling this function
        currt = time.time()
        # Check suspend time-stamp
        if self.st:
            # Calculate difference, do not allow suspending
            # for more than 5 seconds.
            if (currt - self.st)>5.0:
                self.st = None
            return False

        if self.zero_thread():
            self.abortmsg = "Fatal thread reduction, stopping program"
            return True

        for status, role in self.ts.values():
            if status.__name__ not in ('PERM_EXCEPT','FETCHER_WAITING','CRAWLER_WAITING','THREAD_DIED', 'THREAD_STOPPED'):
                return False
        
        #if self.queue.url_q.qsize() or self.queue.data_q.qsize():
        #    return False

        return ((self.fpush == self.cgets) and \
               (self.cpush == self.fgets))

    def all_have_stopped(self):
        """ This method returns whether the threads are all stopped
        (or sleeping) after an abnormal exit of the program either
        by an explicit interrupt or after a program exception """
        
        if self.zero_thread():
            self.abortmsg = "Fatal thread reduction, stopping program"
            return True

        for status, role in self.ts.values():
            if status.__name__ not in ('PERM_EXCEPT','THREAD_STOPPED','THREAD_SLEEPING'):
                return False
        
        return True

    def end_state(self):
        """ Check end state for the program. Returns True
        if the program is ready to end. Abnormal exits are
        not handled here """

        return self.all_are_waiting()

    def exit_state(self):
        """ Checks end of state for program for abnormal
        exits. Returns True if the program is ready to end """

        return self.all_have_stopped()
        
##         # Time stamp of calling this function
##         currt = time.time()
##         # Check suspend time-stamp
##         if self.st:
##             # Calculate difference, do not allow suspending
##             # for more than 5 seconds.
##             if (currt - self.st)>5.0:
##                 self.st = None
##             return False

##         if self.zero_thread():
##             self.abortmsg = "Fatal thread reduction, stopping program"
##             return True
        
##         flag = True
##         numthreads = 0
        
##         fcount, fnblock, ccount, cnblock = 0, 0, 0, 0
##         self.blocked, self.fblocked, self.cblocked = False, False, False

##         for state, role in self.ts.values():
##             numthreads += 1

##             print role,'=>',state
            
##             if role == 'fetcher':
##                 fcount += 1
##                 if state == crawler.FETCHER_WAITING:
##                     fnblock += 1
##                 else:
##                     flag = False
##                     break
##             else:
##                 ccount += 1
##                 if state == crawler.CRAWLER_WAITING:
##                     cnblock += 1
##                 else:
##                     flag = False
##                     break

##         # print 'flag=>',flag
##          # For exit based on thread waiting state allignment
##         if flag:
##             self.blocked = True
##             print 'Numthreads=>',numthreads

##         if ccount==cnblock:
##             self.cblocked = True

##         if fcount==fnblock:
##             self.fblocked = True

##         if self.blocked:
##             # print 'BLOCKED!'
##             # print 'Length1 => ',len(self.queue.data_q)
##             # print 'Length2 => ',len(self.queue.url_q)
            
##             #print "Pushes=>",self.queue._pushes
##             # print 'Transitions',self.ctrans, self.ftrans,self.fpush,self.cpush

##             # If we have one fpush event, we need to have at least
##             # one cpush associated to it...
##             # Error: this is a dangerous condition... we never know if the
##             # crawler has filtered out the children of the first URL itself
##             # so cpush could be == 0, commented this out!
            
##             #if self.fpush>0:
##             #    return (self.cpush>0)
##             self.blkcnt += 1
##             if self.blkcnt > 10:
##                 return True
##             #return False

##         return False

    def __str__(self):
        return str(self.ts)

    def wait1(self, timeout):
        """ Regular wait method. This should be typically
        called with a large timeout value """

        while not self.end_state():
            self.cond.acquire()
            try:
                self.cond.wait(timeout)
            except IOError, e:
                break
            
            self.cond.release()
        
    def wait2(self, timeout):
        """ Secondary wait method. This should be typically
        called with a small timeout value. When calling
        this the caller should have additional logic to
        make sure he does not time out before the condition
        is met """
        
        try:
            self.cond.acquire()
            self.cond.wait(timeout)
            self.cond.release()
        except IOError, e:
            pass
        
class PriorityQueue(Queue):
    """ Priority queue based on bisect module (courtesy: Effbot) """

    def __init__(self, maxsize=0):
        Queue.__init__(self, maxsize)

    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = []
        
    def _put(self, item):
        bisect.insort(self.queue, item)

    def __len__(self):
        return self.qsize()
    
    def _qsize(self):
        return len(self.queue)

    def _empty(self):
        return not self.queue

    def _full(self):
        return self.maxsize>0 and len(self.queue) == self.maxsize

    def _get(self):
        return self.queue.pop(0)    

    def clear(self):
        while True:
            try:
                self.queue.pop()
            except IndexError:
                break
        
class HarvestManCrawlerQueue(object):
    """ This class functions as the thread safe queue
    for storing url data for tracker threads """

    alias = 'queuemgr'
    
    def __init__(self):
        self.reset()

    def reset(self):
        
        self.basetracker = None
        self.controller = None 
        self.flag = 0
        self.pushes = 0
        self.lasttimestamp = time.time()
        self.trackers  = []
        self.savers = []
        self.requests = 0
        self.trackerindex = 0
        self.baseurl = None
        self.stateobj = HarvestManCrawlerState(self)
        self.configobj = objects.config
        self.url_q = PriorityQueue(self.configobj.queuesize)
        self.data_q = PriorityQueue(self.configobj.queuesize)
            
        # Local buffer
        self.buffer = []
        # Lock for creating new threads
        self.cond = threading.Lock()
        # Flag indicating a forceful exit
        self.forcedexit = False
        # Sleep event
        self.evnt = SleepEvent(self.configobj.queuetime)

    def get_controller(self):
        """ Return the controller thread object """

        return self.controller
    
    def configure(self):
        """ Configure this class """

        try:
            self.baseurl = urlparser.HarvestManUrl(self.configobj.url,
                                                   urltypes.URL_TYPE_ANY,
                                                   0, self.configobj.url,
                                                   self.configobj.projdir)

            # Put the original hash of the start url in the class
            urlparser.HarvestManUrl.hashes[self.baseurl.index] = 1
            # Reset index to zero
            self.baseurl.index = 0
            objects.datamgr.add_url(self.baseurl)
            
        except urlparser.HarvestManUrlError:
            return False

        self.baseurl.starturl = True
        
        #if self.configobj.fastmode:
        try:
            self.basetracker = crawler.HarvestManUrlFetcher( 0, self.baseurl, True )
        except Exception, e:
            print "Fatal Error:",e
            hexit(1)
                
        #else:
        #    # Not much point keeping this code...!
        #    
        #    # Disable usethreads
        #    self.configobj.usethreads = False
        #    # Disable blocking
        #    self.configobj.blocking = False
        #    self.basetracker = crawler.HarvestManUrlDownloader( 0, self.baseurl, False )
            
        self.trackers.append(self.basetracker)
        # Reset state object
        self.stateobj.reset()
        
        return True

    def mainloop(self):
        """ Main program loop which waits for
        the threads to do their work """

        # print 'Waiting...'
        timeslot, tottime = 0.5, 0
        pool = objects.datamgr.get_url_threadpool()
        
        while not self.stateobj.end_state():
            self.stateobj.wait2(timeslot)
            tottime += timeslot
            if self.flag: 
                break
            
        if pool: pool.wait(10.0, self.configobj.timeout)

        if self.stateobj.abortmsg:
            extrainfo(self.stateobj.abortmsg)
            
        if not self.forcedexit:
            self.end_threads()

    def endloop(self, forced=False):
        """ Exit the mainloop """

        # Set flag to 1 to denote that downloading is finished.
        self.flag = 1
        if forced:
            self.forcedexit = True
            # A forced exit happens when we exit because a
            # download limit is breached, so instruct connectors
            # to not save anything from here on...
            conndict = objects.connfactory.get_connector_dict()
            for conn in conndict.keys():
                if conndict.get(conn):
                    conn.blockwrite = True

    def restart(self):
        """ Alternate method to start from a previous restored state """

        # Start harvestman controller thread
        import datamgr

        if self.configobj.enable_controller():
            self.controller = datamgr.HarvestManController()
            self.controller.start()

        # Start base tracker
        self.basetracker.start()
        time.sleep(2.0)

        for t in self.trackers[1:]:
            try:
                t.start()
            except AssertionError, e:
                logconsole(e)
                pass

        self.mainloop()
        
    def crawl(self):
        """ Starts crawling for this project """

        # Reset flag
        self.flag = 0

        t1=time.time()


        # Clear the queues...
        self.url_q.clear()
        self.data_q.clear()
        
        # Push the first URL directly to the url queue
        self.url_q.put((self.baseurl.priority, self.baseurl))
        # This is pushed to url queue, so increment crawler push...
        self.stateobj.cpush += 1
        
        #if self.configobj.fastmode:

        # Start harvestman controller thread
        if self.configobj.enable_controller():        
            self.controller = datamgr.HarvestManController()
            self.controller.start()

        # Create the number of threads in the config file
        # Pre-launch the number of threads specified
        # in the config file.

        # Initialize thread dictionary
        self.stateobj.numfetchers = int(0.75*self.configobj.maxtrackers)
        self.stateobj.numcrawlers = self.configobj.maxtrackers - self.stateobj.numfetchers

        self.basetracker.setDaemon(True)
        self.basetracker.start()

        evt = SleepEvent(0.1)
        while self.stateobj.get(self.basetracker) == crawler.FETCHER_WAITING:
            evt.sleep()

        # Set start time on config object
        self.configobj.starttime = t1

        del evt
        for x in range(1, self.stateobj.numfetchers):
            t = crawler.HarvestManUrlFetcher(x, None)
            self.add_tracker(t)
            t.setDaemon(True)
            t.start()

        for x in range(self.stateobj.numcrawlers):
            t = crawler.HarvestManUrlCrawler(x, None)
            self.add_tracker(t)
            t.setDaemon(True)
            t.start()

        self.mainloop()
        #else:
        #    self.basetracker.action()

    def get_base_tracker(self):
        """ Get the base tracker object """

        return self.basetracker

    def get_base_url(self):

        return self.baseurl
    
    def get_url_data(self, role):
        """ Pop url data from the queue """

        if self.flag: return None
        
        obj = None

        blk = self.configobj.blocking

        slptime = self.configobj.queuetime
        ct = threading.currentThread()
        
        if role == 'crawler':
            if blk:
                obj=self.data_q.get()
                self.stateobj.set(ct, crawler.CRAWLER_GOT_DATA)                
            else:
                self.stateobj.set(ct, crawler.CRAWLER_WAITING)
                try:
                    obj = self.data_q.get(timeout=slptime)
                    self.stateobj.set(ct, crawler.CRAWLER_GOT_DATA)                                    
                except Empty, TypeError:
                    obj = None
                    
        elif role == 'fetcher' or role=='tracker':
            
            if blk:
                obj = self.url_q.get()
                self.stateobj.set(ct, crawler.FETCHER_GOT_DATA)                                
            else:
                self.stateobj.set(ct, crawler.FETCHER_WAITING)
                try:
                    obj = self.url_q.get(timeout=slptime)
                    self.stateobj.set(ct, crawler.FETCHER_GOT_DATA)                                                    
                except Empty, TypeError:
                    obj = None
            
        self.lasttimestamp = time.time()        

        self.requests += 1
        return obj

    def add_tracker(self, tracker):

        self.trackers.append( tracker )
        self.trackerindex += 1

    def remove_tracker(self, tracker):

        self.trackers.remove(tracker)

    def dead_thread_callback(self, t):
        """ Call back function called by a thread if it
        dies with an exception. This class then creates
        a fresh thread, migrates the data of the dead
        thread to it """

        
        try:
            debug('Trying to regenerate thread...')
            self.cond.acquire()
            # First find out the type
            role = t._role
            new_t = None

            if role == 'fetcher':
                new_t = crawler.HarvestManUrlFetcher(t.get_index(), None)
            elif role == 'crawler':
                new_t = crawler.HarvestManUrlCrawler(t.get_index(), None)

            # Migrate data and start thread
            if new_t:
                new_t._url = t._url
                new_t._urlobject = t._urlobject
                
                new_t.buffer = copy.deepcopy(t.buffer)
                # If this is a crawler get links also
                if role == 'crawler':
                    new_t.links = t.links[:]
                    
                # Replace dead thread in the list
                idx = self.trackers.index(t)
                self.trackers[idx] = new_t
                new_t.resuming = True
                new_t.start()

                debug('Regenerated thread...')
                
                return THREAD_MIGRATION_OK
            else:
                # Could not make new thread, so decrement
                # count of threads.
                # Remove from tracker list
                self.trackers.remove(t)
                
                if role == 'fetcher':
                    self.stateobj.numfetchers -= 1
                elif role == 'crawler':
                    self.stateobj.numcrawlers -= 1

                return THREAD_MIGRATION_ERROR
        finally:
            self.cond.release()
                
    def push(self, obj, role):
        """ Push trackers to the queue """

        if self.flag: return
        
        ntries, status = 0, 0
        ct = threading.currentThread()
        
        if role == 'crawler' or role=='tracker' or role =='downloader':
            # debug('Pushing stuff to buffer',ct)
            self.stateobj.set(ct, crawler.CRAWLER_PUSH_URL)
            
            while ntries < 5:
                try:
                    ntries += 1
                    self.url_q.put((obj.priority, obj))
                    self.pushes += 1
                    status = 1
                    self.stateobj.set(ct, crawler.CRAWLER_PUSHED_URL)
                    break
                except Full:
                    self.evnt.sleep()
                    
        elif role == 'fetcher':
            # print 'Pushing stuff to buffer', ct
            self.stateobj.set(ct, crawler.FETCHER_PUSH_URL)                                
            # stuff = (obj[0].priority, (obj[0].index, obj[1]))
            while ntries < 5:
                try:
                    ntries += 1
                    self.data_q.put(obj)
                    self.pushes += 1
                    status = 1
                    self.stateobj.set(ct, crawler.FETCHER_PUSHED_URL)                    
                    break
                except Full:
                    self.evnt.sleep()                    

        self.lasttimestamp = time.time()

        return status
    
    def end_threads(self):
        """ Stop all running threads and clean
        up the program. This function is called
        for a normal/abnormal exit of HravestMan """

        extrainfo("Ending threads...")
        if self.configobj.project:
            if self.forcedexit:
                info('Terminating project ',self.configobj.project,'...')
            else:
                info("Ending Project", self.configobj.project,'...')

        # Stop controller
        if self.controller:
            self.controller.stop()
        
        if self.forcedexit:
            self._kill_tracker_threads()
        else:
            # Do a regular stop and join
            for t in self.trackers:
                try:
                    t.stop()
                except Exception, e:
                    pass

            # Wait till all threads report
            # to the state machine, with a
            # timeout of 5 minutes.
            extrainfo("Waiting for threads to finish up...")

            timeslot, tottime = 0.5, 0
            while not self.stateobj.exit_state():
                # print 'Waiting...'
                self.stateobj.wait2(timeslot)
                tottime += timeslot
                if tottime>=300.0:
                    break

            pool = objects.datamgr.get_url_threadpool()
            if pool: pool.wait(10.0, 120.0)
            
            extrainfo("Done.")
            # print 'Done.'
        
        self.trackers = []
        self.basetracker = None

    def _kill_tracker_threads(self):
        """ This function kills running tracker threads """

        count =0

        for tracker in self.trackers:
            count += 1
            sys.stdout.write('...')

            if count % 10 == 0: sys.stdout.write('\n')

            try:
                tracker.stop()
            except AssertionError, e:
                logconsole(str(e))
            except ValueError, e:
                logconsole(str(e))
            except crawler.HarvestManUrlCrawlerException, e:
                pass

