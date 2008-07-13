# -- coding: utf-8
""" connector.py - Module to manage and retrieve data
    from an internet connection using urllib2. This module is
    part of the HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>

    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Modification History
    ====================

    Aug 16 06         Restarted dev cycle. Fixed 2 bugs with 404
                      errors, one with setting directory URLs
                      and another with re-resolving URLs.
    Feb 8 2007        Added hooks support.

    Mar 5 2007        Modified cache check logic slightly to add
                      support for HTTP 304 errors. HarvestMan will
                      now use HTTP 304 if caching is enabled and
                      we have data cache for the URL being checked.
                      This adds true server-side cache check.
                      Older caching logic retained as fallback.

   Mar 7 2007         Added HTTP compression (gzip) support.
   Mar 8 2007         Added connect2 method for grabbing URLs.
                      Added interactive progress bar for connect2 method.
                      Improved interactive progress bar to resize
                      with changing size of terminal.

   Mar 9 2007         Made progress bar use Progress class borrowed
                      from SMART package manager (Thanks to Vaibhav
                      for pointing this out!)

   Mar 14 2007        Completed implementation of multipart with
                      range checks and all.

   Mar 26 2007        Finished implementation of multipart, integrating
                      with the crawler pieces. Resuming of URLs and
                      caching changes are pending.

   April 20 2007  Anand Added force-splitting option for hget.
   April 30 2007  Anand Using datetime module to convert seconds to
                        hh:mm:ss display.
                        HarvestManFileObject obejcts not recreated when a lost
                        connection is resumed, instead new data is
                        added to existing data, by adjusting byte range
                        if necessary.
   Aug 14 2007    Anand Fixed a bug with download after querying a server
                        for multipart download abilities. Also split
                        _write_url function and rewrote it.

   Aug 22 2007    Anand  MyRedirectHandler is buggy - replaced with
                         urllib2.HTTPRedirectHandler.
   Mar 07 2008    Anand  Made connect to create HEAD request (instead of 'GET')
                         when either last modified time or etag is given. Added etag
                         support to connect and HarvestMan cache.
                         
   Copyright (C) 2004 Anand B Pillai.    
                              
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import sys
import socket
import time
import datetime
import threading

import urllib2 
import urlparse
import gzip
import cStringIO
import os
import shutil
import glob
import random
import base64
import sha
import weakref

import document
import mirrors
import urlparser
from methodwrapper import MethodWrapperMetaClass

from common.common import *
from common.macros import *

from common.spincursor import InfiniteSpinCursor


from httplib import BadStatusLine
from common import keepalive

# Defining pluggable functions
__plugins__ = { 'save_url_plugin': 'HarvestManUrlConnector:save_url' }

# Defining functions with callbacks
__callbacks__ = { 'connect_callback' : 'HarvestManUrlConnector:connect' }

__protocols__=["http", "ftp"]

# Error Macros with arbitrary error numbers
URL_IO_ERROR = 31
URL_BADSTATUSLINE = 41
URL_TYPE_ERROR = 51
URL_VALUE_ERROR = 61
URL_ASSERTION_ERROR = 71
URL_SOCKET_ERROR = 81
URL_SOCKET_TIMEOUT = 91
URL_GENERAL_ERROR = 101

FILEOBJECT_EXCEPTION = 111

class HeadRequest(urllib2.Request):
    """ A request class which performs a HEAD request """

    def get_method(self):
        return 'HEAD'
    
class HarvestManFileObjectException(Exception):
    """ Exception class for HarvestManFileObject class """
    pass

class HarvestManFileObject(threading.Thread):
    """ A class which imitates a file object. This wraps
    around the file object returned by urllib2 and provides
    features such as block reading, throttling and a progress
    bar """

    # Class level attributes used for multipart
    ORIGLENGTH = 0
    START_TIME = 0.0
    CONTENTLEN = []
    MULTIPART = False
    NETDATALEN = 0
    
    def __init__(self, fobj, filename, clength, mode = 0, bwlimit = 0):
        """ Overloaded __init__ method """
        
        self._fobj = fobj
        self._data = ''
        self._clength = int(clength)
        self._start = 0.0
        self._flag = False
        # Mode: 0 => flush data to file (default)
        #     : 1 => keep data in memory
        self._mode = mode
        if self._mode == CONNECTOR_DATA_MODE_FLUSH:
            self._tmpf = open(filename, 'wb')
        else:
            self._tmpf = None
        # Content-length so far
        self._contentlen = 0
        self._index = 0
        # Initialized flag
        self._init = False
        # Last error
        self._lasterror = None
        # Bandwidth limit as bytes/sec
        self._bwlimit = bwlimit
        self._bs = 4096

        threading.Thread.__init__(self, None, None, 'data reader')

    def initialize(self):
        """ Initialize before using an instance of this class.
        This methods sets the start time and the init flag """
        
        self._start = time.time()
        self._init = True

    def is_initialized(self):
        """ Returns the init flag """
        
        return self._init
    
    def set_fileobject(self, fileobj):
        """ Setter method for the encapsulated file object """
        
        self._fobj = fileobj

    def throttle(self, bytecount, start_time, factor):
        """ Throttle to fall within limits of specified download speed """
            
        diff = float(bytecount)/self._bwlimit - (time.time() - start_time)
        diff = factor*diff/HarvestManUrlConnectorFactory.connector_count
        # We need to sleep. But a time.sleep does waste raw CPU
        # cycles. Still there does not seem to be an option here
        # since we cannot use SleepEvent class here as there could
        # be many connectors at any given time and hence the threading
        # library may not be able to create so many distinct Event
        # objects...
        # print 'Diff=>',diff

        if diff>0:
            # We are 'ahead' of the required bandwidth, so sleep
            # the time difference off.
            if self._bs>=256: 
                self._bs -= 128
            time.sleep(diff)

        elif diff<0:
            # We are behind the required bandwidth, so read the
            # additional data
            self._bs += int(self._bwlimit*abs(diff))

    def run(self):
        """ Overloaded run method """
        
        self.initialize()
        self.read()

    def read(self):

        reads = 0
        
        dmgr = objects.datamgr
        config = objects.config

        start_time = config.starttime
        tfactor = config.throttlefactor

        while not self._flag:
            try:
                block = self._fobj.read(self._bs)
                if block=='':
                    self._flag = True
                    # Close the file
                    if self._mode==CONNECTOR_DATA_MODE_FLUSH:
                        self.close()                
                    break
                else:
                    reads += 1
                    self._data = self._data + block
                    self._contentlen += len(block)
                    if self._bwlimit:
                        self.throttle(dmgr.bytes, start_time, tfactor)
                    
                    # Flush data to disk
                    if self._mode==CONNECTOR_DATA_MODE_FLUSH:
                        self.flush()
            
            except socket.error, e:
                self._flag = True
                self._lasterror = e
                break
            except Exception, e:
                self._flag = True
                self._lasterror = e
                break

        self._fobj.close()

    def readNext(self):
        """ Method which reads the next block of data from the URL """

        dmgr = objects.datamgr
        config = objects.config

        start_time = config.starttime
        tfactor = config.throttlefactor

        try:
            block = self._fobj.read(self._bs)
            if block=='':
                self._flag = True
                # Close the file
                if self._mode==CONNECTOR_DATA_MODE_FLUSH:
                    self.close()
                return False
            else:
                self._data = self._data + block
                self._contentlen += len(block)
                if self._bwlimit:
                    self.throttle(dmgr.bytes, start_time, tfactor)
                
                # Flush data to disk
                if self._mode==CONNECTOR_DATA_MODE_FLUSH:
                    self.flush()

        except socket.error, e:
            print 'Error=>',error
            self._fobj.close()
            raise HarvestManFileObjectException, str(e)
        except Exception, e:
            print 'Error=>',error
            self._fobj.close()            
            raise HarvestManFileObjectException, str(e)               

    def flush(self):
        """ Flushes data to the temporary file on disk """

        self._tmpf.write(self._data)
        self._data = ''

    def close(self):
        """ Closes the temporary file object """
        
        self._tmpf.close()

    def get_lasterror(self):
        """ Returns the last error object """
        
        return self._lasterror
    
    def get_info(self):
        """ Returns percentage, data downloaded, bandwidth and estimated time to
        complete as a tuple """

        curr = time.time()
        per, pertotal, bandwidth, l, eta = -1, -1, 0, 0, -1
        
        if not self.__class__.MULTIPART:
            if self._clength:
                pertotal = float(100.0*self._contentlen)/float(self._clength)
            
            l = self._contentlen
            self.__class__.NETDATALEN = self._contentlen
            
            per = pertotal
            
            if curr>self._start:
                bandwidth = float(l)/float(curr - self._start)
            
            if bandwidth and self._clength:
                eta = int((self._clength - l)/float(bandwidth))
        else:
            kls = self.__class__
            kls.CONTENTLEN[self._index] = self._contentlen

            total = sum(kls.CONTENTLEN)
            self.__class__.NETDATALEN = total
            
            if kls.ORIGLENGTH:
               pertotal = float(100.0*total)/float(kls.ORIGLENGTH)

            if self._clength:
                per = float(100.0*self._contentlen)/float(self._clength)
                
            if curr>kls.START_TIME:
               bandwidth = float(total)/float(curr - kls.START_TIME)

            if bandwidth and kls.ORIGLENGTH:
               eta = int((kls.ORIGLENGTH - total)/float(bandwidth))
            pass
        
        if eta != -1:
            eta = str(datetime.timedelta(seconds=int(eta)))
        else:
            eta = 'NaN'
        
        return (per, pertotal, l, bandwidth, eta)

    def get_data(self):
        """ Returns the downloaded data """
        
        return self._data

    def get_datalen(self):
        """ Returns length of downloaded data """
        
        return self._contentlen

    def set_index(self, idx):
        """ Sets the index attribute (used for multipart downloads only) """

        self._index = idx

    def get_index(self):
        """ Gets the index attribute (used for multipart downloads only) """
        
        return self._index
    
    def stop(self):
        """ Stops the thread """
        
        self._flag = True

    @classmethod
    def reset(cls):
        """ Resets all class attributes (classmethod) """
        
        cls.ORIGLENGTH = 0
        cls.START_TIME = 0.0
        cls.CONTENTLEN = []
        cls.MULTIPART = False
        cls.NETDATALEN = 0
        
class HarvestManNetworkConnector(object):
    """ This class keeps the Internet settings and configures the network. """

    alias = 'connmgr'                
    
    def __init__(self):
        # use proxies flag
        self._useproxy=0
        # check for ssl support in python
        self._initssl=False
        # Number of socket errors
        self._sockerrs = 0
        # Config object
        self._cfg = objects.config
        
        if hasattr(socket, 'ssl'):
            self._initssl=True
            __protocols__.append("https")

        # dictionary of protocol:proxy values
        self._proxydict = {}
        # dictionary of protocol:proxy auth values
        self._proxyauth = {}
        self.configure()
        
    def set_useproxy(self, val=True):
        """ Set the value of use-proxy flag. Also sets proxy dictionaries to default values """

        self._useproxy=val

        if val:
            proxystring = 'proxy:80'
            
            # proxy variables
            self._proxydict["http"] =  proxystring
            self._proxydict["https"] = proxystring
            self._proxydict["ftp"] = proxystring
            # set default for proxy authentication
            # tokens.
            self._proxyauth["http"] = ""
            self._proxyauth["https"] = ""
            self._proxyauth["ftp"] = ""            

    def set_ftp_proxy(self, proxyserver, proxyport, authinfo=(), encrypted=True):
        """ Sets ftp proxy information """

        if encrypted:
            self._proxydict["ftp"] = "".join((bin_decrypt(proxyserver),  ':', str(proxyport)))
        else:
            self._proxydict["ftp"] = "".join((proxyserver, ':', str(proxyport)))

        if authinfo:
            try:
                username, passwd = authinfo
            except ValueError:
                username, passwd = '', ''

            if encrypted:
                passwdstring= "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
            else:
                passwdstring = "".join((username, ':', passwd))

            self._proxyauth["ftp"] = passwdstring

    def set_https_proxy(self, proxyserver, proxyport, authinfo=(), encrypted=True):
        """ Sets https(ssl) proxy  information """

        if encrypted:
            self._proxydict["https"] = "".join((bin_decrypt(proxyserver), ':', str(proxyport)))
        else:
            self._proxydict["https"] = "".join((proxyserver, ':', str(proxyport)))

        if authinfo:
            try:
                username, passwd = authinfo
            except ValueError:
                username, passwd = '', ''

            if encrypted:
                passwdstring= "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
            else:
                passwdstring = "".join((username, ':', passwd))

            self._proxyauth["https"] = passwdstring

    def set_http_proxy(self, proxyserver, proxyport, authinfo=(), encrypted=True):
        """ Sets http proxy information """

        if encrypted:
            self._proxydict["http"] = "".join((bin_decrypt(proxyserver), ':', str(proxyport)))
        else:
            self._proxydict["http"] = "".join((proxyserver, ':', str(proxyport)))

        if authinfo:
            try:
                username, passwd = authinfo
            except ValueError:
                username, passwd = '', ''

            if encrypted:
                passwdstring= "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
            else:
                passwdstring= "".join((username, ':', passwd))

            self._proxyauth["http"] = passwdstring

    def set_proxy(self, server, port, authinfo=(), encrypted=True):
        """ Sets proxy information for all protocols """

        # For most users, only this method will be called,
        # rather than the specific method for each protocol,
        # as proxies are normally shared for all tcp/ip protocols 

        for p in __protocols__:
            # eval helps to do this dynamically
            s='self.set_' + p + '_proxy'
            func=eval(s, locals())
            
            func(server, port, authinfo, encrypted)

    def set_authinfo(self, username, passwd, encrypted=True):
        """ Set authentication information for proxy server """

        
        # Note: If this function is used all protocol specific
        # authentication will be replaced by this authentication. 

        if encrypted:
            passwdstring = "".join((bin_decrypt(username), ':', bin_decrypt(passwd)))
        else:
            passwdstring = "".join((username, ':', passwd))

        self._proxyauth = {"http" : passwdstring,
                            "https" : passwdstring,
                            "ftp" : passwdstring }

    def configure(self):
        """ Wrapper method for configuring network and protocols """

        import common.keepalive
        log = objects.logger

        common.keepalive.DEBUG = common.keepalive.FakeLogger()
        common.keepalive.DEBUG.info = log.debug
        common.keepalive.DEBUG.error = log.debug
        
        self.configure_network()
        self.configure_protocols()
        
    def configure_network(self):
        """ Configure network settings for the user """

        # First: Configuration of network (proxies/intranet etc)
        
        # Check for proxies in the config object
        if self._cfg.proxy:
            self.set_useproxy(True)
            proxy = self._cfg.proxy
            
            index = proxy.rfind(':')
            if index != -1:
                port = proxy[(index+1):].strip()
                server = proxy[:index]
                # strip of any 'http://' from server
                index = server.find('http://')
                if index != -1:
                    server = server[(index+7):]

                self.set_proxy(server, int(port), (), self._cfg.proxyenc)

            else:
                port = self._cfg.proxyport
                server = self._cfg.proxy
                self.set_proxy(server, int(port), (), self._cfg.proxyenc)

            # Set proxy username and password, if specified
            puser, ppasswd = self._cfg.puser, self._cfg.ppasswd
            if puser and ppasswd: self.set_authinfo(puser, ppasswd, self._cfg.proxyenc)


    def configure_protocols(self):
        """ Configures protocol handlers """
        
        # Second: Configuration of protocol handlers.

        # TODO: Verify gopher protocol
        authhandler = urllib2.HTTPBasicAuthHandler()
        cookiehandler = None
        
        # set timeout for sockets to thread timeout, for Python 2.3
        # and greater. 
        minor_version = sys.version_info[1]
        if minor_version>=3:
            socket.setdefaulttimeout( self._cfg.socktimeout )
            # For Python 2.4, use cookielib support
            # To fix HTTP cookie errors such as those
            # produced by http://www.eidsvoll.kommune.no/
            if minor_version>=4:
                import cookielib
                cj = cookielib.MozillaCookieJar()
                cookiehandler = urllib2.HTTPCookieProcessor(cj)

        # HTTP/HTTPS handlers
        if self._cfg.appname == 'Hget':
            httphandler = urllib2.HTTPHandler
            httpshandler = urllib2.HTTPSHandler
        else:
            httphandler = keepalive.HTTPHandler
            httpshandler = urllib2.HTTPSHandler #keepalive.HTTPSHandler
            
        # If we are behing proxies/firewalls
        if self._useproxy:
            if self._proxyauth['http']:
                httpproxystring = "".join(('http://',
                                           self._proxyauth['http'],
                                           '@',
                                           self._proxydict['http']))
            else:
                httpproxystring = "".join(('http://', self._proxydict['http']))

            if self._proxyauth['ftp']:
                ftpproxystring = "".join(('http://',
                                          self._proxyauth['ftp'],
                                          '@',
                                          self._proxydict['ftp']))
            else:
                ftpproxystring = "".join(('http://', self._proxydict['ftp']))

            if self._proxyauth['https']:
                httpsproxystring = "".join(('http://',
                                            self._proxyauth['https'],
                                            '@',
                                            self._proxydict['https']))
            else:
                httpsproxystring = "".join(('http://', self._proxydict['https']))

            # Set this as the new entry in the proxy dictionary
            self._proxydict['http'] = httpproxystring
            self._proxydict['ftp'] = ftpproxystring
            self._proxydict['https'] = httpsproxystring

            
            proxy_support = urllib2.ProxyHandler(self._proxydict)
            
            # build opener and install it
            if self._initssl:
                opener = urllib2.build_opener(authhandler,
                                              urllib2.HTTPRedirectHandler,
                                              proxy_support,
                                              httphandler,
                                              urllib2.HTTPDefaultErrorHandler,
                                              urllib2.FTPHandler,
                                              urllib2.GopherHandler,
                                              httpshandler,
                                              urllib2.FileHandler,
                                              cookiehandler)
            else:
                opener = urllib2.build_opener(authhandler,
                                              urllib2.HTTPRedirectHandler,
                                              proxy_support,
                                              httphandler,
                                              urllib2.HTTPDefaultErrorHandler,
                                              urllib2.FTPHandler,
                                              urllib2.GopherHandler,
                                              urllib2.FileHandler,
                                              cookiehandler)

        else:
            # Direct connection to internet
            if self._initssl:
                opener = urllib2.build_opener(authhandler,
                                              urllib2.HTTPRedirectHandler,
                                              httphandler,
                                              urllib2.FTPHandler,
                                              httpshandler,
                                              urllib2.GopherHandler,
                                              urllib2.FileHandler,
                                              urllib2.HTTPDefaultErrorHandler,
                                              cookiehandler)
            else:
                opener = urllib2.build_opener( authhandler,
                                               urllib2.HTTPRedirectHandler,
                                               httphandler,
                                               urllib2.FTPHandler,
                                               urllib2.GopherHandler,
                                               urllib2.FileHandler,
                                               urllib2.HTTPDefaultErrorHandler,
                                               cookiehandler)

        urllib2.install_opener(opener)

        return CONFIGURE_PROTOCOL_OK

    # Get methods
    def get_useproxy(self):
        """ Returns whether we are going through a proxy server """

        return self._useproxy
    
    def get_proxy_info(self):
        """ Return proxy information as a tuple. The first member
        of the tuple is the proxy server dictionary and the second
        member the proxy authentication information """
        
        return (self._proxydict, self._proxyauth)

    def increment_socket_errors(self, val=1):
        """ Increment socket error count """
        
        self._sockerrs += val

    def decrement_socket_errors(self, val=1):
        """ Decrement socket error count """
        
        self._sockerrs -= val
        
    def get_socket_errors(self):
        """ Get socket error count """
        
        return self._sockerrs

class HarvestManUrlError(object):
    """ Class encapsulating errors raised by HarvestManUrlConnector objects
    while connecting and downloading data from the Internet """
    
    def __init__(self):
        """ Overloaded __init__ method """
        
        self.initialize()

    def initialize(self):
        """ Initializes an instance of this class """
        self.reset()

    def __str__(self):
        """ Returns string representation of an instance of the class """
        
        return ''.join((str(self.errclass),' ', str(self.number),': ',self.msg))

    def reset(self):
        """ Resets attributes """
        
        self.number = 0
        self.msg = ''
        self.fatal = False
        self.errclass = ''        
        
class HarvestManUrlConnector(object):
    """ Class which performs the work of fetching data for URLs
    from the Internet and save data to the disk """

    __metaclass__ = MethodWrapperMetaClass
    
    def __str__(self):
        """ Return a string representation of an instance of this class """
        return `self` 
        
    def __init__(self):
        """ Overloaded __init__ method """

        # file like object returned by
        # urllib2.urlopen(...)
        self._freq = None
        # data downloaded
        self._data = ''
        # length of data downloaded
        self._datalen = 0
        # error object
        self._error = HarvestManUrlError()
        # time to wait before reconnect
        # in case of failed connections
        self._sleeptime = 0.5
        # global network configurator
        self.network_conn = objects.connmgr
        # Config object
        self._cfg = objects.config    
        # Http header for current connection
        self._headers = CaselessDict()
        # HarvestMan file object
        self._fo = None
        # Elasped time for reading data
        self._elapsed = 0.0
        # Mode for data download
        self._mode = self._cfg.datamode
        # Temporary filename if any
        self._tmpfname = ''
        # Status of connection
        # 0 => no connection
        # 1 => connected, download in progress
        self._status = 0
        # Number of tries
        self._numtries = 0
        # Acquired flag
        self._acquired = True
        # Block write flag - to be used
        # to indicate to connector to
        # not save the data to disk
        self.blockwrite = False
        # Throttle sleeping time to be
        # set on the file object
        self.throttle_time = 0
        
    def __del__(self):
        del self._data
        self._data = None
        del self._freq
        self._freq = None
        del self._error
        self._error = None
        del self.network_conn
        self.network_conn = None
        del self._cfg
        self._cfg = None
        
    def _proxy_query(self, queryauth=1, queryserver=0):
        """ Query the user for proxy related information """

        self.network_conn.set_useproxy(True)
        
        if queryserver or queryauth:
            # There is an error in the config file/project file/user input
            SetUserDebug("Error in proxy server settings (Regenerate the config/project file)")

        # Get proxy info from user
        try:
            if queryserver:
                server=bin_crypt(raw_input('Enter the name/ip of your proxy server: '))
                port=int(raw_input('Enter the proxy port: '))         
                self.network_conn.set_proxy(server, port)

            if queryauth:
                user=bin_crypt(raw_input('Enter username for your proxy server: '))
                # Ask for password only if a valid user is given.
                if user:
                    import getpass
                    passwd=bin_crypt(getpass.getpass('Enter password for your proxy server: '))
                    # Set it on myself and re-configure
                    self.network_conn.set_authinfo(user,passwd)
        except EOFError, e:
            error("Proxy Setting Error:",e)

        info('Re-configuring protocol handlers...')
        self.network_conn.configure_protocols()
        
        extrainfo('Done.')

    def release(self):
        """ Marks the connector object as released """

        self._acquired = False

    def is_released(self):
        """ Returns whether the connector was released or not """

        return (not self._acquired)
    
    def urlopen(self, url):
        """ Opens the URL and returns the url file stream """

        try:
            urlobj = urlparser.HarvestManUrl(url)
            self.connect(urlobj, True, self._cfg.retryfailed )
            # return the file like object
            if self._error.fatal:
                return None
            else:
                return self._freq
        except urlparser.HarvestManUrlError, e:
            error("URL Error:",e)
            
    def robot_urlopen(self, url):
        """ Opens a robots.txt URL and returns the request object """

        try:
            urlobj = urlparser.HarvestManUrl(url)
            self.connect(urlobj, False, 0)
            # return the file like object
            if self._error.fatal:
                return None
            else:
                return self._freq
        except urlparser.HarvestManUrlError, e:
            error("URL Error:",e)
        
    def connect(self, urlobj, fetchdata=True, retries=1, lastmodified='', etag=''):
        """ Connects to the Internet and fetches data for the URL encapsulated
        in the object 'urlobj' """

        # This is the work-horse method of this class...
        
        data = ''

        dmgr = objects.datamgr
        rulesmgr = objects.rulesmgr

        self._numtries = 0
        three_oh_four = False

        # Reset the http headers
        self._headers.clear()
        urltofetch = urlobj.get_full_url()

        lmt, tag = lastmodified, etag

        # Raise an event...
        if objects.eventmgr.raise_event('beforeconnect', urlobj, None, last_modified=lastmodified, etag=etag)==False:
            return CONNECT_NO_FILTERED

        add_ua = self._cfg._connaddua
        
        while self._numtries <= retries and not self._error.fatal:

            # Reset status
            self._status = 0
            
            errnum = 0
            try:
                # Reset error
                self._error.reset()

                self._numtries += 1

                # create a request object
                # If we are passed either the lastmodified time or
                # the etag value or both, we will be creating a
                # head request. Now if either the etag or lastmodified
                # time match, the server should produce a 304 error
                # and we break the loop automatically. If not, we have
                # to set lmt and tag values to null strings so that
                # we make an actual request.

                # Set lmt, tag to null strings if try count is greater
                # than 1...
                if self._numtries>1:
                    lmt, tag = '', ''
                    
                request = self.create_request(urltofetch, lmt, tag, useragent=add_ua)

                # Check for urlobject which is trying to do
                # multipart download.
                #byterange = urlobj.range
                #if byterange:
                #    range1 = byterange[0]
                #    range2 = byterange[-1]
                #    request.add_header('Range','bytes=%d-%d' % (range1, range2))

                # If we accept http-compression, add the required header.
                if self._cfg.httpcompress:
                    request.add_header('Accept-Encoding', 'gzip')

                self._freq = urllib2.urlopen(request)
                # Set status to 1
                self._status = 1
                
                # Set http headers
                self.set_http_headers()

                clength = int(self.get_content_length())
                if urlobj: urlobj.clength = clength
                
                trynormal = False
                # Check constraint on file size, dont do this on
                # objects which are already downloading pieces of
                # a multipart download.
                if not self.check_content_length(): # and not byterange
                    maxsz = self._cfg.maxfilesize
                    extrainfo("Url",urltofetch,"does not match size constraints")
                    # Raise an event...
                    objects.eventmgr.raise_event('afterconnect', urlobj, None)
                    
                    return CONNECT_NO_RULES_VIOLATION
                
##                     supports_multipart = dmgr.supports_range_requests(urlobj)
                    
##                     # Dont do range checking on FTP servers since they
##                     # typically support it by default.
##                     if urlobj.protocol != 'ftp' and supports_multipart==0:
##                         # See if the server supports 'Range' header
##                         # by requesting half the length
##                         self._headers.clear()
##                         request.add_header('Range','bytes=%d-%d' % (0,clength/2))
##                         self._freq = urllib2.urlopen(request)
##                         # Set http headers
##                         self.set_http_headers()
##                         range_result = self._headers.get('accept-ranges')

##                         if range_result.lower()=='bytes':
##                             supports_multipart = 1
##                         else:
##                             extrainfo('Server %s does not support multipart downloads' % urlobj.domain)
##                             extrainfo('Aborting download of  URL %s.' % urltofetch)
##                             return CONNECT_NO_RULES_VIOLATION

##                     if supports_multipart==1:
##                         extrainfo('Server %s supports multipart downloads' % urlobj.domain)
##                         dmgr.download_multipart_url(urlobj, clength)
##                         return CONNECT_MULTIPART_DOWNLOAD
                    
                # The actual url information is used to
                # differentiate between directory like urls
                # and file like urls.
                actual_url = self._freq.geturl()
                
                # Replace the urltofetch in actual_url with null
                if actual_url:
                    no_change = (actual_url == urltofetch)
                    
                    if not no_change:
                        replacedurl = actual_url.replace(urltofetch, '')
                        # If the difference is only as a directory url
                        if replacedurl=='/':
                            no_change = True
                        else:
                            no_change = False
                            
                        # Sometimes, there could be HTTP re-directions which
                        # means the actual url may not be same as original one.
                        if no_change:
                            if (actual_url[-1] == '/' and urltofetch[-1] != '/'):
                                extrainfo('Setting directory url=>',urltofetch)
                                urlobj.set_directory_url()
                                
                        else:
                            # There is considerable change in the URL.
                            # So we need to re-resolve it, since otherwies
                            # some child URLs which derive from this could
                            # be otherwise invalid and will result in 404
                            # errors.
                            urlobj.redirected = True                            
                            urlobj.url = actual_url
                            debug('Actual URL=>',actual_url)
                            urlobj.wrapper_resolveurl()
                    
                # Find the actual type... if type was assumed
                # as wrong, correct it.
                content_type = self.get_content_type()
                urlobj.manage_content_type(content_type)
                        
                # update byte count
                # if this is the not the first attempt, print a success msg
                if self._numtries>1:
                    extrainfo("Reconnect succeeded => ", urltofetch)

                # Update content info on urlobject
                self.set_content_info(urlobj)

                if fetchdata:
                    try:
                        # If gzip-encoded, need to deflate data
                        encoding = self.get_content_encoding()
                        clength = self.get_content_length()
                        
                        t1 = time.time()
                        
                        if self._fo==None:
                            if self._mode==CONNECTOR_DATA_MODE_FLUSH:
                                if self._cfg.projtmpdir:
                                    self._tmpfname = self.make_tmp_fname(urlobj.get_filename(),
                                                                         self._cfg.projtmpdir)
                                else:
                                    # For stand-alone use outside crawls
                                    self._tmpfname = self.make_tmp_fname(urlobj.get_filename(),
                                                                         GetMyTempDir())
                            self._fo = HarvestManFileObject(self._freq,
                                                            self._tmpfname,
                                                            clength,
                                                            self._mode,
                                                            float(self._cfg.bandwidthlimit))
                            self._fo.initialize()
                        else:
                            self._fo.set_fileobject(self._freq)

                        
                        self._fo.read()
                        self._elapsed = time.time() - t1
                        
                        self._freq.close()                       
 
                        if self._mode==CONNECTOR_DATA_MODE_INMEM:
                            data = self._fo.get_data()
                            self._datalen = len(data)

                            # Save a reference
                            data0 = data
                            self._freq.close()                        
                            dmgr.update_bytes(len(data))
                            debug('Encoding',encoding)
                        
                            if encoding.strip().find('gzip') != -1:
                                try:
                                    gzfile = gzip.GzipFile(fileobj=cStringIO.StringIO(data))
                                    data = gzfile.read()
                                    gzfile.close()
                                except (IOError, EOFError), e:
                                    data = data0
                                    pass
                        else:
                            self._datalen = self._fo.get_datalen()
                            dmgr.update_bytes(self._datalen)
                            
                    except MemoryError, e:
                        # Catch memory error for sockets
                        error("Memory Error:",str(e))

                # Explicitly set the status of urlobj to zero since
                # download was completed...
                urlobj.status = 0
                        
                break

            #except Exception, e:
            #     raise
            
            except urllib2.HTTPError, e:
                
                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.strip().split()
                    self._error.number = int(parts[-1])
                    self._error.msg = errdescn.strip()
                    self._error.errclass = "HTTPError"
                except:
                    pass

                if self._error.msg:
                    error(self._error.msg, '=> ',urltofetch)
                else:
                    error('HTTPError:',urltofetch)

                try:
                    errnum = int(self._error.number)
                except:
                    pass

                if errnum==304:
                    # Page not modified
                    three_oh_four = True
                    self._error.fatal = False
                    # Need to do this to ensure that the crawler
                    # proceeds further!
                    content_type = self.get_content_type()
                    urlobj.manage_content_type(content_type)                    
                    break
                if errnum in range(400, 407):
                    # 400 => bad request
                    # 401 => Unauthorized
                    # 402 => Payment required (not used)
                    # 403 => Forbidden
                    # 404 => Not found
                    # 405 => Method not allowed
                    # 406 => Not acceptable
                    
                    # If error is 400, 405 or 406, then we
                    # retry with the useragent string not set.
                    if errnum in (400, 405, 406):
                        self._cfg._badrequests += 1
                        # If we get many badrequests in a row
                        # we disable UA addition for this crawl.
                        if self._cfg._badrequests>=5:
                            self._cfg._connaddua = False
                            
                        if self._numtries<=retries:
                            add_ua = False
                        else:
                            self._error.fatal = True                            
                    else:
                        self._error.fatal = True
                elif errnum == 407:
                    # Proxy authentication required
                    self._proxy_query(1, 1)
                elif errnum == 408:
                    # Request timeout, try again
                    pass
                elif errnum == 412:
                    # Pre-condition failed, this has been
                    # detected due to our user-agent on some
                    # websites (sample URL: http://guyh.textdriven.com/)
                    self._error.fatal =  True
                elif errnum in range(409, 418):
                    # Error codes in 409-417 contain a mix of
                    # fatal and non-fatal states. For example
                    # 410 indicates requested resource is no
                    # Longer available, but we could try later.
                    # However for all practical purposes, we
                    # are marking these codes as fatal errors
                    # for the time being.
                    self._error.fatal = True
                elif errnum == 500:
                    # Internal server error, can try again
                    pass
                elif errnum == 501:
                    # Server does not implement the functionality
                    # to fulfill the request - fatal
                    self._error.fatal = True
                elif errnum == 502:
                    # Bad gateway, can try again ?
                    pass
                elif errnum in (503, 506):
                    # 503 - Service unavailable
                    # 504 - Gatway timeout
                    # 505 - HTTP version not supported
                    self._error.fatal = True

                if self._error.fatal:
                    rulesmgr.add_to_filter(urltofetch)
                    
            except urllib2.URLError, e:
                # print 'urlerror',urltofetch
                
                errdescn = ''
                self._error.errclass = "URLError"
                
                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.split()                            
                except:
                    try:
                        errbasic, errdescn = (str(e)).split(',')
                        parts = errbasic.split('(')
                        errdescn = (errdescn.split("'"))[1]
                    except:
                        pass

                try:
                    self._error.number = int(parts[-1])
                except:
                    pass
                
                if errdescn:
                    self._error.msg = errdescn

                if self._error.msg:
                    error(self._error.msg, '=> ',urltofetch)
                else:
                    error('URLError:',urltofetch)

                errnum = self._error.number
                if errnum == 10049 or errnum == 10061: # Proxy server error
                    self._proxy_query(1, 1)
                elif errnum == 10055:
                    # no buffer space available
                    self.network_conn.increment_socket_errors()
                    # If the number of socket errors is >= 4
                    # we decrease max connections by 1
                    sockerrs = self.network_conn.get_socket_errors()
                    if sockerrs>=4:
                        self._cfg.connections -= 1
                        self.network_conn.decrement_socket_errors(4)

            except IOError, e:
                self._error.number = URL_IO_ERROR
                self._error.fatal=True
                self._error.msg = str(e)
                self._error.errclass = "IOError"                
                # Generated by invalid ftp hosts and
                # other reasons,
                # bug(url: http://www.gnu.org/software/emacs/emacs-paper.html)
                error(e ,'=> ',urltofetch)

            except BadStatusLine, e:
                self._error.number = URL_BADSTATUSLINE
                self._error.msg = str(e)
                self._error.errclass = "BadStatusLine"
                error(e, '=> ',urltofetch)

            except TypeError, e:
                self._error.number = URL_TYPE_ERROR
                self._error.msg = str(e)
                self._error.errclass = "TypeError"                
                error(e, '=> ',urltofetch)
                
            except ValueError, e:
                self._error.number = URL_VALUE_ERROR
                self._error.msg = str(e)
                self._error.errclass = "ValueError"                
                error(e, '=> ',urltofetch)

            except AssertionError, e:
                self._error.number = URL_ASSERTION_ERROR
                self._error.msg = str(e)
                self._error.errclass = "AssertionError"                
                error(e ,'=> ',urltofetch)

            except socket.error, e:
                self._error.msg = str(e)
                self._error.number = URL_SOCKET_ERROR
                self._error.errclass = "SocketError"                
                errmsg = self._error.msg

                error('Socket Error: ', errmsg,'=> ',urltofetch)

                if errmsg.lower().find('connection reset by peer') != -1:
                    # Connection reset by peer (socket error)
                    self.network_conn.increment_socket_errors()
                    # If the number of socket errors is >= 4
                    # we decrease max connections by 1
                    sockerrs = self.network_conn.get_socket_errors()

                    if sockerrs>=4:
                        self._cfg.connections -= 1
                        self.network_conn.decrement_socket_errors(4)

            except socket.timeout, e:
                self._error['msg'] = 'socket timed out'
                self._error['number'] = URL_SOCKET_TIMEOUT
                errmsg = self._error['msg']

                error('Socket Error: ', errmsg,'=> ',urltofetch)
                
            except Exception, e:
                self._error.msg = str(e)
                self._error.number = URL_GENERAL_ERROR
                self._error.errclass = "GeneralError"                
                errmsg = self._error.msg
            
                error('General Error: ', errmsg,'=> ',urltofetch)
                
            # attempt reconnect after some time
            # self.evnt.sleep()
            time.sleep(self._sleeptime)

        if data:
            self._data = data
            # Set hash on URL object
            urlobj.pagehash = sha.new(data).hexdigest()

        # print 'URLOBJ STATUS=>',urlobj.status
        if urlobj and urlobj.status != 0:
            urlobj.status = self._error.number
            urlobj.fatal = self._error.fatal
            debug('Setting %s status to %s' % (urlobj.get_full_url(), str(urlobj.status)))
            
        # Raise an event...
        objects.eventmgr.raise_event('afterconnect', urlobj, None)
        
        if three_oh_four:
            return CONNECT_NO_UPTODATE
            
        if self._data or self._datalen:
            return CONNECT_YES_DOWNLOADED
        else:
            return CONNECT_NO_ERROR

    def set_progress_object(self, topic, n=0, subtopics=[], nolengthmode=False):
        """ Set the progress bar with the given topic and sub-topics """

        # n=> number of subtopics
        # topic => Topic
        # subtopics => List of subtopics

        # n should be = len(subtopics)
        if n != len(subtopics):
            return False

        # Create progress object
        prog = self._cfg.progressobj
        prog.setTopic(topic)
        #if n==1:
        prog.set(100, 100)
        #else:
        #    prog.set(n, 100)
        
        if nolengthmode:
            prog.setNoLengthMode(True)

        if n>0:
            prog.setHasSub(True)
            if not nolengthmode:
                for x in range(1,n+1):
                    prog.setSubTopic(x, subtopics[x-1])
                    prog.setSub(x, 0.0, 100)
        else:
            pass
            
    def make_tmp_fname(self, filename, directory='.'):
        """ Creates a temporary filename for download """

        random.seed()
        
        while True:
            fint = int(random.random()*random.random()*10000000)
            fname = ''.join(('.',filename,'#',str(fint)))
            fpath = os.path.join(directory, fname)
            if not os.path.isfile(fpath):
                return fpath

    def create_request(self, urltofetch, lmt='', etag='', useragent=True):
        """ Creates request object for the URL 'urltofetch' and return it """

        # This function takes care of adding any additional headers
        # etc in addition to creating the request object.
        
        # create a request object
        if lmt or etag:
            # print 'Making a head request', lmt, etag
            # Create a head request...
            request = HeadRequest(urltofetch)
            if lmt != '':
                ts = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.localtime(lmt))
                request.add_header('If-Modified-Since', ts)
            if etag != '':
                request.add_header('If-None-Match', etag)
        else:
            request = urllib2.Request(urltofetch)

        # Some sites do not like User-Agent strings and raise a Bad Request
        # (HTTP 400) error. Egs: http://www.bad-ischl.ooe.gv.at/. In such
        # cases, the connect method, sets useragent flag to False and calls
        # this method again.
        # print 'User agent', self._cfg.USER_AGENT
        if useragent: request.add_header('User-Agent', self._cfg.USER_AGENT)
        
        # Check if any HTTP username/password are required
        username, password = self._cfg.username, self._cfg.passwd
        if username and password:
            # Add basic HTTP auth headers
            authstring = base64.encodestring('%s:%s' % (username, password))
            request.add_header('Authorization','Basic %s' % authstring)

        return request

    def get_url_data(self, url):
        """ Downloads data for the given URL and returns it """

        try:
            urlobj = urlparser.HarvestManUrl(url)
            res = self.connect(urlobj)
            return self._data
        except urlparser.HarvestManUrlError, e:
            error("URL Error: ",e)
        
    def connect2(self, urlobj, showprogress=True, resuming=False):
        """ Connects to the Internet and fetches data for the URL encapsulated
        in the object 'urlobj'. This is the method used by Hget """
        
        data = '' 
        
        # Reset the http headers
        self._headers.clear()
        retries = 1
        self._numtries = 0

        urltofetch = urlobj.get_full_url()
        filename = urlobj.get_filename()

        dmgr = objects.datamgr
        rulesmgr = objects.rulesmgr
        
        # print self, urltofetch
        while self._numtries <= retries and not self._error.fatal:

            # Reset status
            self._status = 0

            errnum = 0
            try:
                # Reset error
                self._error.reset()

                self._numtries += 1

                request = self.create_request(urltofetch)
                byterange = urlobj.range
                
                if byterange:
                
                    range1 = byterange[0]
                    range2 = byterange[-1]
                    # For a repeat connection, don't redownload already downloaded data.
                    if self._fo:
                        datasofar = self._fo.get_datalen()
                        if datasofar: range1 += datasofar
                        
                    request.add_header('Range','bytes=%d-%d' % (range1,range2))

                self._freq = urllib2.urlopen(request)

                # Set status to 1
                self._status = 1

                actual_url = self._freq.geturl()
                if actual_url != urltofetch:
                    # Don't do this for mirrors...
                    if not urlobj.trymultipart:
                        logconsole('Redirected to %s...' % actual_url)
                
                    if actual_url.replace(urltofetch, '') != '/':
                        no_change = False
                    else:
                        no_change = True

                    if no_change:
                        if (actual_url[-1] == '/' and urltofetch[-1] != '/'):
                            # Setting directory URL
                            urlobj.set_directory_url()
                    else:
                        # Considerable change
                        urlobj.redirected = True
                        urlobj.url = actual_url
                        urlobj.wrapper_resolveurl()
                        # Get filename again
                        filename = urlobj.get_filename()
                        
                # Set http headers
                self.set_http_headers()
                
                encoding = self.get_content_encoding()
                ctype = self.get_content_type()
                clength = int(self.get_content_length())
                
                if clength==0:
                    clength_str = 'Unknown'
                elif clength>=1024*1024:
                    clength_str = '%dM' % (clength/(1024*1024))
                elif clength >=1024:
                    clength_str = '%dK' % (clength/1024)
                else:
                    clength_str = '%d bytes' % clength

                if resuming or (not urlobj.range):
                    if clength:
                        logconsole('Length: %d (%s) Type: %s' % (clength, clength_str, ctype))
                        nolengthmode = False
                    else:
                        logconsole('Length: (%s) Type: %s' % (clength_str, ctype))
                        nolengthmode = True

                    logconsole('Content Encoding: %s\n' % encoding)

                # FTP servers do not support HTTP like byte-range
                # requests. The way to do multipart for FTP is to use
                # the FTP restart (REST) command, but that requires writing
                # new wrappers on top of ftplib instead of the current simpler
                # way of routing everything using urllib2. This is planned
                # for later.

                # However if mirror search is enabled, we try to do it
                if urlobj.protocol == 'ftp://' and not self._cfg.mirrorsearch:
                    trynormal = True
                    
                    if self._cfg.forcesplit:
                        logconsole('FTP request, not trying multipart download, defaulting to single thread')
                else:
                    trynormal = False

                # Check constraint on file size
                if (not byterange) and (not trynormal) and (not self._cfg.nomultipart) and self._cfg.forcesplit:
                    if self._cfg.forcesplit and not self._cfg.mirrorsearch:
                        logconsole('Forcing download into %d parts' % self._cfg.numparts)
                        
                    if (not self._headers.get('accept-ranges', '').lower() == 'bytes') and (not self._cfg.mirrorfile) and \
                           not mirrors.is_multipart_download_supported(urlobj) and not (self._cfg.mirrorsearch):
                        logconsole('Checking whether server supports multipart downloads...')
                        # See if the server supports 'Range' header
                        # by requesting half the length
                        self._headers.clear()
                        request.add_header('Range','bytes=%d-%d' % (0,clength/2))
                        self._freq.close()                        
                        self._freq = urllib2.urlopen(request)

                        # Set http headers
                        self.set_http_headers()
                        range_result = self._headers.get('accept-ranges', '')
                        if range_result.lower()=='bytes':
                            logconsole('Server supports multipart downloads')
                            self._freq.close()
                        else:
                            logconsole('Server does not support multipart downloads')
                            resp = raw_input('Do you still want to download this URL [y/n] ?')
                            if resp.lower() !='y':
                                logconsole('Aborting download.')
                                return CONNECT_DOWNLOAD_ABORTED
                            else:
                                # Create a fresh request object
                                self._freq.close()
                                request = self.create_request(urltofetch)
                                self._freq = urllib2.urlopen(request)

                                logconsole('Downloading URL %s...' % urltofetch)
                                trynormal = True
                    else:
                        logconsole('Server supports multipart downloads')

                    if not trynormal:
                        logconsole('Trying multipart download...')
                        urlobj.trymultipart = True
                        
                        ret = dmgr.download_multipart_url(urlobj, clength)
                        if ret == URL_PUSHED_TO_POOL:
                            # Set flag which indicates a multipart
                            # download is in progress
                            self._cfg.multipart = True
                            # Set progress object
                            if showprogress:
                                self.set_progress_object(filename,1,[filename],nolengthmode)

                            return CONNECT_MULTIPART_DOWNLOAD
                        elif ret == MIRRORS_NOT_FOUND:
                            return ret
                    
                # if this is the not the first attempt, print a success msg
                if self._numtries>1:
                    extrainfo("Reconnect succeeded => ", urltofetch)

                try:
                    # Don't set progress object if multipart download - it
                    # would have been done before.
                    if showprogress and (resuming or (not urlobj.range)):
                        self.set_progress_object(filename,1,[filename],nolengthmode)
                    
                    prog = self._cfg.progressobj
                    
                    mypercent = 0.0

                    # Report fname to calling thread
                    ct = threading.currentThread()

                    # Only set tmpfname if this is a fresh download.
                    if self._tmpfname=='':
                        if not self._cfg.hgetnotemp:
                            if urlobj.trymultipart:
                                localurl = urlobj.mirror_url.get_original_url()
                            else:
                                localurl = urlobj.get_original_url()
                                
                            tmpd = os.path.join(GetMyTempDir(), str(abs(hash(localurl))))
                        else:
                            tmpd = '.'
                            
                        self._tmpfname = self.make_tmp_fname(filename, tmpd)
                        
                    if ct.__class__.__name__ == 'HarvestManUrlThread':
                        ct.set_tmpfname(self._tmpfname)

                    if self._fo==None:
                        self._fo = HarvestManFileObject(self._freq,
                                                        self._tmpfname,
                                                        clength,
                                                        self._mode)
                    else:
                        self._fo.set_fileobject(self._freq)

                    # Setting class-level variables
                    if self._cfg.multipart:
                        if not HarvestManFileObject.MULTIPART:
                            HarvestManFileObject.MULTIPART = True
                            HarvestManFileObject.START_TIME = time.time()
                            HarvestManFileObject.ORIGLENGTH = urlobj.clength
                            HarvestManFileObject.CONTENTLEN = [0]*self._cfg.numparts

                    if not self._fo.is_initialized():
                        if self._cfg.multipart:
                            self._fo.set_index(urlobj.mindex)
                            self._fo.initialize()
                        else:
                            self._fo.start()

                    t1 = time.time()

                    while True:
                        if self._cfg.multipart:
                            self._fo.readNext()

                        # Get number of active worker threads...
                        nthreads = dmgr.get_url_threadpool().get_busy_count()
                        # If no active worker threads, then there is at least
                        # the main thread which is active
                        if nthreads==0: nthreads = 1

                        # Check if there was any exception in the reader thread
                        # If there is an exception when the reader is running as
                        # a thread, the flag will be set
                        if self._fo._flag:
                            readerror = self._fo.get_lasterror()
                            if readerror:
                                raise HarvestManFileObjectException, str(readerror)
                            
                        if clength:
                            per1,per2,l,bw,eta = self._fo.get_info()
                            
                            if per2 and showprogress:
                                prog.setScreenWidth(prog.getScreenWidth())
                                infostring = '%4.2fK/s (%d) eta: %s' % (float(bw/1024.0),
                                                                            nthreads,
                                                                            str(eta))
                                prog.setSubTopic(1, infostring)
                                prog.setSub(1, per2, 100)
                                prog.show()
                                    
                            if per1==100.0: break
                        else:
                            if mypercent and showprogress:
                                self._fo.get_info()
                                prog.setScreenWidth(prog.getScreenWidth())
                                infostring = 'RT: %s  ' % str(nthreads) +  filename
                                prog.setSubTopic(1, infostring)
                                prog.setSub(1, mypercent, 100)
                                prog.show()
                                
                            if self._fo._flag: break
                            mypercent += 2.0
                            if mypercent==100.0: mypercent=0.0

                    self._elapsed = time.time() - t1

                    if self._fo._mode == CONNECTOR_DATA_MODE_INMEM:
                        if not resuming:
                            self._data = self._fo.get_data()
                        else:
                            self._data += self._fo.get_data()
                        
                        self._datalen = len(self._data)
                    else:
                        self._datalen = self._fo.get_datalen()

                except MemoryError, e:
                    # Catch memory error for sockets
                    pass
                    
                break

            #except Exception, e:
            #    raise
                
            except urllib2.HTTPError, e:

                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.strip().split()
                    self._error.number = int(parts[-1])
                    self._error.msg = errdescn.strip()
                    self._error.errclass = "HTTPError"                    
                except:
                    pass

                if self._error.msg:
                    error(self._error.msg, '=> ',urltofetch)
                else:
                    error('HTTPError:',urltofetch)

                try:
                    errnum = int(self._error.number)
                except:
                    pass

                if errnum==304:
                    # Page not modified
                    three_oh_four = True
                    self._error.fatal = False
                    # Need to do this to ensure that the crawler
                    # proceeds further!
                    content_type = self.get_content_type()
                    urlobj.manage_content_type(content_type)                    
                    break
                if errnum in range(400, 407):
                    # 400 => bad request
                    # 401 => Unauthorized
                    # 402 => Payment required (not used)
                    # 403 => Forbidden
                    # 404 => Not found
                    # 405 => Method not allowed
                    # 406 => Not acceptable
                    self._error.fatal = True
                elif errnum == 407:
                    # Proxy authentication required
                    self._proxy_query(1, 1)
                elif errnum == 408:
                    # Request timeout, try again
                    pass
                elif errnum == 412:
                    # Pre-condition failed, this has been
                    # detected due to our user-agent on some
                    # websites (sample URL: http://guyh.textdriven.com/)
                    self._error.fatal =  True
                elif errnum in range(409, 418):
                    # Error codes in 409-417 contain a mix of
                    # fatal and non-fatal states. For example
                    # 410 indicates requested resource is no
                    # Longer available, but we could try later.
                    # However for all practical purposes, we
                    # are marking these codes as fatal errors
                    # for the time being.
                    self._error.fatal = True
                elif errnum == 500:
                    # Internal server error, can try again
                    pass
                elif errnum == 501:
                    # Server does not implement the functionality
                    # to fulfill the request - fatal
                    self._error.fatal = True
                elif errnum == 502:
                    # Bad gateway, can try again ?
                    pass
                elif errnum in (503, 506):
                    # 503 - Service unavailable
                    # 504 - Gatway timeout
                    # 505 - HTTP version not supported
                    self._error.fatal = True

                if self._error.fatal:
                    rulesmgr.add_to_filter(urltofetch)                

            except urllib2.URLError, e:
                errdescn = ''
                self._error.errclass = "URLError"
                    
                try:
                    errbasic, errdescn = (str(e)).split(':',1)
                    parts = errbasic.split()                            
                except:
                    try:
                        errbasic, errdescn = (str(e)).split(',')
                        parts = errbasic.split('(')
                        errdescn = (errdescn.split("'"))[1]
                    except:
                        pass

                try:
                    self._error.number = int(parts[-1])
                except:
                    pass
                
                if errdescn:
                    self._error.msg = errdescn

                if self._error.msg:
                    error(self._error.msg, '=> ',urltofetch)
                else:
                    error('URLError:',urltofetch)

                errnum = self._error.number

                # URL error basically wraps up socket error numbers
                # Why did I decide 10049 etc stand for Proxy server
                # error ? Need to check this...
                if errnum == 10049 or errnum == 10061: # Proxy server error
                    self._proxy_query(1, 1)

            except IOError, e:
                self._error.number = URL_IO_ERROR
                self._error.fatal=True
                self._error.errclass = "IOError"                                    
                self._error.msg = str(e)                    
                # Generated by invalid ftp hosts and
                # other reasons,
                # bug(url: http://www.gnu.org/software/emacs/emacs-paper.html)
                error(e,'=>',urltofetch)

            except BadStatusLine, e:
                self._error.number = URL_BADSTATUSLINE
                self._error.msg = str(e)
                self._error.errclass = "BadStatusLine"                                    
                error(e, '=> ',urltofetch)

            except TypeError, e:
                self._error.number = URL_TYPE_ERROR
                self._error.msg = str(e)
                self._error.errclass = "TypeError"                                    
                error(e, '=> ',urltofetch)
                
            except ValueError, e:
                self._error.number = URL_VALUE_ERROR
                self._error.msg = str(e)
                self._error.errclass = "ValueError"                                    
                extrainfo(e, '=> ',urltofetch)

            except AssertionError, e:
                self._error.number = URL_ASSERTION_ERROR
                self._error.msg = str(e)
                self._error.errclass = "AssertionError"                                    
                error(e ,'=> ',urltofetch)

            except socket.error, e:
                self._error.number = URL_SOCKET_ERROR                
                self._error.msg = str(e)
                self._error.errclass = "SocketError"                                    
                errmsg = self._error.msg

                error('Socket Error: ',errmsg,'=> ',urltofetch)

            except HarvestManFileObjectException, e:
                self._error.number = FILEOBJECT_EXCEPTION
                self._error.msg = str(e)
                self._error.errclass = "HarvestManFileObjectException"                                    
                errmsg = self._error.msg

                error('HarvestManFileObjectException: ',errmsg,'=> ',urltofetch)
                
            # attempt reconnect after some time
            # self.evnt.sleep()
            time.sleep(self._sleeptime)

        if self._data or self._datalen:
            return CONNECT_YES_DOWNLOADED
        else:
            return CONNECT_NO_ERROR
        
    def get_error(self):
        """ Returns the error object """
        
        return self._error

    def set_content_info(self, urlobj):
        """ Sets the contents information on the url object 'urlobj' """

        # set this on the url object
        if self._headers:
            urlobj.set_url_content_info(self._headers)

    def set_http_headers(self):
        """ Sets http header dictionary from current request """

        self._headers.clear()
        for key,val in dict(self._freq.headers).iteritems():
            self._headers[key] = val

        # print self._headers

    def print_http_headers(self):
        """ Prints the HTTP headers for this connection """

        print 'HTTP Headers '
        for k,v in self._headers.iteritems():
            print k,'=> ', v

        print '\n'

    def get_content_length(self):
        """ Returns the content length after fetching a URL """
        
        clength = self._headers.get('content-length', 0)
        if clength != 0:
            # Sometimes this could be two numbers
            # separated by commas.
            return int(clength.split(',')[0].strip())
        else:
            return self._datalen

    def check_content_length(self):
        """ Checks whether content length of a URL is within the
        limits of the maximum allowed file size """

        # check for min & max file size
        try:
            length = int(self.get_content_length())
        except:
            length = 0
            
        return (length <= self._cfg.maxfilesize)
        
    def get_content_type(self):
        """ Returns content type after fetching a URL """

        ctype = self._headers.get('content-type','')
        if ctype:
            # Sometimes content type
            # definition might have
            # the charset information,
            # - .stx files for example.
            # Need to strip out that
            # part, if any
            if ctype.find(';') != -1:
                ctype2, charset = ctype.split(';',1)
                if ctype2: ctype = ctype2
            
        return ctype

    def get_etag(self):
        """ Returns the 'etag' header information """
        
        return self._headers.get('etag','')
    
    def get_last_modified_time(self):
        """ Returns the 'last-modified' header information """
        
        return self._headers.get('last-modified','')

    def get_content_encoding(self):
        """ Returns the 'content-encoding' header information """
        
        return self._headers.get('content-encoding', 'plain')

    def _write_url(self, urlobj, overwrite=False):
        """ Writes the data for the URL object 'urlobj' to a disk file (internal method) """

        # Raise writeurl event
        if objects.eventmgr.raise_event('writeurl', urlobj, data=self._data)==False:
            extrainfo('Filtering write of URL',urlobj)
            return WRITE_URL_FILTERED

        if self.blockwrite:
            return WRITE_URL_BLOCKED
        
        dmgr = objects.datamgr
        
        # If the file does not exist...
        fname = urlobj.get_full_filename()
        if not os.path.isfile(fname):
            # Recalculate locations to check if there is any error
            # in computed directories/filenames - like saving a
            # filename, when its parent directory is saved as a
            # file or trying to save as file when there is already
            # a directory in that name etc... This is a fix for
            # EIAO bug #491 - sample websites: www.nyc.estemb.org
            # and www.est-emb.fr
            urlobj.recalc_locations()
            directory = urlobj.get_local_directory()

            if SUCCESS(dmgr.create_local_directory(directory)):
                if SUCCESS(self._write_url_filename( urlobj.get_full_filename())):
                    return WRITE_URL_OK
                else:
                    return WRITE_URL_FAILED
                
            else:
                error("Error in creating local directory for", urlobj.get_full_url())
                return WRITE_URL_FAILED
        else:
            debug("File exists => ",urlobj.get_full_filename())
            # File exists - could be many reasons for it (redirected URL
            # duplicate download etc) - first check if this is a redirected
            # URL.
            if urlobj.reresolved:
                # Get old filename and save in it
                urlobj.useoldfilename = True
                directory = urlobj.get_local_directory_old()

                if SUCCESS(dmgr.create_local_directory(directory)):
                    if SUCCESS(self._write_url_filename( urlobj.get_full_filename_old())):
                        return WRITE_URL_OK
                    else:
                        return WRITE_URL_FAILED
                else:
                    error("Error in creating local directory for", urlobj.get_full_url())
                    return WRITE_URL_FAILED
            else:
                if overwrite:
                    extrainfo("Over-writing file =>",urlobj.get_full_filename())
                else:
                    # Save as filename.1 etc
                    index = 1
                    fname2 = fname
                    rootfname = urlobj.validfilename
                    
                    while os.path.isfile(fname2):
                        urlobj.validfilename = rootfname + '.' + str(index)
                        fname2 = urlobj.get_full_filename()
                        index += 1

                directory = urlobj.get_local_directory()

                if SUCCESS(dmgr.create_local_directory(directory)):
                    if SUCCESS(self._write_url_filename( urlobj.get_full_filename())):
                        return WRITE_URL_OK
                    else:
                        WRITE_URL_FAILED
                else:
                    error("Error in creating local directory for", urlobj.get_full_url())
                    return WRITE_URL_FAILED

    def _write_url_filename(self, filename, overwrite=True, printmsg=False):
        """ Writes downloaded data for a URL to the file named 'filename' """

        if self.blockwrite:
            return WRITE_URL_BLOCKED
        
        if self._data=='' and self._datalen==0:
            return DATA_EMPTY_ERROR

        if not overwrite:
            # Recalcuate new filename...
            origfilepath, n = filename, 1
        
            while os.path.isfile(filename):
                filename = ''.join((origfilepath,'.',str(n)))
                n += 1

        try:
            extrainfo('Writing file ', filename)
            if self._mode==CONNECTOR_DATA_MODE_INMEM:
                f=open(filename, 'wb')
                f.write(self._data)
                f.close()
            else:
                # Rename file
                if os.path.isfile(self._tmpfname):
                    # If gzip-encoded, we need to deflate data
                    if self.get_content_encoding().strip().find('gzip') != -1:
                        try:
                            g=gzip.GzipFile(fileobj=open(self._tmpfname, 'rb'))
                            # Open file for writing and write block by block
                            f=open(filename, 'wb')
                            while 1:
                                block = g.read(8192)
                                if block=='':
                                    f.flush()
                                    f.close()
                                    break
                                else:
                                    f.write(block)
                                    f.flush()
                            g.close()
                        except (IOError, OSError), e:
                            return FILE_WRITE_ERROR
                    else:
                        shutil.move(self._tmpfname, filename)
                    
            if os.path.isfile(filename):
                self._writelen = os.path.getsize(filename)

                if printmsg:
                    print '\nSaved to %s' % filename    
                return FILE_WRITE_OK
                
        except IOError,e:
            error('IO Error:', str(e))
            return FILE_WRITE_ERROR
        except ValueError, e:
            error(str(e))
            return FILE_WRITE_ERROR

        return FILE_WRITE_ERROR

    def write_url_info_file(self, url):
        """ Writes an information file in temporary directory for
        the URL. This will support HTTP resuming in case of partial
        downloads (Used by Hget) """

        # Used only by hget now
        info_file = os.path.join(os.path.dirname(self._tmpfname),
                                 ''.join((".info#",str(abs(hash(url))))))

        if not os.path.isfile(info_file):
            try:
                open(info_file, 'wb').write(str(self._headers))
            except (OSError, IOError), e:
                print e

    def print_download_stats(self, statsdict):
        """ Prints download statistics such as bytes transferred, time and speed """

        # Used by hget...
        print '%(BYTES)s bytes downloaded in %(TIME)s hours at an average of %(BANDWIDTH)s kb/s.' % statsdict
        
    def wrapper_connect(self, urlobj):
        """ Wrapper method for the connect/connect2 methods """

        if self._cfg.nocrawl:
            return self.connect2(urlobj)
        else:
            url = urlobj.get_full_url()
            # See if this URL is in cache, then get its lmt time & data
            lmt = objects.datamgr.get_last_modified_time(urlobj)
            return self.connect(urlobj, True, self._cfg.retryfailed, lmt)            
                        
    def save_url(self, urlobj):
        """ Downloads data for url represented by 'urlobj' and saves the
        downloaded data to disk """

        # Rearranged this to take care of http 304
        url = urlobj.get_full_url()

        # See if this URL is in cache, then get its lmt time & data

        # If data caching is enabled, we cannot use this since
        # we will not have any data to parse...
        lmt, cached_data, etag, filefound = '', '', '', ''

        filefound = os.path.isfile(urlobj.get_full_filename())
        
        if self._cfg.datacache:
            cached_data = objects.datamgr.get_url_cache_data(urlobj)
            
        # Makes sense to do this only if we find the cached data or the file...
        if (cached_data or filefound) and not urlobj.starturl:
            lmt = objects.datamgr.get_last_modified_time(urlobj)
            etag = objects.datamgr.get_etag(urlobj)

        urlobj.qstatus = urlparser.URL_IN_DOWNLOAD
        res = self.connect(urlobj, True, self._cfg.retryfailed, lmt, etag)
        urlobj.qstatus = urlparser.URL_DONE_DOWNLOAD
        
        # If it was a rules violation or error, skip it
        if res in (CONNECT_NO_RULES_VIOLATION, CONNECT_NO_ERROR):
            return res

        # If this became a request for multipart download
        # wait for the download to complete.
        #if res == CONNECT_MULTIPART_DOWNLOAD:
        #    # Trying multipart download...
        #    pool = objects.datamgr.get_url_threadpool()
        #    while not pool.get_multipart_download_status(urlobj):
        #        time.sleep(2.0)

        #    data = pool.get_multipart_url_data(urlobj)
        #    self._data = data

        #    if SUCCESS(self._write_url(urlobj)):
        #        return DOWNLOAD_YES_OK
        #    else:
        #        return DOWNLOAD_NO_ERROR

        if res == CONNECT_NO_UPTODATE:
            # Set the data as cache-data
            self._data = cached_data
            
        # Apply word filter
        if not urlobj.starturl:
            if urlobj.is_webpage() and objects.rulesmgr.apply_word_filter(self._data):
                extrainfo("Word filter prevents download of url =>", url)
                return DOWNLOAD_NO_RULE_VIOLATION

        # If no need to save html files return from here
        if urlobj.is_webpage() and not self._cfg.html:
            extrainfo("Html filter prevents download of url =>", url)
            return DOWNLOAD_NO_RULE_VIOLATION

        # Get last modified time
        timestr = self.get_last_modified_time()
        if timestr:
            try:
                lmt = time.mktime( time.strptime(timestr, "%a, %d %b %Y %H:%M:%S GMT"))
            except ValueError, e:
                pass
        
        filename = urlobj.get_full_filename()
        update, fileverified = False, False

        datalen = self.get_content_length()
        etag = self.get_etag()
        
        if self._cfg.cachefound:
            update, fileverified = objects.datamgr.is_url_cache_uptodate(urlobj, filename, self._data, datalen, lmt, etag)

            # If this caused a 304 error, then our copy is up-to-date so nothing to be done.
            # print update, fileverified
            if res == CONNECT_NO_UPTODATE:
                if update and fileverified:
                    extrainfo("Project cache is uptodate (304) =>", url)
                    return DOWNLOAD_NO_UPTODATE
            
            # No need to download
            elif update and fileverified:
                extrainfo("Project cache is uptodate =>", url)
                return DOWNLOAD_NO_UPTODATE                        

            # If cache is up to date, but someone has deleted
            # the downloaded files, instruct data manager to
            # write file from the cache.
            if update and not fileverified:
                if objects.datamgr.write_file_from_cache(urlobj):
                    return DOWNLOAD_NO_CACHE_SYNCED
                else:
                    return DOWNLOAD_NO_CACHE_SYNC_FAILED
        else:
            objects.datamgr.update_cache_for_url(urlobj, filename, self._data, datalen, lmt, etag)

        # Overwrite flag...
        # If file exists, but is not up to date
        # it needs to be overwritten...
        overwrite = fileverified and (not update)

        retval = self._write_url(urlobj, overwrite)
        
        if SUCCESS(retval):
            # Update saved bytes
            objects.datamgr.update_saved_bytes(self._writelen)
            return DOWNLOAD_YES_OK
        
        elif retval == WRITE_URL_FILTERED:
            return DOWNLOAD_NO_WRITE_FILTERED
        else:
            return DOWNLOAD_NO_ERROR

    def calc_bandwidth(self, urlobj):
        """ Calculates bandwidth of the user's network by downloading URL specified by 'urlobj' """

        url = urlobj.get_full_url()
        # Set verbosity to silent
        logobj = objects.logger
        self._cfg.verbosity = 0
        logobj.setLogSeverity(0)

        # Reset force-split, otherwise download
        # will be split!
        fs = self._cfg.forcesplit
        self._cfg.forcesplit = False
        ret = self.connect2(urlobj, showprogress=False)
        # Reset verbosity
        self._cfg.verbosity = self._cfg.verbosity_default
        logobj.setLogSeverity(self._cfg.verbosity)

        # Set it back
        self._cfg.forcesplit = fs
        
        if self._data:
            return float(len(self._data))/(self._elapsed)
        else:
            return 0

    def write_data_from_tempfiles(self, tmpflist, filename, overwrite=True, printmsg=False):
        """ Writes data from a list of temporary files and save it to the given filename.
        If writing is successful the temporary files are removed. If the argument 'overwrite'
        is True, the file is overwritten if it exists already, else a new filename is
        constructed. The last argument can be used to print a message informing that the
        writing is completed """

        # The temporary files should contain
        # the data in the required order, since this function
        # does not have any logic to automatically order pieces
        # of data 

        if not overwrite:
            # Recalcuate new filename...
            origfilepath, n = filename, 1
            
            while os.path.isfile(filename):
                filename = ''.join((origfilepath,'.',str(n)))
                n += 1

        # If some-one calls this with a single-file, just do a renaming
        if len(tmpflist)==1:
            shutil.copy2(tmpflist[0], filename)
            os.remove(tmpflist[0])
            
            if os.path.isfile(filename):
                if printmsg: print '\nSaved to %s' % filename
                return FILE_WRITE_OK
            else:
                return FILE_WRITE_ERROR
            
        try:
            # Provide a spinning cursor...
            spinner = InfiniteSpinCursor(msg='Assembling file chunks...')
            spinner.start()

            # On a POSIX system this is best done by using the "cat" command.
            # Look for the 'cat' command..
            catcommand=''

            if os.name=='posix':
                # 'cat' should be in /usr/bin, /bin or /usr/local/bin
                for catpath in ('/bin/cat','/usr/bin/cat','/usr/local/bin/cat'):
                    if os.path.isfile(catpath):
                        catcommand = catpath
                        break

            if catcommand != '':
                # Create the command line
                cmdline = 'cat ' + ' '.join(tmpflist) + '>' + filename
                ret = os.system(cmdline)
            else:
                # Do this in Python...
                cf = open(filename, 'wb')
                # Combine data into one
            
                # If any of the file has a size larger than sys.maxint, reading it
                # at once go would produce an overflow error.
                if reduce(lambda x,y: x or y, [os.path.getsize(f) >= sys.maxint for f in tmpflist]):
                    # Find files which have huge sizes
                    hugefiles = []
                    for x in range(len(tmpflist)):
                        f = tmpflist[x]
                        if os.path.getsize(f) >= sys.maxint:
                            hugefiles.append(x)

                    # For hugefiles, read upto sys.maxint -1 at a time...
                    # However, this is going to be incredibly slow for huge files...
                    for x in range(len(tmpflist)):
                        f = tmpflist[x]
                        if x in hugefiles:
                            try:
                                fptr = open(f, 'rb')
                                while True:
                                    data = fptr.read(sys.maxint - 1)
                                    if data=='': break
                                    cf.write(data)
                                    cf.flush()
                                fptr.close()
                            except Exception, e:
                                print e
                        else:
                            data = open(f, 'rb').read()
                            cf.write(data)
                            cf.flush()                                

                else:
                    for f in tmpflist:
                        # print 'Appending data from',f,'...'
                        data = open(f, 'rb').read()
                        cf.write(data)
                        cf.flush()

                cf.close()
                
            spinner.stop()

            if os.path.isfile(filename):
                if printmsg:
                    print '\nSaved to %s' % filename
            
                for f in tmpflist:
                    try:
                        os.remove(f)
                    except OSError, e:
                        pass
                
                return FILE_WRITE_OK
            else:
                return FILE_WRITE_ERROR
        except (IOError, OSError), e:
            print e        
            return FILE_WRITE_ERROR
    
    def url_to_file(self, urlobj):
        """ Downloads the URL encapsulated in 'urlobj' to disk. This method is
        the main method used by the Hget application to download files """

        # Reset counters on data reader class...
        HarvestManFileObject.reset()
        
        if self._cfg.hgetoutfile:
            n, filename = 1, self._cfg.hgetoutfile
        else:
            n, filename = 1, urlobj.get_filename()

        origfilename = filename

        currtmpfiles = []
        resuming = False

        # Use original URL hashes for temporary directory names
        # since URL can change dynamically.
        orig_url = urlobj.get_original_url()

        # Create temp folders for download
        if not self._cfg.hgetnotemp:
            tmpd = os.path.join(GetMyTempDir(), str(abs(hash(orig_url))))
            if not os.path.isdir(tmpd):
                # print 'Directory does not exist=>',tmpd
                try:
                    os.makedirs(tmpd)
                except OSError, e:
                    print e
                    print 'Error in creating temp directory %s!' % tmpd
                    return CREATE_DIRECTORY_NOT_OK
        else:
            tmpd =  '.'

        # Check if there is an info file containing the headers
        infof = os.path.join(tmpd, ''.join((".info#",
                                            str(abs(hash(urlobj.get_full_url()))))))

        flist = glob.glob(os.path.join(tmpd, ''.join(('.', origfilename, '#*'))))
        
        if self._cfg.canresume:
            # Check if a previous unfinished download exists
            # if so, only read from where we left off from
            # previous download.

            if flist:
                # Sort the files according to creation times
                tmpcflist = [(os.path.getctime(fname), fname) for fname in flist]
                tmpcflist.sort()
                # print 'Sorted list=>',tmpcflist
                cflist = [item[1] for item in tmpcflist]

                if os.path.isfile(infof):
                    print 'Temporary files from previous download found, trying to resume download...'
                    # We can proceed only if this file is there, since it contains
                    # all the header information of the previous attempt.
                    try:
                        hdict = eval(open(infof).read())
                        # print 'Header dict=>',hdict
                        # Get content length
                        clength = hdict.get('content-length','')
                        if clength:
                            clength = int(clength.split(',')[0].strip())
                        if clength:
                            # With the failover logic in hget, errors are quite less. So not sure
                            # whether to display warning with more than 3 pieces. However let it
                            # remain...
                            if len(cflist)>3:
                                print 'Warning: 3 or more temporary files found. Final file may have errors!'
                            totsz = sum([os.path.getsize(fname) for fname in cflist])
                            # Get difference in sizes
                            sztoget = clength - totsz
                            # If nothing to get, just save the temp file to original
                            if sztoget==0:
                                if SUCCESS(self.write_data_from_tempfiles(cflist, filename, False, True)):
                                    print 'No data was downloaded, data already present in temporary file for this URL'
                                    return DATA_ALREADY_PRESENT
                            else:
                                # Append filename to list of current temp files
                                # and set resuming to True
                                if self._mode == CONNECTOR_DATA_MODE_FLUSH:
                                    currtmpfiles = cflist

                                elif self._mode==CONNECTOR_DATA_MODE_INMEM:
                                    for tmpf in cflist:
                                        try:
                                            self._data += open(tmpf, 'rb').read()
                                        except IOError, e:
                                            print e

                                    self._datalen = len(self._data)
                                    # print 'Datalen=>',self._datalen

                                resuming = True
                                # print 'Fize=>',totsz,clength
                                urlobj.range = (totsz, clength+1)
                                # self._cfg.multipart = True                                    
                                print 'Resuming download...'
                    except SyntaxError, e:
                        print 'Error reading URL info file, cannot resume previous download...'
                        pass

        else:
            if len(flist):
                print 'Resume mode switched off, cleaning previous temporary files...',
                for tmpitem in flist:
                    try:
                        if os.path.isfile(tmpitem):
                            os.remove(tmpitem)
                    except OSError, e:
                        pass

                print 'done.'

            # Remove the info file
            if os.path.isfile(infof):
                try:
                    os.remove(infof)
                except OSError, e:
                    pass

        flist = glob.glob(os.path.join(tmpd, ''.join(('.', origfilename, '#*'))))

        url = urlobj.get_full_url()
        logconsole('Connecting to %s...' % urlobj.get_full_domain())

        start = time.time()
        ret = self.connect2(urlobj,resuming=resuming)
        end = time.time()
        
        status = URL_DOWNLOAD_FAILED

        # If a redirection is found, save URL in the redirected filename
        # unless the user has already specified an out filename.
        if self._cfg.hgetoutfile=='' and urlobj.redirected:
            filename = urlobj.filename
        
        if ret==CONNECT_MULTIPART_DOWNLOAD:
            # Trying multipart download...
            pool = objects.datamgr.get_url_threadpool()
            while True:
                multi_status = pool.get_multipart_download_status(urlobj)
                if multi_status in (MULTIPART_DOWNLOAD_ERROR, MULTIPART_DOWNLOAD_COMPLETED):
                    break
                
                time.sleep(1.0)

            end = time.time()

            if multi_status == MULTIPART_DOWNLOAD_COMPLETED:
                print 'Data download completed.'
                if self._mode == CONNECTOR_DATA_MODE_INMEM:
                    data = pool.get_multipart_url_data(urlobj)
                    self._data = data
                    if self._data:
                        status = URL_DOWNLOAD_OK
                    
                elif self._mode == CONNECTOR_DATA_MODE_FLUSH:
                    # Get url info
                    infolist = pool.get_multipart_url_info(urlobj)
                    infolist.sort()
                    debug('Info list=>',infolist)
                    # Get filenames
                    tmpflist = [item[1] for item in infolist]
                    debug(tmpflist)
                    # Temp file name
                    self._tmpfname = filename + '.tmp'

                    if SUCCESS(self.write_data_from_tempfiles(tmpflist, self._tmpfname)):
                        status = URL_DOWNLOAD_OK
                        
            elif multi_status == MULTIPART_DOWNLOAD_ERROR:
                print 'Data download could not be completed.'
                
        else:
            if self._data or self._datalen:
                status = URL_DOWNLOAD_OK

        if not SUCCESS(status):
            if self._error.msg:
                print 'Error:',self._error.msg

            # print 'Fatal=>',self._error.fatal
            if not self._error.fatal:
                self.write_url_info_file(url)
                
            print 'Download of URL',url ,'not completed.\n'
            return 
        
        tgap = end - start
        timestr = str(datetime.timedelta(seconds=int(tgap)))


        # Check if full data was downloaded...
        clen = self.get_content_length()
        if clen and (not urlobj.redirected) and (HarvestManFileObject.NETDATALEN != clen):
            print 'Error: Complete data was not downloaded!'
            print 'Expected: %d, Downloaded: %d' % (clen, HarvestManFileObject.NETDATALEN)
            print 'Download of URL',url ,'not completed.\n'
            
            return URL_DOWNLOAD_FAILED

        filesz = HarvestManFileObject.NETDATALEN                
        bandwidth = float(filesz)/float(1024*tgap)

        statsdict = { 'BYTES': filesz,
                      'TIME':  timestr,
                      'BANDWIDTH' : '%.2f' % bandwidth
                      }

        res = FILE_WRITE_ERROR

        if self._cfg.hgetoutdir != '.':
            outdir = self._cfg.hgetoutdir
            if not os.path.isdir(outdir):
                try:
                    os.makedirs(outdir)
                    # If an output director is specified, strip any directory
                    # part from the filename
                    filename = os.path.join(outdir, os.path.split(filename)[1]) 
                except OSError, e:
                    print 'Error in creating directory',e
            else:
                filename = os.path.join(outdir, os.path.split(filename)[1])                 

        if self._mode == CONNECTOR_DATA_MODE_INMEM:
            res = self._write_url_filename(filename, False, True)
            if SUCCESS(res):
                self.print_download_stats(statsdict)

        elif self._mode == CONNECTOR_DATA_MODE_FLUSH:

            if os.path.isfile(self._tmpfname):
                if resuming:
                    currtmpfiles.append(self._tmpfname)
                    tmpflist = currtmpfiles
                    res = self.write_data_from_tempfiles(tmpflist, filename, False, True)
                else:
                    res = self.write_data_from_tempfiles([self._tmpfname], filename, False, True)
                        
                if SUCCESS(res):
                    self.print_download_stats(statsdict)                    
                else:
                    print 'Error saving to file %s' % filename
            else:
                print 'Error saving to file %s' % filename


        # Perform cleanups for successful downloads
        if SUCCESS(res):
            if infof and os.path.isfile(infof):                
                try:
                    os.remove(infof)
                except OSError, e:
                    print e

            # Clean up files if resuming
            if resuming:
                # If this was resumed using temp files then
                # these files will be already cleaned up, but
                # will remain if resumed using in-mem flag.
                for f in currtmpfiles:
                    if os.path.isfile(f):
                        try:
                            os.remove(f)
                        except OSError, e:
                            print e
                        
            # Clean up temp directory if any
            if not self._cfg.hgetnotemp:
               if os.path.isdir(tmpd):
                   # print 'Cleaning up temporary directory...'
                   try:
                       shutil.rmtree(tmpd, True)
                   except OSError, e:
                       print e
                            
            return URL_DOWNLOAD_OK
        
        return URL_DOWNLOAD_OK

    def get_data(self):
        """ Returns the downloaded data string """
        
        return self._data
    
    def get_error(self):
        """ Returns last network error code """

        return self._error

    def get_fileobj(self):
        """ Returns a handle to internal HarvestMan file object """

        return self._fo

    def get_data_sofar(self):
        """ Returned the length of data downloaded so far """

        if self._fo:
            return self._fo.get_datalen()

        return 0
    
    def get_data_mode(self):
        """ Returns the data download mode """

        # 0 => Data is flushed
        # 1 => Data in memory (default)
        return self._mode

    def get_tmpfname(self):
        """ Returns temporary filename if any """

        return self._tmpfname

    def get_status(self):
        """ Returns the download status """

        return self._status

    def get_numtries(self):
        """ Returns the number of attempts in fetching a URL """

        return self._numtries

    def reset(self):
        """ Resets the attribute values """

        # file like object returned by
        # urllib2.urlopen(...)
        self._freq = urllib2.Request('file://')
        # data downloaded
        self._data = ''
        # length of data downloaded
        self._datalen = 0
        # length of data written
        self._writelen = 0
        # error dictionary
        self._error.reset()
        # Http header for current connection
        self._headers = CaselessDict()
        # Elasped time for reading data
        self._elapsed = 0.0
        # Status of connection
        # 0 => no connection
        # 1 => connected, download in progress
        self._status = 0
        # Number of tries
        self._numtries = 0
        
