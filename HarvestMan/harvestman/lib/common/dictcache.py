"""
dictcache.py - Module implementing a dictionary like object
with three level caching (2 level memory, 1 level disk) with
O(1) search times for keys. 

Created Anand B Pillai <abpillai at gmail dot com> Feb 13 2008

Copyright (C) 2008, Anand B Pillai.

"""

import os
import cPickle
import time
from threading import Semaphore

PID = os.getpid()

class DictCache(object):
    """ A dictionary like object with pickled disk caching
    which allows to store large amount of data with minimal
    memory costs """
    
    def __init__(self, frequency, tmpdir=''):
        # Frequency at which commits are done to disk
        self.freq = frequency
        # Total number of commit cycles
        self.cycles = 0
        self.curr = 0
        # Disk cache...
        self.cache = {}
        # Internal temporary cache
        self.d = {} 
        self.dmutex = Semaphore(1)
        # Last loaded cache dictionary from disk
        self.dcache = {}
        # disk cache hits
        self.dhits = 0
        # in-mem cache hits
        self.mhits = 0
        # temp dict hits
        self.thits = 0
        self.tmpdir = tmpdir
        if self.tmpdir:
            self.froot = os.path.join(self.tmpdir, '.' + str(PID) + '_' + str(abs(hash(self))))
        else:
            self.froot = '.' + str(PID) + '_' + str(abs(hash(self)))
        self.t = 0
        
    def __setitem__(self, key, value):

        try:
            self.dmutex.acquire()
            try:
                self.d[key] = value
                self.curr += 1
                if self.curr==self.freq:
                    self.cycles += 1
                    # Dump the cache dictionary to disk...
                    fname = ''.join((self.froot,'#',str(self.cycles)))
                    # print self.d
                    cPickle.dump(self.d, open(fname, 'wb'))
                    # We index the cache keys and associate the
                    # cycle number to them, since the filename
                    # is further associated to the cycle number,
                    # finding the cache file associated to a
                    # dictionary key is a simple dictionary look-up
                    # operation, costing only O(1)...
                    for k in self.d.iterkeys():
                         self.cache[k] = self.cycles
                    self.d.clear()
                    self.curr = 0
            except Exception, e:
                import traceback
                print 'Exception:',e, traceback.extract_stack()
                traceback.print_stack()
        finally:
            self.dmutex.release()

    def __len__(self):
        # Return the 'virtual' length of the
        # dictionary

        # Length is the temporary cache length
        # plus size of disk caches. This assumes
        # that all the committed caches are still
        # present...
        return len(self.d) + self.cycles*self.freq
    
    def __getitem__(self, key):
        try:
            item = self.d[key]
            self.thits += 1
            return item
        except KeyError:
            try:
                item = self.dcache[key]
                self.mhits += 1
                return item
            except KeyError:
                t1 = time.time()
                # Load cache from disk...
                # Cache filename lookup is an O(1) operation...
                try:
                    fname = ''.join((self.froot,'#',str(self.cache[key])))
                except KeyError:
                    return None
                try:
                    # Always caches the last loaded entry
                    self.dcache = cPickle.load(open(fname,'rb'))
                    self.dhits += 1
                    # print time.time() - t1
                    self.t += time.time() - t1
                    
                    return self.dcache[key]
                except (OSError, IOError, EOFError,KeyError), e:
                    return None

    def clear(self):

        try:
            self.dmutex.acquire()
            self.d.clear()
            self.dcache.clear()
            
            # Remove cache filenames
            for k in self.cache.itervalues():
                fname = ''.join((self.froot,'#',str(k)))
                if os.path.isfile(fname):
                    # print 'Removing file',fname
                    os.remove(fname)

            self.cache.clear()
            # Reset counters
            self.curr = 0
            self.cycles = 0
            self.clear_counters()
        finally:
            self.dmutex.release()

    def clear_counters(self):
        self.dhits = 0
        self.thits = 0
        self.mhits = 0        
        self.t = 0

    def get_stats(self):
        """ Return stats as a dictionary """

        if len(self):
            average = float(self.t)/float(len(self))
        else:
            average = 0.0
            
        return { 'disk_hits' : self.dhits,
                 'mem_hits'  : self.mhits,
                 'temp_hits' : self.thits,
                 'time': self.t,
                 'average' : average }
        
