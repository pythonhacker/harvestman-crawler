# -- coding: utf-8
""" robotparser.py - Robot Exclusion Principle for python.
    This module is part of the HarvestMan program.

    This module is a modified version of robotparser.py supplied
    with Python standard library. The author does not assert
    any copyright on this module.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    =============== Original Copyright ============================
    robotparser.py
    
    Copyright (C) 2000  Bastian Kleineidam

    You can choose between two licenses when using this package:
    1) GNU GPLv2
    2) PYTHON 2.0 OPEN SOURCE LICENSE

    The robots.txt Exclusion Protocol is implemented as specified in
    http://info.webcrawler.com/mak/projects/robots/norobots-rfc.html

    ================ End Original Copyright =========================

    Jan 5 2006          Anand   Fix for EIAO ticket #74, small change
                                in open of URLopener class, Also moved
                                import of HarvestManUrlConnector to top.

    Jan 8 2006         Anand    Updated this file from EIAO robacc
                                repository.
    Jan 10 2006          Anand   Converted from dos to unix format (removed Ctrl-Ms).
                                

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import re,urlparse,urllib
from connector import HarvestManUrlConnector

__all__ = ["RobotFileParser"]

debug = 0

def _basicdebug(msg):
    if debug>=1: print msg

def _moredebug(msg):
    if debug>=2: print msg

def _verbosedebug(msg):
    if debug>=3: print msg
    
def _debug(msg):
    if debug: print msg


import socket

class RobotFileParser(object):
    def __init__(self, url=''):
        self.entries = []
        self.disallow_all = 0
        self.allow_all = 0
        self.set_url(url)
        self.last_checked = 0
        # value of last return value
        # of can_fetch() method
        self.cache_val = 0
        # value of url in last call
        # to can_fetch() method
        self.directory = ''

    def mtime(self):
        return self.last_checked

    def modified(self):
        import time
        self.last_checked = time.time()

    def set_url(self, url):
        self.url = url
        self.host, self.path = urlparse.urlparse(url)[1:3]

    def get_server(self):
        urltuple = urlparse.urlparse(self.url)
        return urltuple[1]
    
    def read(self):
        
        opener = URLopener()
        f = opener.open(self.url)
        # bug: we need to check this value against '0'
        if f is None: return -1
        try:
            lines = f.readlines()
        except AttributeError, e:
            return 0
        except socket.error, e:
            print e
            return 0
        
        self.errcode = opener.errcode
        if self.errcode == 401 or self.errcode == 403:
            self.disallow_all = 1
            _moredebug("disallow all")
        elif self.errcode >= 400:
            self.allow_all = 1
            _moredebug("allow all")
        elif self.errcode == 200 and lines:
            _moredebug("parse lines")
            self.parse(lines)

        return 0

    def parse(self, lines):
        """parse the input lines from a robot.txt file.
           We allow that a user-agent: line is not preceded by
           one or more blank lines."""
           
        state = 0
        linenumber = 0
        entry = Entry()

        for line in lines:
            line = line.strip()
            linenumber = linenumber + 1
            if not line:
                if state==1:
                    _verbosedebug("line %d: warning: you should insert"
                           " allow: or disallow: directives below any"
                           " user-agent: line" % linenumber)
                    entry = Entry()
                    state = 0
                elif state==2:
                    self.entries.append(entry)
                    entry = Entry()
                    state = 0
            # remove optional comment and strip line
            i = line.find('#')
            if i>=0:
                line = line[:i]
            line = line.strip()
            if not line:
                continue
            line = line.split(':', 1)
            if len(line) == 2:
                line[0] = line[0].strip().lower()
                line[1] = line[1].strip()
                if line[0] == "user-agent":
                    if state==2:
                        _verbosedebug("line %d: warning: you should insert a blank"
                               " line before any user-agent"
                               " directive" % linenumber)
                        self.entries.append(entry)
                        entry = Entry()
                    entry.useragents.append(line[1])
                    state = 1
                elif line[0] == "disallow":
                    if state==0:
                        _verbosedebug("line %d: error: you must insert a user-agent:"
                               " directive before this line" % linenumber)
                    else:
                        entry.rulelines.append(RuleLine(line[1], 0))
                        state = 2
                elif line[0] == "allow":
                    if state==0:
                        _verbosedebug("line %d: error: you must insert a user-agent:"
                               " directive before this line" % linenumber)
                    else:
                        entry.rulelines.append(RuleLine(line[1], 1))
                else:
                    _verbosedebug("line %d: warning: unknown key %s" % (linenumber,
                               line[0]))
            else:
                _verbosedebug("line %d: error: malformed line %s"%(linenumber, line))
        if state==2:
            self.entries.append(entry)
        _moredebug("Parsed rules:\n%s" % str(self))

    def get_directory(self):
        return self.directory
    
    def can_fetch(self, useragent, url):
        """using the parsed robots.txt decide if useragent can fetch url"""
        _moredebug("Checking robot.txt allowance for:\n  user agent: %s\n  url: %s" %
               (useragent, url))
        # cache value
        self.directory = url
        if self.disallow_all:
            self.cache_val = 0
            return 0
        if self.allow_all:
            self.cache_val = 1
            return 1
        # search for given user agent matches
        # the first match counts
        url = urllib.quote(urlparse.urlparse(url)[2]) or "/"
        
        for entry in self.entries:
            if entry.applies_to(useragent):
                return entry.allowance(url)
        # agent not found ==> access granted
        self.cache_val = 1
        return 1


    def __str__(self):
        ret = ""
        for entry in self.entries:
            ret = ret + str(entry) + "\n"
        return ret


class RuleLine(object):
    """A rule line is a single "Allow:" (allowance==1) or "Disallow:"
       (allowance==0) followed by a path."""
    def __init__(self, path, allowance):
        self.path = urllib.quote(path)
        self.allowance = allowance

    def applies_to(self, filename):
        return self.path=="*" or re.match(self.path, filename)

    def __str__(self):
        return (self.allowance and "Allow" or "Disallow")+": "+self.path


class Entry(object):
    """An entry has one or more user-agents and zero or more rulelines"""
    def __init__(self):
        self.useragents = []
        self.rulelines = []

    def __str__(self):
        ret = ""
        for agent in self.useragents:
            ret = ret + "User-agent: "+agent+"\n"
        for line in self.rulelines:
            ret = ret + str(line) + "\n"
        return ret

    def applies_to(self, useragent):
        """check if this entry applies to the specified agent"""
        # split the name token and make it lower case
        useragent = useragent.split("/")[0].lower()
        for agent in self.useragents:
            if agent=='*':
                # we have the catch-all agent
                return 1
            agent = agent.lower()
            # don't forget to re.escape
            if re.search(re.escape(useragent), agent):
                return 1
        return 0

    def allowance(self, filename):
        """Preconditions:
        - our agent applies to this entry
        - filename is URLdecoded"""
        for line in self.rulelines:
            _verbosedebug((filename, str(line), line.allowance))
            if line.applies_to(filename):
                return line.allowance
        return 1

class URLopener(urllib.FancyURLopener):
    
    def __init__(self, *args):
        apply(urllib.FancyURLopener.__init__, (self,) + args)
        self.errcode = 200
        self.tries = 0
        self.maxtries = 10

    def http_error_default(self, url, fp, errcode, errmsg, headers):
        self.errcode = errcode
        return urllib.FancyURLopener.http_error_default(self, url, fp, errcode,
                                                        errmsg, headers)

    def http_error_302(self, url, fp, errcode, errmsg, headers, data=None):
        self.tries += 1
        if self.tries >= self.maxtries:
            return self.http_error_default(url, fp, 500,
                                           "Internal Server Error: Redirect Recursion",
                                           headers)
        result = urllib.FancyURLopener.http_error_302(self, url, fp, errcode,
                                                      errmsg, headers, data)
        self.tries = 0
        return result

    def open(self, url):
        return HarvestManUrlConnector().robot_urlopen(url)
    
def _check(a,b):
    if not b:
        ac = "access denied"
    else:
        ac = "access allowed"
    if a!=b:
        _basicdebug("failed")
    else:
        _basicdebug("ok (%s)" % ac)
    _basicdebug('')

def _test():
    global debug
    rp = RobotFileParser()
    debug = 2

    # robots.txt that exists, gotten to by redirection
    rp.set_url('http://www.musi-cal.com/robots.txt')
    #rp.set_url('http://www.lycos.com/robots.txt')
    rp.read()

    return
    # test for re.escape
    _check(rp.can_fetch('*', 'http://www.musi-cal.com/'), 1)
    # this should match the first rule, which is a disallow
    _check(rp.can_fetch('', 'http://www.musi-cal.com/'), 0)
    # various cherry pickers
    _check(rp.can_fetch('CherryPickerSE',
                       'http://www.musi-cal.com/cgi-bin/event-search'
                       '?city=San+Francisco'), 0)
    _check(rp.can_fetch('CherryPickerSE/1.0',
                       'http://www.musi-cal.com/cgi-bin/event-search'
                       '?city=San+Francisco'), 0)
    _check(rp.can_fetch('CherryPickerSE/1.5',
                       'http://www.musi-cal.com/cgi-bin/event-search'
                       '?city=San+Francisco'), 0)
    # case sensitivity
    _check(rp.can_fetch('ExtractorPro', 'http://www.musi-cal.com/blubba'), 0)
    _check(rp.can_fetch('extractorpro', 'http://www.musi-cal.com/blubba'), 0)
    # substring test
    _check(rp.can_fetch('toolpak/1.1', 'http://www.musi-cal.com/blubba'), 0)
    # tests for catch-all * agent
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/search'), 0)
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/Musician/me'), 1)
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/'), 1)
    _check(rp.can_fetch('spam', 'http://www.musi-cal.com/'), 1)

    rp.set_url('http://members.fortunecity.com/robots.txt')
    rp.read()
    _check(rp.can_fetch('Python urllib2 module', 'http://www.fortunecity.com/login.shtml'), 1)
    
    # robots.txt that does not exist
    rp.set_url('http://www.lycos.com/robots.txt')
    rp.read()
    _check(rp.can_fetch('Mozilla', 'http://www.lycos.com/search'), 1)
    

if __name__ == '__main__':
    _test()
