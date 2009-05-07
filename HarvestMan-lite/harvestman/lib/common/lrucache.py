# -- coding: utf-8
"""
lrucache.py - Length-limited O(1) LRU cache implementation

Author: Anand B Pillai <abpillai at gmail dot com>
    
Created Anand B Pillai Jun 26 2007 from ASPN Python Cookbook recipe #252524.

{http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/252524}

Original code courtesy Josiah Carlson.

Copyright (C) 2007, Anand B Pillai.
"""
import copy
import cPickle, os, sys
import time
import cStringIO
from threading import Semaphore
from dictcache import DictCache

class Node(object):
    # __slots__ = ['prev', 'next', 'me']

    def __init__(self, prev, me):
        self.prev = prev
        self.me = me
        self.next = None

    def __copy__(self):
        n = Node(self.prev, self.me)
        n.next = self.next

        return n

    #def __getstate__(self):
    #    return self
    
class LRU(object):
    """
    Implementation of a length-limited O(1) LRU queue.
    Built for and used by PyPE:
    http://pype.sourceforge.net
    Copyright 2003 Josiah Carlson.
    """
    def __init__(self, count, pairs=[]):
        self.count = max(count, 1)
        self.d = {}
        self.first = None
        self.last = None
        for key, value in pairs:
            self[key] = value

    def __copy__(self):
        lrucopy = LRU(self.count)
        lrucopy.first = copy.copy(self.first)
        lrucopy.last = copy.copy(self.last)
        lrucopy.d = self.d.copy()
        for key,value in self.iteritems():
            lrucopy[key] = value

        return lrucopy
        
    def __contains__(self, obj):
        return obj in self.d

    def __getitem__(self, obj):

        a = self.d[obj].me
        self[a[0]] = a[1]
        return a[1]

    def __setitem__(self, obj, val):
        if obj in self.d:
            del self[obj]
        nobj = Node(self.last, (obj, val))
        if self.first is None:
            self.first = nobj
        if self.last:
            self.last.next = nobj
        self.last = nobj
        self.d[obj] = nobj
        if len(self.d) > self.count:
            if self.first == self.last:
                self.first = None
                self.last = None
                return
            a = self.first
            if a:
                if a.next:
                    a.next.prev = None
                    self.first = a.next
                    a.next = None
                    try:
                       del self.d[a.me[0]]
                    except KeyError:
                       pass
                del a

    def __delitem__(self, obj):
        nobj = self.d[obj]
        if nobj.prev:
            nobj.prev.next = nobj.next
        else:
            self.first = nobj.next
        if nobj.next:
            nobj.next.prev = nobj.prev
        else:
            self.last = nobj.prev
        del self.d[obj]

    def __iter__(self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2

    def iteritems(self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me
            cur = cur2

    def iterkeys(self):
        return iter(self.d)

    def itervalues(self):
        for i,j in self.iteritems():
            yield j

    def keys(self):
        return self.d.keys()

    def clear(self):
        self.d.clear()

    def __len__(self):
        return len(self.d)


class LRU2(object):
    """
    Implementation of a length-limited O(1) LRU queue
    with disk caching. 
    """

    # This LRU drops off items to a disk dictionary cache
    # when older items are dropped. 
    def __init__(self, count, freq, cachedir='', pairs=[]):
        self.count = max(count, 1)
        self.d = {}
        self.lastmutex = Semaphore(1)
        self.first = None
        self.last = None
        for key, value in pairs:
            self[key] = value
        # Set the frequency to something like 1/100th of
        # the expected dictionary final size to achieve
        # best performance.
        self.diskcache = DictCache(freq, cachedir)
        
    def __copy__(self):
        lrucopy = LRU(self.count)
        lrucopy.first = copy.copy(self.first)
        lrucopy.last = copy.copy(self.last)
        lrucopy.d = self.d.copy()
        for key,value in self.iteritems():
            lrucopy[key] = value

        return lrucopy
        
    def __contains__(self, obj):
        return obj in self.d

    def __getitem__(self, obj):
       try:
           a = self.d[obj].me
           self[a[0]] = a[1]
           return a[1]
       except (KeyError,AttributeError):
           return self.diskcache[obj]
        
    def __setitem__(self, obj, val):
        if obj in self.d:
            del self[obj]
        nobj = Node(self.last, (obj, val))
        if self.first is None:
            self.first = nobj
        self.lastmutex.acquire()
        try:
            if self.last:
               self.last.next = nobj
            self.last = nobj
        except:
            pass
        self.lastmutex.release()
        self.d[obj] = nobj
        if len(self.d) > self.count:
            self.lastmutex.acquire()
            try:
                if self.first == self.last:
                    self.first = None
                    self.last = None
                    self.lastmutex.release()
                    return
            except:
                pass
            self.lastmutex.release()
            a = self.first
            if a:
                if a.next:
                    a.next.prev = None
                self.first = a.next
                a.next = None
            try:
                key, val = a.me[0], self.d[a.me[0]]
                del self.d[a.me[0]]
                del a
                self.diskcache[key] = val.me[1]
            except (KeyError,AttributeError):
                pass

    def __delitem__(self, obj):
        nobj = self.d[obj]
        if nobj.prev:
            nobj.prev.next = nobj.next
        else:
            self.first = nobj.next
        if nobj.next:
            nobj.next.prev = nobj.prev
        else:
            self.last = nobj.prev
        del self.d[obj]

    def __iter__(self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me[1]
            cur = cur2

    def iteritems(self):
        cur = self.first
        while cur != None:
            cur2 = cur.next
            yield cur.me
            cur = cur2

    def iterkeys(self):
        return iter(self.d)

    def itervalues(self):
        for i,j in self.iteritems():
            yield j

    def keys(self):
        return self.d.keys()

    def clear(self):
        self.d.clear()
        self.diskcache.clear()

    def __len__(self):
        return len(self.d)

    def get_stats(self):
        """ Return statistics as a dictionary """

        return self.diskcache.get_stats()
    
    def test(self, N):

        # Test to see if the diskcache works. Pass
        # the total number of items added to this
        # function...
        
        flag = True
        
        for x in range(N):
            if self[x] == None:
                flag = False
                break

        return flag

def test_lru2():
    import random
    
    n1, n2 = 10000, 5000
    
    l=LRU2(n1, 100)
    for x in range(n1):
        l[x] = x + 1 #urlparser.HarvestManUrlParser('htt://www.python.org/doc/current/tut/tut.html')

    # make use of first n2 random entries
    for x in range(n2):
        l[random.randint(0,n2)]
        
    # Add another n2 entries
    # This will cause the LRU to drop
    # entries and cache old entries.
    for x in range(n2):
        l[n1+x] = x + 1 #urlparser.HarvestManUrlParser('htt://www.python.org/doc/current/tut/tut.html') #  x + 1

    print l.test(n1+n2)

    print 'Random access test...'
    # Try to access random entries
    for x in range(n1+n2):
        # A random access will take more time since in-mem
        # cache will be emptied more often
        l[random.randint(0,n1+n2-1)]

    print
    print "Disk Hits",l.diskcache.dhits
    print "Mem Hits",l.diskcache.mhits
    print "Temp dict Hits",l.diskcache.thits    
    print "Time taken",l.diskcache.t
    print 'Hit %=>',100*float(l.diskcache.dhits)/float(n1+n2)
    print 'Time per disk cache hit=>',float(l.diskcache.t)/float(l.diskcache.dhits)
    print 'Average disk access time=>',float(l.diskcache.t)/float(len(l.diskcache))
    
    l.diskcache.clear_counters()

    print 'Sequential access test...'
    
    for x in range(n1+n2):
        # A sequential access will be faster since in-mem cache
        # will be hit sequentially...
        l[x]        

    print
    
    print "Disk Hits",l.diskcache.dhits
    print "Mem Hits",l.diskcache.mhits
    print "Temp dict Hits",l.diskcache.thits    
    print "Time taken",l.diskcache.t
    print 'Hit %=>',100*float(l.diskcache.dhits)/float(n1+n2)
    print 'Time per disk cache hit=>',float(l.diskcache.t)/float(l.diskcache.dhits)    
    print 'Average disk access time=>',float(l.diskcache.t)/float(len(l.diskcache))    
    
    l.clear()

if __name__=="__main__":
    test_lru2()
 ##    l = LRU2(10)
##     for x in range(10):
##         l[x] = x
##     print l.keys()
##     print l[3]
##     print l[3]
##     print l[9]
##     print l[9]
    
##     l[12]=11
##     l[13]=12
##     l[14]=15
##     l[15]=16
##     l[16]=17
##     l[17]=18
##     l[18]=19
##     l[19]=20
##     print l.keys()
##     print len(l)
##     print l[0]
##     print l[1]
##     print l[2]    
##     print copy.copy(l).keys()
