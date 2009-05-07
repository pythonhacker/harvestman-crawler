# -- coding: utf-8
""" rules.py - Rules checker module for HarvestMan.
    This module is part of the HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>

    Modification History
    --------------------

   Jan 8 2006          Anand    Updated this file from EIAO
                                repository to get fixes for robot
                                rules. Removed EIAO specific
                                code.

                                Put ext check rules before robots
                                check to speed up things.
   Jan 10 2006          Anand    Converted from dos to unix format
                                (removed Ctrl-Ms).

   April 11 2007        Anand   Not doing I.P comparison for
                                non-robots.txt URLs in compare_domains
                                method as it is erroneous.
                                

   Copyright (C) 2004 Anand B Pillai.
                                
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import socket
import re
import os
import time
import copy

from harvestman.lib.event import HarvestManEvent
from harvestman.lib import robotparser
from harvestman.lib.methodwrapper import MethodWrapperMetaClass
from harvestman.lib import urlparser
from harvestman.lib import filters

from harvestman.lib.common.common import *
from harvestman.lib.common.netinfo import tlds
from harvestman.lib.common.lrucache import LRU

# Defining pluggable functions
__plugins__ = {'violates_rules_plugin': 'HarvestManRulesChecker:violates_rules'}

# Defining functions with callbacks
__callbacks__ = {'violates_rules_callback' : 'HarvestManRulesChecker:violates_rules'}


class HarvestManRulesChecker(object):
    """ Class which checks the download rules for urls. These
    rules include depth checks, robot.txt rules checks, filter
    checks, external server/directory checks, duplicate url
    checks, maximum limits check etc. """

    # For supporting callbacks
    __metaclass__ = MethodWrapperMetaClass
    alias = 'rulesmgr'
    
    # Regular expression for matching www. infront of domains
    wwwre = re.compile(r'^www(\d*)\.')

    def __init__(self):
        self.reset()

    def reset(self):
        self._filter = {}
        self._extservers = Ldeque(1000)
        self._extdirs = Ldeque(1000)
        self._wordstr = '[\s+<>]'
        self._robots  = LRU(1000)
        self._robocache = Ldeque(1000)
        self._invalidservers = Ldeque(1000)
        # Flag for making filters
        self._madefilters = False
        self._configobj = objects.config
        self.junkfilter = filters.HarvestManJunkFilter()
        self.urlfilter =  filters.HarvestManUrlFilter(self._configobj.pathurlfilters,
                                                      self._configobj.extnurlfilters,
                                                      self._configobj.regexurlfilters)
        self.txtfilter = filters.HarvestManTextFilter(self._configobj.contentfilters,
                                                      self._configobj.metafilters)

    def violates_rules(self, urlObj):
        """ Check the basic rules for this url object,
        This function returns True if the url object
        violates the rules, else returns False """

        # raise event to allow custom logic
        ret = objects.eventmgr.raise_event('includelinks', urlObj)
        if ret==False:
            self.add_to_filter(urlObj.index)            
            return True
        elif ret==True:
            return False
        
        url = urlObj.get_full_url()

        # New in 2.0
        # If checking of rules on the type of this URL
        # is set to be skipped, return False
        if urlObj.typ in self._configobj.skipruletypes:
            return False
        
        # if this url exists in filter list, return
        # True rightaway
        try:
            self._filter[url.index]
            return True
        except KeyError:
            pass

        # now apply the url filter
        if self.apply_url_filter(urlObj):
            extrainfo("URL filter - filtered", url)
            self.add_to_filter(urlObj.index)
            return True

        # now apply the junk filter
        if self.junkfilter:
            if self.junkfilter.filter(urlObj):
                extrainfo("Junk Filter - filtered", url)
                self.add_to_filter(urlObj.index)                            
                return True

        # check if this is an external link
        if self.is_external_link( urlObj ):
            extrainfo("External link - filtered ", urlObj.get_full_url())
            self.add_to_filter(urlObj.index)
            return True

        # now apply REP
        if self.apply_rep(urlObj):
            extrainfo("Robots.txt rules prevents crawl of ", url)
            self.add_to_filter(urlObj.index)
            return True

        # depth check
        if self.apply_depth_check(urlObj):
            extrainfo("Depth exceeds - filtered ", urlObj.get_full_url())
            self.add_to_filter(urlObj.index)            
            return True

        return False

    def add_to_filter(self, urlindex):
        """ Add the link to the filter dictionary """

        self._filter[urlindex] = 1

    def compare_domains(self, domain1, domain2, robots=False):
        """ Compare two domains (servers) first by
        ip and then by name and return True if both point
        to the same server, return False otherwise. """

        # For comparing robots.txt file, first compare by
        # ip and then by name.
        if robots: 
            firstval=self.compare_by_ip(domain1, domain2)
            if firstval:
                return firstval
            else:
                return self.compare_by_name(domain1, domain2)

        # otherwise, we do only a name check
        else:
            return self.compare_by_name(domain1, domain2)

    def _get_base_server(self, server):
        """ Return the base server name of  the passed
        server (domain) name """

        # If the server name is of the form say bar.foo.com
        # or vodka.bar.foo.com, i.e there are more than one
        # '.' in the name, then we need to return the
        # last string containing a dot in the middle.
        if server.count('.') > 1:
            dotstrings = server.split('.')
            # now the list is of the form => [vodka, bar, foo, com]

            # Skip the list for skipping over tld domain name endings
            # such as .org.uk, .mobi.uk etc. For example, if the
            # server is games.mobileworld.mobi.uk, then we
            # need to return mobileworld.mobi.uk, not mobi.uk
            dotstrings.reverse()
            idx = 0
            
            for item in dotstrings:
                if item.lower() in tlds:
                    idx += 1
                
            return '.'.join(dotstrings[idx::-1])
        else:
            # The server is of the form foo.com or just "foo"
            # so return it straight away
            return server

    def compare_no_tld(self, domain1, domain2):
        """ Compare two server names without their tld endings """

        # This will return True for www.foo.com, www.foo.org
        # foo.co.uk etc.
        dotstrings1 = self.wwwre.sub('', domain1.lower()).split('.')
        dotstrings2 = self.wwwre.sub('', domain2.lower()).split('.')
        l1 = [item for item in dotstrings1 if item not in tlds]
        l2 = [item for item in dotstrings2 if item not in tlds]            
        debug(l1, l2)
        
        return '.'.join(l1) =='.'.join(l2)
        
    def compare_by_name(self, domain1, domain2):
        """ Compare two servers by their names. Return True
        if similar, False otherwise """

        # first check if both domains are same
        if domain1.lower() == domain2.lower(): return True
        # Check whether we are comparing something like www.foo.com
        # and foo.com, they are assumed to be same. 
        if self.wwwre.sub('',domain1.lower())==self.wwwre.sub('',domain2.lower()):
            return True

        # If ignoretlds is set to True, return True for two servers such
        # as www.foo.com and www.foo.co.uk, www.foo.org etc.
        if self._configobj.ignoretlds:
            if self.compare_no_tld(domain1, domain2):
                return True
            
        if not self._configobj.subdomain:
            # Checks whether the domain names belong to
            # the same base server, if the above config
            # variable is set. For example, this will
            # return True for two servers like server1.foo.com
            # and server2.foo.com or server1.base and server2.base
            baseserver1 = self.wwwre.sub('',self._get_base_server(domain1))
            baseserver2 = self.wwwre.sub('',self._get_base_server(domain2))
            debug('Bases=>',baseserver1, baseserver2)
            
            # Instead of checking for equality, check for endswith.
            # This will return True even for cases like
            # vanhall-larenstein.nl and larenstein.nl
            if self._configobj.ignoretlds:
                if self.compare_no_tld(baseserver1, baseserver2):
                    return True
                
            return baseserver1.lower().endswith(baseserver2.lower())
            # return (baseserver1.lower() == baseserver2.lower())
        else:
            # if the subdomain variable is set will return False for two servers like
            # server1.foo.com and server2.foo.com i.e with same base domain but different
            # subdomains.
            return False

    def compare_by_ip(self, domain1, domain2):
        """ Compare two servers by their ip address. Return
        True if same, False otherwise """

        try:
            ip1 = socket.gethostbyname(domain1)
            ip2 = socket.gethostbyname(domain2)
        except Exception:
            return False

        if ip1==ip2: return True
        else: return False

    def apply_url_filter(self, urlObj):
        """ Apply URL filter to the URL. Return True if filtered and False otherwise """

        return self.urlfilter.filter(urlObj)

    def apply_text_filter(self, document, urlObj):
        """ Apply text filter to the document object. Return True if filtered and
        False otherwise """

        return self.txtfilter.filter(document, urlObj)
        
    def apply_rep(self, urlObj):
        """ See if the robots.txt file on the server
        allows fetching of this url. Return 0 on success
        (fetching allowed) and 1 on failure(fetching blocked) """

        # robots option turned off
        if self._configobj.robots==0: return False
        
        domport = urlObj.get_full_domain_with_port()
        # The robots.txt file url
        robotsfile = "".join((domport, '/robots.txt'))

        # Check #1
        # if this url exists in filter list, return
        # True rightaway
        try:
            self._filter[urlObj.index]
            return True
        except KeyError:
            pass

        url_directory = urlObj.get_url_directory()

        # Check #2: Check if this directory
        # is already there in the white list
        try:
            self._robocache.index(url_directory)
            return False
        except ValueError:
            pass

        try:
            rp = self._robots[domport]
            # Check #4
            # If there is an entry, but it
            # is None, it means there is no
            # robots.txt file in the server
            # (see below). So return False.
            if not rp: return False
        except KeyError:
            # Not there, create a fresh
            # one and add it.
            rp = robotparser.RobotFileParser()
            rp.set_url(robotsfile)
            ret = rp.read()
            # Check #5                
            if ret==-1:
                # no robots.txt file
                # Set the entry for this
                # server as None, so next
                # time we dont need to do
                # this operation again.
                self._robots[domport] = None
                return False
            else:
                # Set it
                self._robots[domport] = rp
        
        # Check #6
        if rp.can_fetch(self._configobj.USER_AGENT, url_directory):
            # Add to white list
            self._robocache.append(url_directory)
            return False

        # Cannot fetch, so add to filter
        # for quick look up later.
        
        return True

    def apply_word_filter(self, data):
        """ Apply the word filter """

        if self._configobj.wordfilter:
            if self._configobj.wordfilterre.search(data):
                return True
            else:
                return False

        return False

    def is_under_starting_directory(self, urlObj):
        """ Check whether the url in the url object belongs
        to the same directory as the starting url for the
        project """

        directory = urlObj.get_url_directory()
        baseUrlObj = objects.queuemgr.get_base_url()
        if not baseUrlObj:
            return True

        # Bug: the original URL might have had been
        # redirected, so its base URL might have got
        # changed. We need to check with the original
        # URL in such cases.
        # Sample site: http://www.vegvesen.no

        if baseUrlObj.reresolved:
            # bdir = baseUrlObj.get_original_url_directory()
            old_urlobj = baseUrlObj.get_original_state()
            bdir = old_urlobj.get_url_directory()
        else:
            bdir = baseUrlObj.get_url_directory()
            
        # print 'BASEDIR=>',bdir
        # print 'DIRECTORY=>',directory

        # Look for bdir inside dir
        index = directory.find(bdir)
        
        if index == 0:
            return True

        # Sometimes a simple string match
        # is not good enough. May be both
        # the directories are the same but
        # the server names are slightly different
        # ex: www-106.ibm.com and www.ibm.com
        # for developerworks links.

        # Check if both of them are in the same
        # domain
        if self.compare_domains(urlObj.get_domain(), baseUrlObj.get_domain()):
            debug('Domains',urlObj.get_domain(),'and',baseUrlObj.get_domain(),'compare fine')
            # Get url directory sans domain
            directory = urlObj.get_url_directory_sans_domain()
            bdir = baseUrlObj.get_url_directory_sans_domain()
            debug('Directories',directory,bdir)
            
            # Check again
            if directory.find(bdir) == 0:
                return True

        return False
            
    def is_external_server_link(self, urlObj):
        """ Check whether the url in the url object belongs to
        an external server """

        # Get the tracker queue object
        baseUrlObj = objects.queuemgr.get_base_url()
        if not baseUrlObj:
            return False

        # Check based on the server
        server = urlObj.get_domain()
        baseserver = baseUrlObj.get_domain()

        return not self.compare_domains( server, baseserver )

    def is_external_link(self, urlObj):
        """ Check if the url is an external link relative to starting url,
        using the download rules set by the user """

        # Example.
        # Assume our start url is 'http://www.server.com/files/images/index.html"
        # Then any url which starts with another server name or at a level
        # above the start url's base directory on the same server is considered
        # an external url
        # i.e, http://www.yahoo.com will be external because of
        # 1st reason &
        # http://www.server.com/files/search.cgi will be external link because of
        # 2nd reason.
        # External links ?

        # if under the same starting directory, return False
        if self.is_under_starting_directory(urlObj):
            return False

        directory = urlObj.get_url_directory()

        baseUrlObj = objects.queuemgr.get_base_url()
        if not baseUrlObj:
            return False

        if urlObj.get_type() == 'stylesheet':
            if self._configobj.getstylesheets: return False

        elif urlObj.get_type() == 'image':
            if self._configobj.getimagelinks: return False

        if not self.is_external_server_link(urlObj):
            debug('Same!')
            if self._configobj.fetchlevel==0:
                return True
            
            elif self._configobj.fetchlevel==3:
                # check for the directory of the parent url
                # if it is same as starting directory, allow this
                # url, else deny
                try:
                    parentUrlObj = urlObj.get_parent_url()
                    if not parentUrlObj:
                        return False

                    parentdir = parentUrlObj.get_url_directory()
                    bdir = baseUrlObj.get_url_directory()

                    if parentdir == bdir:
                        self._increment_ext_directory_count(directory)
                        return False
                    else:
                        return True
                except urlparser.HarvestManUrlError, e:
                    logconsole(e)
                    
            elif self._configobj.fetchlevel > 0:
                # do other checks , just fall through
                pass
            
            # Increment external directory count
            # directory = urlObj.get_url_directory()

            # res=self._ext_directory_check(directory)
            # if not res:
            #    extrainfo("External directory error - filtered!")
            #    return True

            # Apply depth check for external dirs here
            if self._configobj.extdepth:
                if self.apply_depth_check(urlObj, mode=2):
                    return True

            #if self._configobj.epagelinks:
            #    # We can get external links belonging to same server,
            #    # so this is not an external link
            #    return False
            #else:
            #    # We cannot get external links belonging to same server,
            #    # so this is an external link
            #    return True
            return False
        else:
            # print 'Different!',self._configobj.fetchlevel
            debug('Different!')
            # Both belong to different base servers
            if self._configobj.fetchlevel==0 or self._configobj.fetchlevel == 1:
                return True
            elif self._configobj.fetchlevel==2 or self._configobj.fetchlevel==3:
                # check whether the baseurl (parent url of this url)
                # belongs to the starting server. If so allow fetching
                # else deny. ( we assume the baseurl path is not relative! :-)
                try:
                    parentUrlObj = urlObj.get_parent_url()
                    baseserver = baseUrlObj.get_domain()

                    if not parentUrlObj:
                        return False

                    server = urlObj.get_domain()
                    if parentUrlObj.get_domain() == baseserver:
                        self._increment_ext_server_count(server)
                        return False
                    else:
                        return True
                except urlparser.HarvestManUrlError, e:
                    logconsole(e)
                    
            elif self._configobj.fetchlevel>3:
                pass
                # this option takes precedence over the
                # extserverlinks option, so set extserverlinks
                # option to true.
                # self._configobj.eserverlinks=1
                # do other checks , just fall through

            # res = self._ext_server_check(urlObj.get_domain())
            # if not res:
            #   return True

            # Apply depth check for external servers here
            if self._configobj.extdepth:
                if self.apply_depth_check(urlObj, mode=2):
                    return True

            #if self._configobj.eserverlinks:
            #    # We can get links belonging to another server, so
            #    # this is NOT an external link
            #    return False
            #else:
            #    # We cannot get external links beloning to another server,
            #    # so this is an external link
            #    return True
            return False
        
        # We should not reach here
        return False

    def apply_depth_check(self, urlObj, mode=0):
        """ Apply the depth setting for this url, if any """

        # depth variable is -1 means no depth-check
        baseUrlObj = objects.queuemgr.get_base_url()
        if not baseUrlObj:
            return False

        reldepth = urlObj.get_relative_depth(baseUrlObj, mode)

        if reldepth != -1:
            # check if this exceeds allowed depth
            if mode == 0 and self._configobj.depth != -1:
                if reldepth > self._configobj.depth:
                    return True
            elif mode == 2 and self._configobj.extdepth:
                if reldepth > self._configobj.extdepth:
                    return True

        return False

    ## def _ext_directory_check(self, directory):
    ##     """ Check whether the directory <directory>
    ##     should be considered external """

    ##     index=self._increment_ext_directory_count(directory)

    ##     # Are we above a prescribed limit ?
    ##     if self._configobj.maxextdirs and len(self._extdirs)>self._configobj.maxextdirs:
    ##         if index != -1:
    ##             # directory index was below the limit, allow its urls
    ##             if index <= self._configobj.maxextdirs:
    ##                 return True
    ##             else:
    ##                 # directory index was above the limit, block its urls
    ##                 return False
    ##         # new directory, block its urls
    ##         else:
    ##             return False
    ##     else:
    ##         return True

    ## def _ext_server_check(self, server):
    ##     """ Check whether the server <server> should be considered
    ##     external """

    ##     index=self._increment_ext_server_count(server)

    ##     # are we above a prescribed limit ?
    ##     if self._configobj.maxextservers and len(self._extservers)>self._configobj.maxextservers:
    ##         if index != -1:
    ##             # server index was below the limit, allow its urls
    ##             if index <= self._configobj.maxextservers:
    ##                 return True
    ##             else:
    ##                 return False
    ##         # new server, block its urls
    ##         else:
    ##             return False
    ##     else:
    ##         return True

    def _increment_ext_directory_count(self, directory):
        """ Increment the external dir count """

        index=-1
        try:
            index=self._extdirs.index(directory)
        except:
            self._extdirs.append(directory)

        return index

    def _increment_ext_server_count(self,server):
        """ Increment the external server count """

        index=-1
        try:
            index=self._extservers.index(server)
        except:
            self._extservers.append(server)

        return index

    def get_stats(self):
        """ Return statistics as a 3 tuple. This returns
        a 3 tuple of number of links, number of servers, and
        number of directories in the base server parsed by
        url trackers """

        numservers=len(self._extservers)
        numdirs=len(self._extdirs)
        numfiltered = len(self._filter)
        
        return (numservers, numdirs, numfiltered)

    def make_filters(self):
        pass
    
   ##  def make_filters(self):
