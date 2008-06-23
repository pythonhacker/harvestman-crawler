# -- coding: utf-8
# progress.py - Module which provides a generic Text Progress bar
# and a Progress bar class.
#
# Created: Anand B Pillai Mar 9 2007 by copying and merging
# Progress/TextProgress classes from S.M.A.R.T version 0.5.
# with some modifications for HarvestMan.
#
# This module is part of the HarvestMan program.
# For licensing information see the file LICENSE.txt that
# is included in this distribution.
#
#----------Original copyright/license information-------------------------
#
# Copyright (c) 2005 Canonical
# Copyright (c) 2004 Conectiva, Inc.
#
# Written by Gustavo Niemeyer <niemeyer@conectiva.com>
#
# This file is part of Smart Package Manager.
#
# Smart Package Manager is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# Smart Package Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Smart Package Manager; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#-------------- End of original copyright ---------------------------------
#
# Copyright (C) 2007, Anand B Pillai
#

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import posixpath
import time
import sys
import struct
import os

if os.name == 'posix':
    import fcntl
    import termios

import thread
import time
import sys

INTERVAL = 0.1

class Progress(object):

    def __init__(self):
        self.__topic = ""
        self.__progress = (0, 0, {}) # (current, total, data)
        self.__lastshown = None
        self.__done = False
        self.__subtopic = {}
        self.__subprogress = {} # (subcurrent, subtotal, fragment, subdata)
        self.__sublastshown = {}
        self.__subdone = {}
        self.__lasttime = 0
        self.__lock = thread.allocate_lock()
        self.__hassub = False

    def getScreenWidth(self):
        if os.name == 'posix':
            s = struct.pack('HHHH', 0, 0, 0, 0)
            try:
                x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
            except IOError:
                return 80

            return struct.unpack('HHHH', x)[1]
        else:
            return 80

    def lock(self):
        self.__lock.acquire()

    def unlock(self):
        self.__lock.release()

    def start(self):
        pass

    def stop(self):
        self.__topic = ""
        self.__progress = (0, 0, {})
        self.__lastshown = None
        self.__done = False
        self.__subtopic.clear()
        self.__subprogress.clear()
        self.__sublastshown.clear()
        self.__subdone.clear()
        self.__lasttime = 0
        self.__hassub = False

    def setHasSub(self, flag):
        self.__hassub = flag

    def getHasSub(self):
        return self.__hassub

    def getSubCount(self):
        return len(self.__subprogress)

    def show(self):
        now = time.time()
        if self.__lasttime > now-INTERVAL:
            return
        self.__lock.acquire()
        try:
            self.__lasttime = now
            current, total, data = self.__progress
            subexpose = []
            for subkey in self.__subprogress.keys():
                sub = self.__subprogress[subkey]
                subcurrent, subtotal, fragment, subdata = sub
                subpercent = int(100*float(subcurrent)/(subtotal or 1))
                if fragment:
                    current += int(fragment*float(subpercent)/100)
                subtopic = self.__subtopic.get(subkey)
                if (subkey not in self.__subdone and
                    sub == self.__sublastshown.get(subkey)):
                    continue
                self.__sublastshown[subkey] = sub
                subdone = False
                if subpercent == 100:
                    self.__subdone[subkey] = True
                    subdone = True
                    if fragment:
                        _current, _total, _data = self.__progress
                        self.__progress = (_current+fragment, _total, _data)
                        if _current == _total:
                            self.__lasttime = 0
                elif subkey in self.__subdone:
                    subdone = subkey in self.__subdone
                subexpose.append((subkey, subtopic, subpercent,
                                  subdata, subdone))
            topic = self.__topic
            percent = int(100*float(current)/(total or 1))
            if subexpose:
                for info in subexpose:
                    self.expose(topic, percent, *info)
                    if info[-1]:
                        subkey = info[0]
                        del self.__subprogress[subkey]
                        del self.__sublastshown[subkey]
                        del self.__subtopic[subkey]
                if percent == 100 and len(self.__subprogress) == 0:
                    self.__done = True
                self.expose(topic, percent, None, None, None, data,
                            self.__done)
            elif (topic, percent) != self.__lastshown:
                if percent == 100 and len(self.__subprogress) == 0:
                    self.__done = True
                self.expose(topic, percent, None, None, None, data,
                            self.__done)
        finally:
            self.__lock.release()

    def expose(self, topic, percent, subkey, subtopic, subpercent, data, done):
        pass

    def setTopic(self, topic):
        self.__topic = topic

    def get(self):
        return self.__progress

    def set(self, current, total, data={}):
        self.__lock.acquire()
        try:
            if self.__done:
                return
            if current > total:
                current = total
            self.__progress = (current, total, data)
            if current == total:
                self.__lasttime = 0
        finally:
            self.__lock.release()

    def add(self, value):
        self.__lock.acquire()
        try:
            if self.__done:
                return
            current, total, data = self.__progress
            current += value
            if current > total:
                current = total
            self.__progress = (current, total, data)
            if current == total:
                self.__lasttime = 0
        finally:
            self.__lock.release()

    def addTotal(self, value):
        self.__lock.acquire()
        try:
            if self.__done:
                return
            current, total, data = self.__progress
            self.__progress = (current, total+value, data)
        finally:
            self.__lock.release()

    def setSubTopic(self, subkey, subtopic):
        self.__lock.acquire()
        try:
            if subkey not in self.__subtopic:
                self.__lasttime = 0
            self.__subtopic[subkey] = subtopic
        finally:
            self.__lock.release()

    def getSub(self, subkey):
        return self.__subprogress.get(subkey)

    def getSubData(self, subkey, _none=[None]):
        return self.__subprogress.get(subkey, _none)[-1]

    def setSub(self, subkey, subcurrent, subtotal, fragment=0, subdata={}):
        self.__lock.acquire()
        try:
            if self.__done or subkey in self.__subdone:
                return
            if subkey not in self.__subtopic:
                self.__subtopic[subkey] = ""
                self.__lasttime = 0
            if subcurrent > subtotal:
                subcurrent = subtotal
            if subcurrent == subtotal:
                self.__lasttime = 0
            self.__subprogress[subkey] = (subcurrent, subtotal,
                                          fragment, subdata)
        finally:
            self.__lock.release()

    def addSub(self, subkey, value):
        self.__lock.acquire()
        try:
            if self.__done or subkey in self.__subdone:
                return
            (subcurrent, subtotal,
             fragment, subdata) = self.__subprogress[subkey]
            subcurrent += value
            if subcurrent > subtotal:
                subcurrent = subtotal
            self.__subprogress[subkey] = (subcurrent, subtotal,
                                          fragment, subdata)
            if subcurrent == subtotal:
                self.__lasttime = 0
        finally:
            self.__lock.release()

    def addSubTotal(self, subkey, value):
        self.__lock.acquire()
        try:
            if self.__done or subkey in self.__subdone:
                return
            (subcurrent, subtotal,
             fragment, subdata) = self.__subprogress[subkey]
            self.__subprogress[subkey] = (subcurrent, subtotal+value,
                                          fragment, subdata)
        finally:
            self.__lock.release()

    def setDone(self):
        self.__lock.acquire()
        try:
            current, total, data = self.__progress
            self.__progress = (total, total, data)
            self.__lasttime = 0
        finally:
            self.__lock.release()

    def setSubDone(self, subkey):
        self.__lock.acquire()
        try:
            if subkey in self.__subdone:
                return
            (subcurrent, subtotal,
             fragment, subdata) = self.__subprogress[subkey]
            if subcurrent != subtotal:
                self.__subprogress[subkey] = (subtotal, subtotal,
                                              fragment, subdata)
            self.__lasttime = 0
        finally:
            self.__lock.release()

    def setStopped(self):
        self.__lock.acquire()
        self.__done = True
        self.__lasttime = 0
        self.__lock.release()

    def setSubStopped(self, subkey):
        self.__lock.acquire()
        self.__subdone[subkey] = True
        self.__lasttime = 0
        self.__lock.release()

    def resetSub(self, subkey):
        self.__lock.acquire()
        try:
            if subkey in self.__subdone:
                del self.__subdone[subkey]
            if subkey in self.__subprogress:
                (subcurrent, subtotal,
                 fragment, subdata) = self.__subprogress[subkey]
                self.__subprogress[subkey] = (0, subtotal, fragment, {})
            self.__lasttime = 0
        finally:
            self.__lock.release()