class HarvestManUrlConnectorFactory(object):
    """ Factory class for HarvestManUrlConnector class """

    klass = HarvestManUrlConnector
    alias = 'connfactory'                
    connector_count = 0
    
    def __init__(self, maxsize):
        """ Overloaded __init__ method """
        
        # The requests dictionary
        self._requests = {}
        self._sema = threading.BoundedSemaphore(maxsize)
        self._conndict = {}

    def create_connector(self):
        """ Creates and returns a connector object """

        # Even if the number of connections is
        # below the maximum, the number of requests
        # to the same server can exceed the maximum
        # count. So check for that condition. If
        # the number of current active requests to
        # the server is equal to the maximum allowd
        # this call will also block the calling
        # thread
        self._sema.acquire()

        # Make a connector 
        connector = self.__class__.klass()
        self._conndict[connector] = 1
        self.__class__.connector_count += 1
        
        return connector
        
    def remove_connector(self, conn):
        """ Removes a connector object after use """

        # Release the semaphore once to increase the internal count
        self.__class__.connector_count -= 1
        # print 'Connector removed, count is',self._count
        conn.release()
        del self._conndict[conn]       
        self._sema.release()

    def get_count(self):
        """ Return the current connector count """

        return self.__class__.connector_count

    def get_connector_dict(self):
        return self._conndict
    
# test code
if __name__=="__main__":
    set_aliases()
    
    conn = HarvestManUrlConnector()

    # Note: this test works only for a client
    # directly connected to the internet. If
    # you are behind a proxy, add proxy code of
    # harvestManUrlConnectorUrl class here.

    # FIXME: I need to move this initialize to somewhere else!
    # Check for http connections
    print 'Testing HTTP connections...'
    conn.url_to_file(urlparser.HarvestManUrl('http://www.python.org/index.html'))
    # print the HTTP headers
    conn.print_http_headers()

    # Check for ftp connections
    print 'Testing FTP connections...'  
    conn.url_to_file(urlparser.HarvestManUrl('ftp://ftp.gnu.org'))
    # print the HTTP headers
    conn.print_http_headers()   

