# -- coding: utf-8
""" common.py - Global functions for HarvestMan Program.
    This file is part of the HarvestMan software.
    For licensing information, see file LICENSE.TXT.

    Author: Anand B Pillai <abpillai at gmail dot com>

    Created: Jun 10 2003

    Aug 17 2006          Anand          Modifications for the new logging
                                        module.

    Feb 7 2007           Anand          Some changes. Added logconsole
                                        function. Split Initialize() to
                                        InitConfig() and InitLogger().
    Feb 26 2007          Anand          Replaced urlmappings dictionary
                                        with a WeakValueDictionary.

   Copyright (C) 2004 - Anand B Pillai.

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import weakref
import os, sys
import socket
import binascii
import copy
import threading
import shelve
import cStringIO
import traceback
import threading
import collections
import random
import cStringIO
import tokenize

from types import *
from singleton import Singleton

class Alias(Singleton):
    def __getattr__(self, name):
        try:
            return super(Alias, self).__getattr__(name)
        except AttributeError:
            return None
    pass

class AliasError(Exception):
    pass

class GlobalData(Singleton):
    def __getattr__(self, name):
        try:
            return super(Alias, self).__getattr__(name)
        except AttributeError:
            return None

# Namespace for global unique objects

# This varible holds each global object in HarvestMan
# If any module redefines an 'objects' variable locally, it
# is doing at its own peril!
objects = Alias()

# Namespace for global data
globaldata = GlobalData()
globaldata.userdebug = []


class SleepEvent(object):
    """ A class representing a timeout event. This can be
    used to passively wait for a given time-period instead of
    using time.sleep(...) """

    def __init__(self, sleeptime):
        self._sleeptime = sleeptime
        self.evt = threading.Event()
        self.evt.set()

    def sleep(self):
        self.evt.clear()
        self.evt.wait(self._sleeptime)
        self.evt.set()

class RandomSleepEvent(SleepEvent):
    """ A class representing a timeout event. This can be
    used to passively wait for a given time-period instead of
    using time.sleep(...) """

    def sleep(self):
        self.evt.clear()
        self.evt.wait(random.random()*self._sleeptime)
        self.evt.set()
    
class DummyStderr(object):
    """ A dummy class to imitate stderr """
    
    def write(self, msg):
        pass

class CaselessDict(dict):

    def __init__(self, mapping=None):
        if mapping:
            if type(mapping) is dict:
                for k,v in d.items():
                    self.__setitem__(k, v)
            elif type(mapping) in (list, tuple):
                d = dict(mapping)
                for k,v in d.items():
                    self.__setitem__(k, v)
                    
        # super(CaselessDict, self).__init__(d)
        
    def __setitem__(self, name, value):

        if type(name) in StringTypes:
            super(CaselessDict, self).__setitem__(name.lower(), value)
        else:
            super(CaselessDict, self).__setitem__(name, value)

    def __getitem__(self, name):
        if type(name) in StringTypes:
            return super(CaselessDict, self).__getitem__(name.lower())
        else:
            return super(CaselessDict, self).__getitem__(name)

    def __copy__(self):
        pass

            
class Ldeque(collections.deque):
    """ Length-limited deque """
    
    def __init__(self, count=10):
        self.max = count
        super(Ldeque, self).__init__()

    def append(self, item):
        super(Ldeque, self).append(item)
        if len(self)>self.max:
            # if size exceeds, pop from left
            self.popleft()

    def appendleft(self, item):
        super(Ldeque, self).appendleft(item)
        if len(self)>self.max:
            # if size exceeds, pop from right
            self.pop()            

    def index(self, item):
        """ Return the index of an item from the deque """
        
        return list(self).index(item)

    def remove(self, item):
        """ Remove an item from the deque """
        
        idx = self.index(item)
        self.__delitem__(idx)      

def SysExceptHook(typ, val, tracebak):
    """ Dummy function to replace sys.excepthook """
    pass


def SetAlias(obj):
    """ Set unique alias for the object """

    # Alias is another name for the object, it should be unique
    # The object's class should have a field name 'alias'
    if getattr(obj, 'alias') == None:
        raise AliasError, "object does not define 'alias' attribute!"

    setattr(objects, obj.alias, obj)

def SetLogFile():

    logfile = objects.config.logfile
    if logfile:
        objects.logger.setLogSeverity(objects.config.verbosity)
        # If simulation is turned off, add file-handle
        if not objects.config.simulate:
            objects.logger.addLogHandler('FileHandler',logfile)

def SetUserDebug(message):
    """ Used to store error messages related
    to user settings in the config file/project file.
    These will be printed at the end of the program """

    if message:
        try:
            globaldata.userdebug.index(message)
        except:
            globaldata.userdebug.append(message)

def SetLogSeverity():
    objects.logger.setLogSeverity(objects.config.verbosity)    
    
def wasOrWere(val):
    """ What it says """

    if val > 1: return 'were'
    else: return 'was'

def plural((s, val)):
    """ What it says """

    if val>1:
        if s[len(s)-1] == 'y':
            return s[:len(s)-1]+'ies'
        else: return s + 's'
    else:
        return s

# file type identification functions
# this is the precursor of a more generic file identificator
# based on the '/etc/magic' file on unices.

signatures = { "gif" : [0, ("GIF87a", "GIF89a")],
               "jpeg" :[6, ("JFIF",)],
               "bmp" : [0, ("BM6",)]
             }
aliases = { "gif" : (),                       # common extension aliases
            "jpeg" : ("jpg", "jpe", "jfif"),
            "bmp" : ("dib",) }

def bin_crypt(data):
    """ Encryption using binascii and obfuscation """

    if data=='':
        return ''

    try:
        return binascii.hexlify(obfuscate(data))
    except TypeError, e:
        debug('Error in encrypting data: <',data,'>', e)
        return data
    except ValueError, e:
        debug('Error in encrypting data: <',data,'>', e)
        return data

def bin_decrypt(data):
    """ Decrypttion using binascii and deobfuscation """

    if data=='':
        return ''

    try:
        return unobfuscate(binascii.unhexlify(data))
    except TypeError, e:
        logconsole('Error in decrypting data: <',data,'>', e)
        return data
    except ValueError, e:
        logconsole('Error in decrypting data: <',data,'>', e)
        return data


def obfuscate(data):
    """ Obfuscate a string using repeated xor """

    out = ""
    import operator

    e0=chr(operator.xor(ord(data[0]), ord(data[1])))
    out = "".join((out, e0))

    x=1
    eprev=e0
    for x in range(1, len(data)):
        ax=ord(data[x])
        ex=chr(operator.xor(ax, ord(eprev)))
        out = "".join((out,ex))
        eprev = ex

    return out

def unobfuscate(data):
    """ Unobfuscate a xor obfuscated string """

    out = ""
    x=len(data) - 1

    import operator

    while x>1:
        apos=data[x]
        aprevpos=data[x-1]
        epos=chr(operator.xor(ord(apos), ord(aprevpos)))
        out = "".join((out, epos))
        x -= 1

    out=str(reduce(lambda x, y: y + x, out))
    e2, a2 = data[1], data[0]
    a1=chr(operator.xor(ord(a2), ord(e2)))
    a1 = "".join((a1, out))
    out = a1
    e1,a1=out[0], data[0]
    a0=chr(operator.xor(ord(a1), ord(e1)))
    a0 = "".join((a0, out))
    out = a0

    return out

def send_url(data, host, port):
    
    cfg = objects.config
    if cfg.urlserver_protocol == 'tcp':
        return send_url_tcp(data, host, port)
    elif cfg.urlserver_protocol == 'udp':
        return send_url_udp(data, host, port)
    
def send_url_tcp(data, host, port):
    """ Send url to url server """

    # Return's server response if connection
    # succeeded and null string if failed.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        sock.sendall(data)
        response = sock.recv(8192)
        sock.close()
        return response
    except socket.error, e:
        # print 'url server error:',e
        pass

    return ''

def send_url_udp(data, host, port):
    """ Send url to url server """

    # Return's server response if connection
    # succeeded and null string if failed.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data,0,(host, port))
        response, addr = sock.recvfrom(8192, 0)
        sock.close()
        return response
    except socket.error:
        pass

    return ''

def ping_urlserver(host, port):
    
    cfg = objects.config
    
    if cfg.urlserver_protocol == 'tcp':
        return ping_urlserver_tcp(host, port)
    elif cfg.urlserver_protocol == 'udp':
        return ping_urlserver_udp(host, port)
        
def ping_urlserver_tcp(host, port):
    """ Ping url server to see if it is alive """

    # Returns server's response if server is
    # alive & null string if server is not alive.
    try:
        debug('Pinging server at (%s:%d)' % (host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
        # Send a small packet
        sock.sendall("ping")
        response = sock.recv(8192)
        if response:
            debug('Url server is alive')
        sock.close()
        return response
    except socket.error:
        debug('Could not connect to (%s:%d)' % (host, port))
        return ''

def ping_urlserver_udp(host, port):
    """ Ping url server to see if it is alive """

    # Returns server's response if server is
    # alive & null string if server is not alive.
    try:
        debug('Pinging server at (%s:%d)' % (host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send a small packet
        sock.sendto("ping", 0, (host,port))
        response, addr = sock.recvfrom(8192,0)
        if response:
            debug('Url server is alive')
        sock.close()
        return response
    except socket.error:
        debug('Could not connect to (%s:%d)' % (host, port))
        return ''    

def GetTempDir():
    """ Return the temporary directory """

    # Currently used by hget
    tmpdir = max(map(lambda x: os.environ.get(x, ''), ['TEMP','TMP','TEMPDIR','TMPDIR']))

    if tmpdir=='':
        # No temp dir env variable
        if os.name == 'posix':
            if os.path.isdir('/tmp'):
                return '/tmp'
            elif os.path.isdir('/usr/tmp'):
                return '/usr/tmp'
        elif os.name == 'nt':
            profiledir = os.environ.get('USERPROFILE','')
            if profiledir:
                return os.path.join(profiledir,'Local Settings','Temp')
    else:
        return os.path.abspath(tmpdir)

def GetMyTempDir():
    """ Return temporary directory for HarvestMan. Also creates
    it if the directory is not there """

    # This is tempdir/HarvestMan
    tmpdir = os.path.join(GetTempDir(), 'harvestman')
    if not os.path.isdir(tmpdir):
        try:
            os.makedirs(tmpdir)
        except OSError, e:
            return ''

    return tmpdir

# Modified to use the logger object
def info(arg, *args):
    """ Print basic information, will print if verbosity is >=1 """

    # Setting verbosity to 1 will print the basic
    # messages like project info and final download stats.
    objects.logger.info(arg, *args)

def moreinfo(arg, *args):
    """ Print more information, will print if verbosity is >=2 """

    # Setting verbosity to 2 will print the basic info
    # as well as detailed information regarding each downloaded link.
    objects.logger.moreinfo(arg, *args)    

def extrainfo(arg, *args):
    """ Print extra information, will print if verbosity is >=3 """

    # Setting verbosity to 3 will print more information on each link
    # as well as information of each thread downloading the link, as
    # well as some more extra information.
    objects.logger.extrainfo(arg, *args)    

def debug(arg, *args):
    """ Print debug information, will print if verbosity is >=4 """

    # Setting verbosity to 4 will print maximum information
    # plus extra debugging information.
    objects.logger.debug(arg, *args)    

def moredebug(arg, *args):
    """ Print more debug information, will print if verbosity is >=5 """

    # Setting verbosity to 5 will print maximum information
    # plus maximum debugging information.
    objects.logger.moredebug(arg, *args)        

def logconsole(arg, *args):
    """ Log directly to sys.stdout using print """

    # Setting verbosity to 5 will print maximum information
    # plus maximum debugging information.
    objects.logger.logconsole(arg, *args)        

def logtraceback(console=False):
    """ Log the most recent exception traceback. By default
    the trace goes only to the log file """

    s = cStringIO.StringIO()
    traceback.print_tb(sys.exc_info()[-1], None, s)
    if not console:
        objects.logger.disableConsoleLogging()
    # Log to logger
    objects.logger.debug(s.getvalue())
    # Enable console logging again
    objects.logger.enableConsoleLogging()    

def hexit(arg):
    """ Exit wrapper for HarvestMan """

    print_traceback()
    sys.exit(arg)
    
def print_traceback():
    print 'Printing error traceback for debugging...'
    traceback.print_tb(sys.exc_info()[-1], None, sys.stdout)

# Effbot's simple_eval function which is a safe replacement
# for Python's eval for tuples...

def atom(next, token):
    if token[1] == "(":
        out = []
        token = next()
        while token[1] != ")":
            out.append(atom(next, token))
            token = next()
            if token[1] == ",":
                token = next()
        return tuple(out)
    elif token[0] is tokenize.STRING:
        return token[1][1:-1].decode("string-escape")
    elif token[0] is tokenize.NUMBER:
        try:
            return int(token[1], 0)
        except ValueError:
            return float(token[1])
    raise SyntaxError("malformed expression (%s)" % token[1])

def simple_eval(source):
    src = cStringIO.StringIO(source).readline
    src = tokenize.generate_tokens(src)
    res = atom(src.next, src.next())
    if src.next()[0] is not tokenize.ENDMARKER:
        raise SyntaxError("bogus data after expression")
    return res

def set_aliases(path=None):

    if path != None:
        sys.path.append(path)
        
    import config
    SetAlias(config.HarvestManStateObject())

    import datamgr
    import rules
    import connector
    import urlqueue
    import logger
    import event

    SetAlias(logger.HarvestManLogger())
    
    # Data manager object
    dmgr = datamgr.HarvestManDataManager()
    dmgr.initialize()
    SetAlias(dmgr)
    
    # Rules checker object
    ruleschecker = rules.HarvestManRulesChecker()
    SetAlias(ruleschecker)
    
    # Connector manager object
    connmgr = connector.HarvestManNetworkConnector()
    SetAlias(connmgr)
    
    # Connector factory
    conn_factory = connector.HarvestManUrlConnectorFactory(objects.config.connections)
    SetAlias(conn_factory)
    
    queuemgr = urlqueue.HarvestManCrawlerQueue()
    SetAlias(queuemgr)
    
    SetAlias(event.HarvestManEvent())
        
def test_sgmlop():
    """ Test whether sgmlop is available and working """

    html="""\
    <html><
    title>Test sgmlop</title>
    <body>
    <p>This is a pargraph</p>
    <img src="img.jpg"/>
    <a href="http://www.python.org'>Python</a>
    </body>
    </html>
    """
    
    # Return True for working and False for not-working
    # or not-present...
    try:
        import sgmlop
        
        class DummyHandler(object):
            links = []
            def finish_starttag(self, tag, attrs):
                self.links.append(tag)
                pass
            
        parser = sgmlop.SGMLParser()
        parser.register(DummyHandler())
        parser.feed(html)

        # Check if we got all the links...
        if len(DummyHandler.links)==4:
            return True
        else:
            return False
        
    except ImportError, e:
        return False


if __name__=="__main__":
    pass
    