##         """ This function creates the filter regexps
##         for url/text based filtering of content """

##         # URL regex filters
        
##         url_filters = self._make_filter(urlfilterstr)
##         # print 'URL FILTERS=>',url_filters
        
##         self._configobj.set_option('urlfilterre_value', url_filters)


##         server_filters = self._make_filter(serverfilterstr)
##         self._configobj.set_option('serverfilterre_value', server_filters)

##         #  url/server priority filters
##         urlprioritystr = self._configobj.urlpriority
##         # The return is a dictionary
##         url_priorities = self._make_priority(urlprioritystr)

##         self._configobj.set_option('urlprioritydict_value', url_priorities)

##         serverprioritystr = self._configobj.serverpriority
##         # The return is a dictionary        
##         server_priorities = self._make_priority(serverprioritystr)

##         self._configobj.set_option('serverprioritydict_value', server_priorities)

##         # word filter list
##         wordfilterstr = self._configobj.wordfilter.strip()
##         # print 'Word filter string=>',wordfilterstr,len(wordfilterstr)
##         if wordfilterstr:
##             word_filter = self._make_word_filter(wordfilterstr)
##             self._configobj.wordfilterre = word_filter

##         self._madefilters = True
        
    def _make_priority(self, pstr):
        """ Generate a priority dictionary from the priority string """

        # file priority is based on file extensions &
        # server priority based on server names

        # Priority string is of the form...
        # str1+pnum1,str2-pnum2,str3+pnum3 etc...
        # Priority range is from [-5 ... +5]

        # Split the string based on commas
        pr_strs = pstr.split(',')

        # For each string in list, create a dictionary
        # with the string as key and the priority (including
        # sign) as the value.

        d = {}
        for s in pr_strs:
            if s.find('+') != -1:
                key, val = s.split('+')
                val = int(val)

            elif s.find('-') != -1:
                key, val = s.split('-')
                val = -1*int(val)
            else:
                continue

            # Since we dont allow values outside
            # the range [-5 ..5] skip such values
            if val not in range(-5,6): continue
            d[key.lower()] = val

        return d

    def _make_word_filter(self, s):
        """ Create a word filter rule for HarvestMan """

        return re.compile(s, re.IGNORECASE|re.UNICODE)

    def clean_up(self):
        """ Purge data for a project by cleaning up
        lists, dictionaries and resetting other member items"""

        debug('Rules got cleaned up...!')
        
        self._filter = {}
        self._extservers = []
        self._extdirs = []
        self._robocache = []
        # Reset dicts
        self._robots.clear()
        