class TextProgress(Progress):

    def __init__(self):
        Progress.__init__(self)
        self._lasttopic = None
        self._lastsubkey = None
        self._lastsubkeystart = 0
        self._fetchermode = False
        self._nolengthmode = False
        # Cursor direction for no length mode
        self._direction = 0
        self._current = 0.0
        self._seentopics = {}
        self._addline = False
        self.setScreenWidth(self.getScreenWidth())
        #signal.signal(signal.SIGWINCH, self.handleScreenWidth)

    def setScreenWidth(self, width):
        self._screenwidth = width
        self._topicwidth = int(width*0.4)
        self._hashwidth = int(width-self._topicwidth-1)
        self._topicmask = "%%-%d.%ds" % (self._topicwidth, self._topicwidth)
        self._topicmaskn = "%%4d:%%-%d.%ds" % (self._topicwidth-5,
                                               self._topicwidth-5)

    def handleScreenWidth(self, signum, frame):
        self.setScreenWidth(self.getScreenWidth())

    def setFetcherMode(self, flag):
        self._fetchermode = flag

    def setNoLengthMode(self, flag):
        self._nolengthmode = flag
        
    def stop(self):
        Progress.stop(self)
        print

    def expose(self, topic, percent, subkey, subtopic, subpercent, data, done):

        out = sys.stdout
        if not out.isatty() and not done:
            return
        if self.getHasSub():
            if topic != self._lasttopic:
                self._lasttopic = topic
                out.write(" "*(self._screenwidth-1)+"\r")

                if self._addline:
                    print
                else:
                    self._addline = True
            if not subkey:
                return
            if not done:
                now = time.time()
                if subkey == self._lastsubkey:
                    if (self._lastsubkeystart+2 < now and
                        self.getSubCount() > 1):
                        return
                else:
                    if (self._lastsubkeystart+2 > now and
                        self.getSubCount() > 1):
                        return
                    self._lastsubkey = subkey
                    self._lastsubkeystart = now
            elif subkey == self._lastsubkey:
                    self._lastsubkeystart = 0
            current = subpercent
            topic = subtopic
        else:
            current = percent

        n = data.get("item-number")
        if n:
            if len(topic) > self._topicwidth-6:
                topic = topic[:self._topicwidth-8]+".."
            out.write(self._topicmaskn % (n, topic))
        else:
            if len(topic) > self._topicwidth-1:
                topic = topic[:self._topicwidth-3]+".."
            out.write(self._topicmask % topic)

        if not done:
            speed = data.get("speed")
            if speed:
                suffix = "(%s%% %s %s) \r" % (str(current), speed, data.get("eta"))
            else:
                suffix = "(%3d%%) \r" % current
        elif subpercent is None:
            suffix = "[%3d%%] \n" % current
        else:
            suffix = "[%3d%%] \n" % percent

        if self._nolengthmode:
            hashwidth = self._hashwidth - 8
            hashes = int(hashwidth*current/100)
            suffix = "(%3s) \r" % '...'
            out.write("[")
            #if self._direction==0:
            leftwidth = hashes - 1
            rightwidth = hashwidth - hashes -3
            #elif self._direction==1:
            #    leftwidth = hashwidth - hashes - 3
            #    rightwidth = hashes

            # print leftwidth, rightwidth, hashwidth
            #if rightwidth==0:
            #    # Switch direction
            #    self._direction = 1
            #elif leftwidth==0:
            #    self._direction = 0
                
            if leftwidth >=0: out.write(" "*leftwidth)
            out.write("<=>")
            if rightwidth >=0: out.write(" "*(rightwidth))
            out.write("]")
            out.write(suffix)
            out.flush()
            # Sleep for some time
            time.sleep(0.1)
        else:
            hashwidth = self._hashwidth -len(suffix)
            hashes = int(hashwidth*current/100)
            
            out.write("[")
            out.write("="*(hashes-1))
            out.write(">")
            out.write(" "*(hashwidth-hashes-1))
            out.write("]")
            out.write(suffix)
            out.flush()            

def test():
    prog = TextProgress()
    data = {"item-number": 0}
    total, subtotal = 10, 10
    prog.setHasSub(True)
    prog.start()
    prog.setTopic("Installing packages..")
    #data["item-number"] = 1
    for n in range(1, total+1):
        prog.set(n, total)
        for i in range(0,subtotal+1):
            prog.setSubTopic(n, "package-name%d" % n)
            prog.setSub(n, i, subtotal) #, subdata=data)
            prog.show()
            time.sleep(0.1)
        
    prog.stop()

def test2():
    prog = TextProgress()
    data = {"item-number": 0}
    total, subtotal = 10, 100
    prog.setFetcherMode(True)
    prog.setHasSub(True)
    prog.start()
    prog.setTopic("Installing packages...")
    for n in range(1,total+1):
        data["item-number"] = n
        prog.set(n, total)
        prog.setSubTopic(n, "package-name%d" % n)
        for i in range(0,subtotal+1):
            prog.setSub(n, i, subtotal, subdata=data)
            prog.show()
            # time.sleep(0.1)
    prog.stop()
if __name__ == "__main__":
    test()

# vim:ts=4:sw=4:et
