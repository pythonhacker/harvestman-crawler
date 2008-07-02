# -- coding: utf-8
""" config.py - Module to keep configuration options
    for HarvestMan program and its related modules. This 
    module is part of the HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>

    For licensing information see the file LICENSE.txt that
    is included in this distribution.


    Jan 23 2007      Anand    Added code to check config in $HOME/.harvestman.
                              Added control-var for session saving feature.
    Feb 8 2007       Anand    Added config support for loading plugins. Added
                              code for swish-e plugin.

    Feb 11 2007      Anand    Re-wrote configuration parsing using generic option
                              parser.

    Mar 03 2007      Anand    Removed old option parsing dictionary and some
                              obsolete code. Added option for changing time gap
                              between downloads in config file. Removed command
                              line option for urllistfile/urltree file. Added
                              option to read multiple start URLs from a file.
                              Modified behaviour so that if a source of URL is
                              specified (command-line, URL file etc), any URLs
                              in config file is skipped. Set urlserver option
                              as default.
   Mar 06 2007       Anand    Reset default option to queue.
   April 11 2007     Anand    Renamed xmlparser module to configparser.
   April 20 2007     Anand    Added options for hget.
   May 7 2007       Anand     Modified option parsing for plugin option.
   Jun 2 2008       Anand     Fixed kludgy processing of <project> options
                              by using a function set_project. Added method
                              'add' for easy adding of project URLs in
                              interactive/programmatic crawling.
   
   Copyright (C) 2004 Anand B Pillai.                              

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

USAGE1 = """\
 %(program)s [options] [optional URL]
 
%(appname)s %(version)s %(maturity)s: An extensible, multithreaded web crawler.
Author: Anand B Pillai

Mail bug reports and suggestions to <abpillai at gmail dot com>."""

USAGE2 = """\
 %(program)s [options] URL(s) | file(s)
 
%(appname)s %(version)s %(maturity)s: A multithreaded web downloader based on HarvestMan.
Author: Anand B Pillai

The program accepts URL(s) or an input file(s) containing a number of URLs,
one per line. If a file is passed as input, any other program option
passed is applied for every URL downloaded using the file.

Mail bug reports and suggestions to <abpillai at gmail dot com>."""

import os, sys
import re
import configparser
import options
import urlparser

from common.optionparser import *
from common.macros import *
from common.common import hexit, test_sgmlop, logconsole, objects
from common.singleton import Singleton
from common.progress import TextProgress

CONFIG_XML_TEMPLATE="""\
<?xml version="1.0" encoding="utf-8"?>

<HarvestMan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://harvestmanontheweb.com/schemas/HarvestMan.xsd">
            
   <config version="3.0" xmlversion="1.0">
            %(@PROJECTS_ELEMENT)s
     <network>
      <proxy>
        <proxyserver>%(proxy)s</proxyserver>
        <proxyuser>%(puser)s</proxyuser>
        <proxypasswd>%(ppasswd)s</proxypasswd>
        <proxyport value="%(proxyport)s" />
      </proxy>
    </network>
    
    <download>
      <types>
        <html value="%(html)s" />
        <images value="%(images)s" />
        <movies value="%(movies)s" />
        <sounds value="%(sounds)s" />
        <documents value="%(documents)s" />        
        <javascript value="%(javascript)s" />
        <javaapplet value="%(javaapplet)s" />
        <querylinks value="%(getquerylinks)s" />
      </types> 
      <cache status="%(pagecache)s">
        <datacache value="%(datacache)s" />
      </cache>
      <protocol>
        <http compress="%(httpcompress)s" />
      </protocol>
      <misc>
        <retries value="%(retryfailed)s" />
      </misc>
    </download>
    
    <control>
      <links>
        <imagelinks value="%(getimagelinks)s" />
        <stylesheetlinks value="%(getstylesheets)s" />
        <offset start="%(linksoffsetstart)s" end="%(linksoffsetend)s" />
      </links>
      <extent>
        <fetchlevel value="%(fetchlevel)s" />
        <depth value="%(depth)s" />
        <extdepth value="%(extdepth)s" />
        <subdomain value="%(subdomain)s" />
        <ignoretlds value="%(ignoretlds)s" />
      </extent>
      <limits>
        <maxextservers value="%(maxextservers)s"/>
        <maxextdirs value="%(maxextdirs)s" />
        <maxfiles value="%(maxfiles)s" />
        <maxfilesize value="%(maxfilesize)s" />
        <maxbytes value="%(maxbytes)s" />
        <connections value="%(connections)s" />
        <maxbandwidth value="%(bandwidthlimit)s" factor="%(throttlefactor)s" />
        <timelimit value="%(timelimit)s" />
      </limits>
      <rules>
        <robots value="%(robots)s" />
        <urlpriority>%(urlpriority)s</urlpriority>
        <serverpriority>%(serverpriority)s</serverpriority>
      </rules>
      <filters>
        <urlfilter>%(urlfilter)s</urlfilter>
        <serverfilter>%(serverfilter)s</serverfilter>
        <wordfilter>%(wordfilter)s</wordfilter>
        <junkfilter value="%(junkfilter)s" />
      </filters>
      <plugins>
        <plugin name="swish-e" enable="0" />
        <plugin name="simulator" enable="0" />
        <plugin name="lucene" enable="0" />
        <plugin name="userbrowse" enable="0" />
        <plugin name="spam" enable="0" />
        <plugin name="datafilter" enable="0" />        
      </plugins>
    </control>

    <parser>
      <feature name='a' enable='1' />
      <feature name='base' enable='1' />
      <feature name='frame' enable='1' />
      <feature name='img' enable='1' />
      <feature name='form' enable='1' />
      <feature name='link' enable='1' />
      <feature name='body' enable='1' />
      <feature name='script' enable='1' />
      <feature name='applet' enable='1' />
      <feature name='area' enable='1' />
      <feature name='meta' enable='1' />
      <feature name='embed' enable='1' />
      <feature name='object' enable='1' />
      <feature name='option' enable='0' />
    </parser>
      
    <system>
      <workers status="%(usethreads)s" size="%(threadpoolsize)s" timeout="%(timeout)s" />
      <trackers value="%(maxtrackers)s" timeout="%(fetchertimeout)s" />
      <timegap value="%(sleeptime)s" random="%(randomsleep)s" />
    </system>
    
    <files>
      <urltreefile status="%(urltreefile)s" />
      <archive status="%(archive)s" format="%(archformat)s" />
      <urlheaders status="%(urlheaders)s" />
      <localise value="%(localise)s" />
    </files>
    
    <display>
      <browsepage value="%(browsepage)s"/>
    </display>
    
  </config>
  
</HarvestMan>
"""

param_re = re.compile(r'\S+=\S+',re.LOCALE|re.UNICODE)
int_re = re.compile(r'\d+')
float_re = re.compile(r'\d+\.\d*')
maxbytes_re = re.compile(r'(\d+\s*)(kb?|mb?|gb?)?$', re.IGNORECASE)
maxbw_re = re.compile(r'(\d+\s*)(k(b|bps)?|m(b|bps)?|g(b|bps)?)?$', re.IGNORECASE)

# This will contain the absolute path of parent-folder of
# harvestman installation...

module_path = ''

class HarvestManStateObject(dict, Singleton):
    """ Configuration class for HarvestMan framework and applications
    derived from it. A single instance of this class keeps most of the
    shared state and configuration params of HarvestMan """

    klassmap = {}
    alias = 'config'
    
    def __init__(self):
        """ Initialize dictionary with the most common settings and their values """

        # Calculate the module path
        mydir = os.path.dirname(globals()["__file__"])
        global module_path
        module_path = os.path.dirname(mydir)
            
        self._init1()
        self._init2()
        self.set_system_params()
        self.set_user_params()
        super(HarvestManStateObject, self).__init__()
        
    def _init1(self):
        """ First level initialization method. Initializes most of the state variables """
        
        self.items_to_skip=[]
        # USER-AGENT string
        self.USER_AGENT = ''
        # Version for harvestman
        self.version='2.0'
        # Maturity for harvestman
        self.maturity="alpha 1"
        # Single appname property for hget/harvestman
        self.appname='HarvestMan'
        self.progname="".join((self.appname," ",self.version," ",self.maturity))
        self.program = sys.argv[0]
        self.url=''
        self.project=''
        self.project_ignore = 0
        self.basedir=''
        # A list which will hold dicts of (url, name, basedir, verbosity) for all projects
        self.projects = []
        self.urlmap = {}
        self.archive = 0
        self.archformat = 'bzip'
        self.urlheaders = 1
        self.configfile = 'config.xml'
        self.projectfile = ''         
        self.proxy=''
        self.puser=''
        self.ppasswd=''
        self.proxyenc=1
        self.username=''   
        self.passwd=''     
        self.proxyport=80
        self.errorfile='errors.log'
        self.localise=2
        self.images=1
        self.movies=0
        self.sounds=0
        self.documents=1
        self.depth=10
        self.html=1
        self.robots=1
        self.eserverlinks=0
        self.epagelinks=1
        self.fastmode=1
        self.usethreads=1
        self.maxfiles=5000
        self.maxbytes=0
        self.maxextservers=0
        self.maxextdirs=0
        self.retryfailed=1
        self.extdepth=0
        self.maxtrackers=4
        self.urlfilter=''
        self.wordfilter=''
        self.inclfilter=[]
        self.exclfilter=[]
        self.allfilters=[]
        self.serverfilter=''
        self.serverinclfilter=[]
        self.serverexclfilter=[]
        self.allserverfilters=[]
        self.urlpriority = ''
        self.serverpriority = ''
        self.urlprioritydict = {}
        self.serverprioritydict = {}
        self.verbosity=2
        self.verbosity_default=2
        # timeout for worker threads is a rather
        # large 5 minutes.
        self.timeout=300.00
        # timeout for sockets is a rather high 1.0 minute
        self.socktimeout = 60.0
        # Time out for fetchers is a rather small 4 minutes
        self.fetchertimeout = 240.0
        self.getimagelinks=1
        self.getstylesheets=1
        # Load images from anywhere irrepsective of rules
        self.anyimages=1
        self.threadpoolsize=10
        self.renamefiles=0
        self.fetchlevel=0
        self.browsepage=0
        self.checkfiles=1
        self.pagecache=1
        # Internal variable telling whether to write cache
        self.writecache=True
        self.cachefound=0
        self._error=''
        self.starttime=0
        self.endtime=0
        self.javascript = 1
        self.javaapplet = 1
        self.connections=5
        # Bandwidth limit, 0 means no limit
        self.bandwidthlimit = 0
        self.throttlefactor = 1.5
        self.cachefileformat='pickled' 
        self.testing = 0
        self.testnocrawl = 0
        self.nocrawl = 0
        self.ignoreinterrupts = 0
        # Set to true when a kb interrupt is caught
        self.keyboardinterrupt = 0
        # Differentiate between sub-domains of a domain ?
        # When set to True, subdomains act like different
        # domains, so they are filtered out for fetchlevel<=1
        self.subdomain = 1
        # Flag to ignore tlds, if set to True, domains
        # such as www.foo.com, www.foo.co.uk, www.foo.org
        # will all evaluate to the same server.
        # Use this carefully!
        self.ignoretlds = 0
        self.getquerylinks = 0
        self.bytes = 20.00 # Not used!
        self.projtimeout = 1800.00
        self.downloadtime = 0.0
        self.timelimit = -1
        self.terminate = 0
        self.datacache = 0
        self.blocking = 0
        self.junkfilter = 1
        self.junkfilterdomains = 1
        self.junkfilterpatterns = 1
        self.urltreefile = 0
        self.urlfile = ''
        self.maxfilesize=5242880
        self.minfilesize=0
        self.format = 'xml'
        self.rawsave = 0
        self.fromprojfile = 0
        # HTML features (optional)
        self.htmlfeatures = []
        # For running from previous states.
        self.resuming = 0
        self.runfile = None
        # Control var for session-saver feature.
        self.savesessions = 0
        # List of enabled plugins
        self.plugins = []
        # Control var for simulation feature
        self.simulate = 0
        # Time to sleep between requests
        self.sleeptime = 1.0
        # Time to sleep on the request queue
        self.queuetime = 1.0
        # Queue size - fixed...
        self.queuesize = 5000
        self.randomsleep = 1
        # For http compression
        self.httpcompress = 1
        # Type of URLs which can be
        # set to skip any rules we define
        # This is not a user configurable
        # option, but can be configured in
        # plugins, of course.
        self.skipruletypes = []
        # Number of parts to split a file
        # to, for multipart http downloads
        self.numparts = 4
        # Flag to force multipart downloads off
        self.nomultipart = 0
        # Flag to indicate that a multipart
        # download is in progress
        self.multipart = 0
        # Links offset start - this will
        # skip the list of child links of a URL
        # to the given value
        self.linksoffsetstart = 0
        # Links offset value - this will skip
        # the list of child links of a URL
        # after the given value
        self.linksoffsetend = -1
        # Cache size for 
        # Current progress object
        self.progressobj = TextProgress()
        # Flag for forcing multipart downloads
        self.forcesplit = 0
        # Data save mode for connectors
        # Is in-mem by default
        self.datamode = CONNECTOR_DATA_MODE_INMEM
        # Hget outfile - default empty string
        self.hgetoutfile = ''
        # Hget output directory - default current directory
        self.hgetoutdir = '.'
        # Hget verbosity flag - default False
        self.hgetverbose = 0
        # Hget temp flag - default False
        self.hgetnotemp = 0
        # Hget mirror file
        self.mirrorfile = ''
        # Hget mirror search flag
        self.mirrorsearch = False
        # Hget mirror relpath index
        self.mirrorpathindex = 0
        # Hget relpath use flag
        self.mirroruserelpath = 1
        # Hget resume mode
        self.canresume = 1
        # Internal state param
        self._badrequests = 0
        # Internal config param
        self._connaddua = True
        
    def _init2(self):
        """ Second level initialization method. Initializes the dictionary which maps
        configuration XML file entries to state variables """
        
        # For mapping xml entities to config entities
        
        self.xml_map = { 'project_ignore' : ('project_ignore', 'int'),
                         'url' : ('url', 'func:set_project'),
                         'name': ('project', 'func:set_project'),
                         'basedir' : ('basedir', 'func:set_project'),
                         'verbosity_value' : ('verbosity', 'func:set_project'),

                         'proxyserver': ('proxy','str'),
                         'proxyuser': ('puser','str'),
                         'proxypasswd' : ('ppasswd','str'),
                         'proxyport_value' : ('proxyport','int'),

                         'username': ('username','str'),
                         'passwd' : ('passwd','str'),
                         
                         'urlhost' : ('urlhost','str'),
                         'urlport_value' : ('urlport','int'),

                         'html_value' : ('html','int'),
                         'images_value' : ('images','int'),
                         'movies_value' : ('movies','int'),
                         'sounds_value' : ('sounds','int'),
                         'documents_value' : ('documents','int'),                         
                         
                         'javascript_value' : ('javascript','int'),
                         'javaapplet_value' : ('javaapplet','int'),
                         'querylinks_value' : ('getquerylinks','int'),

                         'cache_status' : ('pagecache','int'),
                         'datacache_value' : ('datacache','int'),

                         'urllist': ('urlfile', 'str'),
                         'urltreefile_status' : ('urltreefile', 'int'),
                         'archive_status' : ('archive', 'int'),
                         'archive_format' : ('archformat', 'str'),
                         'urlheaders_status' : ('urlheaders', 'int'),
                         'retries_value': ('retryfailed','int'),
                         'imagelinks_value' : ('getimagelinks','int'),
                         'stylesheetlinks_value' : ('getstylesheets','int'),
                         'offset_start' : ('linksoffsetstart','int'),
                         'offset_end' : ('linksoffsetend','int'),
                         'fetchlevel_value' : ('fetchlevel','int'),
                         'extserverlinks_value' : ('eserverlinks','int'),
                         'extpagelinks_value' : ('epagelinks','int'),
                         'depth_value' : ('depth','int'),
                         'extdepth_value' : ('extdepth','int'),
                         'subdomain_value' : ('subdomain','int'),
                         'ignoretlds_value': ('ignoretlds','int'),
                         'maxextservers_value' : ('maxextservers','int'),
                         'maxextdirs_value' : ('maxextdirs','int'),
                         'maxfiles_value' : ('maxfiles','int'),
                         'maxfilesize_value' : ('maxfilesize','int'),
                         'maxbytes_value' : ('maxbytes', 'func:set_maxbytes'),
                         'connections_value' : ('connections','int'),
                         'maxbandwidth_value' : ('bandwidthlimit','func:set_maxbandwidth'),
                         'maxbandwidth_factor': ('throttlefactor','float'),
                         'robots_value' : ('robots','int'),
                         'timelimit_value' : ('timelimit','float'),
                         'urlpriority' : ('urlpriority','str'),
                         'serverpriority' : ('serverpriority','str'),
                         'urlfilter': ('urlfilter','str'),
                         'serverfilter' : ('serverfilter','str'),
                         'wordfilter' : ('wordfilter','str'),
                         'junkfilter_value' : ('junkfilter','int'),
                         'useragent_value': ('USER_AGENT','str'),
                         'workers_status' : ('usethreads','int'),
                         'workers_size' : ('threadpoolsize','int'),
                         'workers_timeout' : ('timeout','float'),
                         'trackers_value' : ('maxtrackers','int'),
                         'trackers_timeout' : ('fetchertimeout','float'),                         
                         'fastmode_value': ('fastmode','int'),
                         'savesessions_value': ('savesessions','int'),
                         'timegap_value': ('sleeptime', 'float'),
                         'timegap_random': ('randomsleep', 'int'),
                         'feature_name' : ('htmlfeatures', 'func:set_parse_features'),
                         'simulate_value': ('simulate', 'int'),
                         'localise_value' : ('localise','int'),
                         'browsepage_value' : ('browsepage','int'),

                         'configfile_value': ('configfile', 'str'),
                         'projectfile_value': ('projectfile', 'str'),

                         'urlfilterre_value': (('inclfilter', 'list'),
                                               ('exclfilter', 'list'),
                                               ('allfilters', 'list')),
                         'serverfilterre_value':(('serverinclfilter', 'list'),
                                                 ('serverexclfilter', 'list'),
                                                 ('allserverfilters', 'list')),
                         'urlprioritydict_value': ('urlprioritydict', 'dict'),
                         'serverprioritydict_value': ('serverprioritydict', 'dict'),
                         'http_compress' : ('httpcompress', 'int'),
                         'plugin_name': ('plugins','func:set_plugin')
                         }

    def copy(self):
        """ Return a serializable copy of this instance """
        
        # Set non-picklable objects to None type
        self.progressobj = None
        return self

    def __getstate__(self):
        """ Overloaded __getstate__ method """
        return self

    def __setstate__(self, state):
        """ Overloaded __setstate__ method """
        pass
    

    def assign_option(self, option_val, value, kwargs={}):
        """ Assigns values to internal variables using the option specified """

        # Currently this is used only to parse
        # xml config files.
        if len(option_val) == 2:
            key, typ = option_val
            # If type is not a list, the
            # action is simple assignment

            # Bug fix: If someone has set the
            # value to 'True'/'False' instead of
            # 1/0, convert to bool type first.
            
            if type(value) in (str, unicode):
                if value.lower() == 'true':
                    value = 1
                elif value.lower() == 'false':
                    value = 0

            if typ.find(':') == -1:
                # do any type casting of the option
                fval = (eval(typ))(value)
                self[key] = fval
                
                # If type is list, the action is
                # appending, after doing any type
                # casting of the actual value
            else:
                # Type is of the form <type>:<actual type>
                typname, typ = typ.split(':')
                # print 'typename',typname
                
                if typname == 'list':
                    if typ:
                        fval = (eval(typ))(value)
                    else:
                        fval = value
                        
                    var = self[key]
                    var.append(fval)
                elif typname == 'func':
                    funktion = getattr(self, typ)
                    if funktion:
                        funktion(key, value, kwargs)
        else:
            debug('Error in option value %s!' % option_val)

    def set_option(self, option, value, negate=0):
        """ Sets the passed option in with its value as the passed value """
        
        # find out if the option exists in the dictionary
        if option in self.xml_map.keys():
            # if the option is a string or int or any
            # non-seq type

            # if value is an emptry string, return error
            if value=="": return CONFIG_VALUE_EMPTY

            # Bug fix: If someone has set the
            # value to 'True'/'False' instead of
            # 1/0, convert to bool type first.
            if type(value) in (str, unicode):
                if value.lower() == 'true':
                    value = 1
                elif value.lower() == 'false':
                    value = 0
            
            if type(value) is not tuple:
                # get the key for the option
                key = (self.xml_map[option])[0]
                # get the type of the option
                typ = (self.xml_map[option])[1]
                # do any type casting of the option
                fval = (eval(typ))(value)
                # do any negation of the option
                if type(fval) in (int,bool):
                    if negate: fval = not fval
                # set the option on the dictionary
                self[key] = fval
                
                return CONFIG_OPTION_SET
            else:
                # option is a tuple of values
                # iterate through all values of the option
                # see if the size of the value tuple and the
                # size of the values for this key match
                _values = self.xml_map[option]
                if len(_values) != len(value): return CONFIG_VALUE_MISMATCH

                for index in range(0, len(_values)):
                    _v = _values[index]
                    if len(_v) !=2: continue
                    _key, _type = _v

                    v = value[index]
                    # do any type casting on the option's value
                    fval = (eval(_type))(v)
                    # do any negation
                    if type(fval) in (int,bool):                    
                        if negate: fval = not fval
                    # set the option on the dictionary
                    self[_key] = fval

                return CONFIG_OPTION_SET

        return CONFIG_OPTION_NOT_SET

    def set_option_xml_attr(self, option, value, attrs):
        """ Sets an option from the XML config file for an XML attribute """

        # If option in things to be skipped, return
        if option in self.items_to_skip:
            return CONFIG_ITEM_SKIPPED
        
        option_val = self.xml_map.get(option, None)
        
        if option_val:
            try:
                if type(option_val) is tuple:
                    self.assign_option(option_val, value, attrs)
                elif type(option_val) is list:
                    # If the option_val is a list, there
                    # might be multiple vars to set.
                    for item in option_val:
                        # The item has to be a tuple again...
                        if type(item) is tuple:
                            # Set it
                            self.assign_option(item, value, attrs)
            except Exception, e:
                print 'Error assigning option \"',option,'\"', e
                if e.__class__==ValueError:
                    print '(Perhaps you invoked the wrong argument ?)'
                print 'Pass option -h for command line usage.'                    
                hexit(e)
        else:
            return CONFIG_OPTION_NOT_DEFINED

        return CONFIG_OPTION_SET

    def set_option_xml(self, option, value):
        """ Set an option from the XML config file from an XML element """

        # If option in things to be skipped, return
        if option in self.items_to_skip:
            return CONFIG_ITEM_SKIPPED
        
        option_val = self.xml_map.get(option, None)
        
        if option_val:
            try:
                if type(option_val) is tuple:
                    self.assign_option(option_val, value)
                elif type(option_val) is list:
                    # If the option_val is a list, there
                    # might be multiple vars to set.
                    for item in option_val:
                        # The item has to be a tuple again...
                        if type(item) is tuple:
                            # Set it
                            self.assign_option(item, value)
            except Exception, e:
                print 'Error assigning option \"',option,'\"'
                # If this is a ValueError, mostly the wrong argument was passed
                if e.__class__==ValueError:
                    print '(Perhaps you invoked the wrong argument ?)'
                print 'Pass option -h for command line usage.'
                hexit(1)
        else:
            return CONFIG_OPTION_NOT_DEFINED

        return CONFIG_OPTION_SET        

    def set_maxbytes(self, key, val, attrdict):

        # The value could be in any of the following forms
        # <maxbytes value="5000" /> - End crawl at 5000 bytes
        # <maxbytes value="10kb" /> - End crawl at 10kb 
        # <maxbytes value="50MB" /> - End crawl at 50 MB.
        # <maxbytes value="1GB" /> - End crawl at 1 GB.
        # <maxbytes value="10k" /> - End crawl at 10kb 
        # <maxbytes value="50M" /> - End crawl at 50 MB.
        # <maxbytes value="1G" /> - End crawl at 1 GB.        
        # Any extra spaces should also be taken care of
        
        # The regexp does all the above
        items = maxbytes_re.findall(val.strip())
        if items:
            # 'item' is a pair
            item = items[0]
            # First member is the number, second the
            # specification for kb, mb, gb if any.
            limit, spec = item
            limit = int(limit)
            
            if spec != '':
                # Check for kb, mb, gb
                spec = spec.strip().lower()
                if spec.startswith('k'):
                    limit *= 1024
                elif spec.startswith('m'):
                    limit *= pow(1024, 2)
                elif spec.startswith('g'):
                    limit *= pow(1024, 3)

            # Set maxbytes
            self.maxbytes = limit

    def set_maxbandwidth(self, key, val, attrdict):

        # The value could be in any of the following forms
        # <maxbandwidth value="5" /> - Crawl at 5 bytes per sec 
        # <maxbandwidth value="5 k" /> - Crawl at 5 kbps
        # <maxbandwidth value="5 kb" /> - Crawl at 5 kbps
        # <maxbandwidth value="5 kbps" /> - Crawl at 5 kbps        
        # <maxbandwidth value="5 m" /> - Crawl at 5 mbps
        # <maxbandwidth value="5 mb" /> - Crawl at 5 mbps
        # <maxbandwidth value="5 mbps" /> - Crawl at 5 mbps        
        # Any extra spaces should also be taken care of
        
        # The regexp does all the above
        items = maxbw_re.findall(val.strip())
        if items:
            item = items[0]
            # First member is the number, second the
            # specification for kb, mb, gb if any.
            limit = int(item[0])
            spec = item[1]
            
            if spec != '':
                # Check for kb, mb, gb, kbps, mbps, gbps
                spec = spec.strip().lower()
                if spec.startswith('k'):
                    limit *= 1024
                elif spec.startswith('m'):
                    limit *= pow(1024, 2)
                elif spec.startswith('g'):
                    limit *= pow(1024, 3)

            # Set maxbandwidth
            self.bandwidthlimit = float(limit)
                    
    def set_project(self, key, val, prjdict):
        # Same function is called for url, basedir, name
        # and verbosity

        # If project is to be ignored, skip this
        if self.project_ignore:
            return
        
        new_entry, recent = False, {}
        sz = len(self.projects)
        if sz==0:
            new_entry = True
        else:
            item = self.projects[-1]
            # If item is completed, new entry is True
            # else it is false
            if item.get('done',False):
                new_entry = True
            else:
                recent = item

                # Still check if this is beginning of a new entry
                # since we may not define all fields inside <project>...</project>
                if key in recent:
                    # Key already there, so treat this as a fresh entry
                    # and close current entry...
                    recent['done'] = True
                    self.projects[-1] = recent
                    recent = {}
                    new_entry = True
            
        if key in ('url','basedir','project'):
            recent[key] = val
        elif key=='verbosity':
            try:
                recent['verbosity'] = int(prjdict[u'value'])
            except KeyError:
                recent['verbosity'] = int(val)

        # If all items are present, put 'done' to True
        if len(recent)==4:
            recent['done'] = True

        # If new entry, then append, else set in position
        if new_entry:
            self.projects.append(recent)
        else:
            self.projects[-1] = recent

        # print self.projects
        
    def set_plugin(self, key, val, plugindict):
        """ Sets the state of the plugins param """

        plugin = plugindict['name']
        enable = int(plugindict['enable'])
        if enable: self.plugins.append(plugin)

    def set_parse_features(self, key, val, featuredict):
        """ Sets the state of the plugins param """

        feat = featuredict['name']
        enable = int(featuredict['enable'])
        self.htmlfeatures.append((feat, enable))
        
    def parse_arguments(self):
        """ Parses the command line arguments """

        # This function has 3 return values
        # CONFIG_INVALID_ARGUMENT => no cmd line arguments/invalid cmd line arguments
        # ,so force program to read config file.
        # PROJECT_FILE_EXISTS => existing project file supplied in cmd line
        # CONFIG_ARGUMENTS_OK => all options correctly read from cmd line

        # if no cmd line arguments, then use config file,
        # return -1
        if len(sys.argv)==1:
            return CONFIG_INVALID_ARGUMENT

        # Otherwise parse the arguments, the command line arguments
        # are the same as the variables(dictionary keys) of this class.
        # Description
        # Options needing no arguments
        #
        # -h => prints help
        # -v => prints version info
        
        args, optdict = '',{}
        try:
            if self.appname == 'HarvestMan':
                USAGE = USAGE1
            elif self.appname == 'Hget':
                USAGE = USAGE2
                
            gopt = GenericOptionParser(options.getOptList(self.appname), usage = USAGE % self )
            optdict, args = gopt.parse_arguments()
        except GenericOptionParserError, e:
            hexit('Error: ' + str(e))

        # print optdict
        
        cfgfile = False

        if self.appname == 'HarvestMan':
            for option, value in optdict.items():
                # If an option with value of null string, skip it
                if value=='':
                   # print 'Skipping option',option
                   continue
                else:
                   # print 'Processing option',option,'value',value
                   pass

                # first parse arguments with no options
                if option=='version' and value:
                    self.print_version_info()
                    sys.exit(0)                
                elif option=='configfile':
                    if SUCCESS(self.check_value(option,value)):
                        self.set_option_xml('configfile_value', self.process_value(value))
                        cfgfile = True
                        # Continue parsing and take rest of options from cmd line
                elif option=='projectfile':
                    if SUCCESS(self.check_value(option,value)):
                        self.set_option_xml('projectfile_value', self.process_value(value))
                        import utils 

                        projector = utils.HarvestManProjectManager()

                        if projector.read_project() == PROJECT_FILE_EXISTS:
                            # No need to parse further values
                            return PROJECT_FILE_EXISTS

                elif option=='basedir':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('basedir', self.process_value(value))
                elif option=='project':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('name', self.process_value(value))
                elif option=='retries':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('retries_value', self.process_value(value))
                elif option=='localise':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('localise_value', self.process_value(value))
                elif option=='fetchlevel':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('fetchlevel_value', self.process_value(value))
                elif option=='maxthreads':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('trackers_value', self.process_value(value))
                elif option=='maxfiles':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('maxfiles_value', self.process_value(value))
                elif option=='timelimit':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('timelimit_value', self.process_value(value))
                elif option=='workers':
                    self.set_option_xml('workers_status',1)
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('workers_size', self.process_value(value))                
                elif option=='urlfilter':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('urlfilter', self.process_value(value))
                elif option=='depth':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('depth_value', self.process_value(value))
                elif option=='robots':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('robots_value', self.process_value(value))
                elif option=='urllist':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('urllist', self.process_value(value))
                elif option=='proxy':
                    if SUCCESS(self.check_value(option,value)):
                        # Set proxyencrypted flat to False
                        self.proxyenc=False
                        self.set_option_xml('proxyserver', self.process_value(value))
                elif option=='proxyuser':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('proxyuser', self.process_value(value))                
                elif option=='proxypasswd':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('proxypasswd', self.process_value(value))
                elif option=='urlserver':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('urlserver_status', self.process_value(value))

                elif option=='cache':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('cache_status', self.process_value(value))
                elif option=='connections':
                    if SUCCESS(self.check_value(option,value)):
                        val = self.process_value(value)
                        if val>=self.connections:
                            self.connections = val + 1
                elif option=='verbosity':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('verbosity_value', self.process_value(value))
                elif option=='subdomain':
                    if value: self.set_option_xml('subdomain_value', 0)                    
                #elif option=='savesessions':
                #    if SUCCESS(self.check_value(option,value)): self.set_option_xml('savesessions_value', self.process_value(value))
                elif option=='simulate':
                    self.set_option_xml('simulate_value', value)
                elif option=='plugins':
                    # Plugin is specified as plugin1+plugin2+...
                    plugins = value.split('+')
                    # Remove any duplicate occurence of same plugin
                    self.plugins = list(set([plugin.strip() for plugin in plugins]))
                    # Don't allow reading plugin from config file now
                    self.items_to_skip.append('plugin_name')
                elif option=='option':
                    # Value should be of the form param=value
                    if not param_re.match(value):
                        print 'Error in option value, should be of the form <param>=<value>'
                    else:
                        param,val=value.strip().split('=')
                        if param in self:
                            # Guess type of param
                            # Could be a tuple, dict or list value ?
                            if (val.startswith('(') and val.endswith(')')) or \
                               (val.startswith('[') and val.endswith(']')) or \
                               (val.startswith('{') and val.endswith('}')):

                                # Try tupling
                                try:
                                    val = eval(val)
                                except Exception:
                                    pass
                            else:
                                # Try float next
                                if float_re.match(val):
                                    val = float(val)
                                # Try int next
                                elif int_re.match(val):
                                    val = int(val)
                                else:
                                    # Plain string
                                    pass
                                
                            self[param]=val
                elif option == 'ui' and value:
                    # Start the web UI
                    import gui
                    gui.run()
                elif option == 'selftest' and value:
                    # Run the unit-tests as self-tests
                    print 'Running self-test...'
                    sys.path.append(os.path.join(module_path, 'test'))
                    import run_tests
                    
                    result = run_tests.run_all_tests()
                    print result
                    if result.wasSuccessful():
                        print 'self-test complete. All tests passed.'
                        sys.exit(0)
                    else:
                        print 'self-test failed. Please check your installation!'
                        sys.exit(1)

        elif self.appname == 'Hget':
            # Hget options
            for option, value in optdict.items():
                # If an option with value of null string, skip it
                if value=='':
                   # print 'Skipping option',option
                   continue
                else:
                   # print 'Processing option',option,'value',value
                   pass

                # first parse arguments with no options
                if option=='version' and value:
                    self.print_version_info()
                    sys.exit(0)                               
                elif option=='numparts':
                    # Setting numparts forces split downloads
                    self.numparts = abs(int(value))
                    if self.numparts == 0:
                        print 'Error: Invalid value for number of parts, value should be non-zero!'
                        sys.exit(1)
                    if self.numparts>1:
                        self.forcesplit = True
                        # If we are forcesplitting with parts>1, then disable resume automatically
                        print 'Force-split switched on, resuming will be disabled'
                        self.canresume = False
                    else:
                        print 'Warning: Setting numparts to 1 has no effect!'
                elif option=='memory':
                    if value:
                        print 'Warning: Enabling in-memory flag, data will be stored in memory!'
                        self.datamode = CONNECTOR_DATA_MODE_INMEM
                elif option=='notempdir':
                    if value:
                        print 'Temporary files will be saved to current directory'
                        # Do not use temporary directory for saving intermediate files
                        self.hgetnotemp = True
                elif option=='output':
                    self.hgetoutfile = value
                elif option=='outputdir':
                    self.hgetoutdir = value
                elif option=='verbose':
                    self.hgetverbose = value
                elif option=='proxy':
                    if SUCCESS(self.check_value(option,value)):
                        # Set proxyencrypted flat to False
                        self.proxyenc=False
                        self.set_option_xml('proxyserver', self.process_value(value))
                elif option=='proxyuser':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('proxyuser', self.process_value(value))
                elif option=='proxypasswd':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('proxypasswd', self.process_value(value))
                elif option=='passwd':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('passwd', self.process_value(value))
                elif option=='username':
                    if SUCCESS(self.check_value(option,value)): self.set_option_xml('username', self.process_value(value))
                elif option == 'single':
                    if value:
                        print "Single thread option set, disabling multipart downloads..."
                        self.nomultipart = True
                elif option == 'mirrorfile':
                    filename = value.strip()
                    if os.path.isfile(filename):
                        print 'Mirrors will be loaded from %s...' % filename
                        self.mirrorfile = filename
                    else:
                        print  'Warning: Mirror file %s not found!' % filename
                elif option == 'mirrorsearch':
                    if value:
                        print  'Mirror search turned on'
                        self.mirrorsearch = True
                elif option == 'relpathidx':
                    idx = int(value.strip())
                    self.mirrorpathindex = idx
                elif option == 'norelpath':
                    if value:
                        print 'Using filename only to construct mirror URLs...'
                        self.mirroruserelpath = False
                elif option == 'resumeoff':
                    if value:
                        print 'Resume mode set to off, partial downloads will not be resumed!'
                        self.canresume = False

            # If both mirror search and mirror file specified, mirror file is used
            # Print some information regarding mismatch of options...
            if self.mirrorfile and self.mirrorsearch:
                print 'Both mirror search and mirror file option given, mirror search will not be done'
                self.mirrorsearch = False
            if self.mirrorpathindex and not self.mirrorfile:
                print 'Ignoring mirror path index param because no mirror file is loaded'
            if not self.mirroruserelpath and not self.mirrorfile:
                print 'Ignoring relpath flag because no mirror file is loaded'
                
                    
        # print self.subdomain
        if self.nocrawl:
            self.pagecache = False
            self.rawsave = True
            self.localise = 0
            # Set project name to ''
            self.set_option_xml('name','')
            # Set basedir to dot
            self.set_option_xml('basedir','.')
        
        if args:
            # Any option without an argument is assumed to be a URL
            for arg in args:
                self.set_option_xml('url',self.process_value(arg))
                
            # Since we set a URL from outside, we dont want to read
            # URLs from the config file - same for plugins
            self.items_to_skip = ['url','name','basedir','verbosity_value']

        # If urlfile option set, read all URLs from a file
        # and load them.
        if self.urlfile:
            if not os.path.isfile(self.urlfile):
                print 'Error: Cannot find URL file %s!' % self.urlfile
                return CONFIG_INVALID_ARGUMENT
            
            # Open file
            try:
                lines = open(self.urlfile).readlines()
                if len(lines):
                    # Reset all...
                    self.projects = []

                    for line in lines:
                        url = line.strip()
                        # Fix URL protocol string
                        url = self._fix_url_protocol(url)
                        try:
                            # Create project name
                            h = urlparser.HarvestManUrl(url)
                            project = h.get_domain()
                            self.projects.append({'url': url,
                                                  'project': project,
                                                  'basedir': '.',
                                                  'verbosity': 2})
                        except urlparser.HarvestManUrlError, e:
                            continue

                    # We would now want to skip url, project,
                    # basedir etc in the config file
                    self.items_to_skip = ['url','name','basedir','verbosity_value']

            except Exception, e:
                print e
                return CONFIG_INVALID_ARGUMENT


        # Error in option value
        if self._error:
            print self._error, value
            return CONFIG_INVALID_ARGUMENT

        # If need to pass config file return CONFIG_INVALID_ARGUMENT
        if cfgfile:
            return CONFIG_INVALID_ARGUMENT
        
        return CONFIG_ARGUMENTS_OK

    def check_value(self, option, value):
        """ This function checks the values for options when options
        are supplied as command line arguments. Returns 0 on any error
        and non-zero otherwise """

        # check #1: If value is a null, return 0
        if not value:
            self._error='Error in option value for option %s, value should not be empty!' % option
            return CONFIG_ARGUMENT_ERROR

        # no other checks right now
        return CONFIG_ARGUMENT_OK

    def process_value(self, value):
        """ This function maps values of command line arguments to values
        which can be used to assign to config params """

        # a 'yes' is treated as 1 and 'no' as 0
        # also an 'on' is treated as 1 and 'off' as 0
        # Other valid values: integers, strings, 'YES'/'NO'
        # 'OFF'/'ON'

        ret = OPTION_TURN_OFF
        # We expect the null check has been done before
        val = value.lower()
        if val in ('yes', 'on'):
            return OPTION_TURN_ON
        elif val in ('no', 'off'):
            return OPTION_TURN_OFF

        # convert value to int
        try:
            ret=int(val)
            return ret
        except:
            pass

        # return string value directly
        return str(value)

    def print_help(self):
        """ Prints the command-line usage information """

        print PROG_HELP % {'appname' : self.appname,
                           'version' : self.version,
                           'maturity' : self.maturity }

    def print_version_info(self):
        """ Prints version information about the program """

        print 'Version: %s %s' % (self.version, self.maturity)

    def _fix_url_protocol(self, url):
        """ Fixes errors in URL protocol string, if any """
        
        r = re.compile('www\d?\.|http://|https://|ftp://|file://',re.IGNORECASE)
        if not r.match(url):
            # Assume http url
            # prepend http:// to it
            # We prepend http:// to even FTP urls so that
            # the ftp servers can be crawled.
            url = 'http://' + url

        return url

    def add(self, url, name='', basedir='.', verbosity=2):
        """ Adds a crawl project to the crawler. The arguments
        are the starting URL, and optional name for the project,
        a base directory for saving files and project verbosity """

        # Useful for command-line crawling
        self.projects.append({'url': url,
                              'project': name,
                              'basedir': basedir,
                              'verbosity': verbosity})
        
    def setup(self):
        """ Sets up the configuration object for full use,
        after fixing any errors in key config variables such as
        URL, project directory, project names etc """

        # If there is more than one url, we
        # combine all the project related
        # variables into a dictionary for easy
        # lookup.
        
        num=len(self.projects)
        if num==0:
            msg = 'Fatal Error: No URLs given, Aborting.\nFor command-line options run with -h option'
            sys.exit(msg)

        # Fix url error
        for x in range(len(self.projects)):
            entry = self.projects[x]
            url = entry['url']
            
            # If null url, return
            if not url: continue

            # Fix protocol strings
            url = self._fix_url_protocol(url)
            entry['url'] = url
            
            # If project is not set, set it to domain
            # name of the url.
            if entry.get('project','')=='':
                h = urlparser.HarvestManUrl(url)
                project = h.get_domain()
                entry['project'] = project

            if entry.get('basedir','')=='':
                entry['basedir'] = '.'

            if entry.get('verbosity',0)==0:
                entry['verbosity'] = 2

        self.plugins = list(set(self.plugins))
            
        if 'swish-e' in self.plugins:
            # Disable any message output for swish-e
            self.verbosity = 0
            # Set verbosity to zero for all projects
            for entry in self.projects:
                entry['verbosity'] = 0

        objects.logger.setLogSeverity(self.verbosity)
                

    def set_system_params(self):
        """ Sets config file/directory parameters for all users """

        # Directory for system wide configuration files...
        if os.name == 'posix':
            self.etcdir = '/etc/harvestman'
        elif os.name == 'nt':
            self.etcdir = os.path.join(os.environ.get("ALLUSERSPROFILE"),
                                       "Application Data", "HarvestMan", "conf")
                
    def set_user_params(self):
        """ Set config file/directory parameters specific to the current user  """
        
        if os.name == 'posix':
            homedir = os.environ.get('HOME')
            if homedir and os.path.isdir(homedir):
                harvestman_dir = os.path.join(homedir, '.harvestman')
                
        elif os.name == 'nt':
            profiledir = os.environ.get('USERPROFILE')
            if profiledir and os.path.isdir(profiledir):
                harvestman_dir = os.path.join(profiledir, 'Local Settings', 'Application Data','HarvestMan')

        if harvestman_dir:
            harvestman_conf_dir = os.path.join(harvestman_dir, 'conf')
            harvestman_sessions_dir = os.path.join(harvestman_dir, 'sessions')
            harvestman_db_dir = os.path.join(harvestman_dir, 'db')

            self.userdir = harvestman_dir
            self.userconfdir = harvestman_conf_dir
            self.usersessiondir = harvestman_sessions_dir
            self.userdbdir = harvestman_db_dir
    
    def parse_config_file(self, configfile=None):
        """ Parses the configuration file. An optional configuration file can be
        passed to this method. Otherwise it tries to parse the default configuration
        file """

        if configfile:
            cfgfile = configfile
        else:
            cfgfile = self.configfile
            
        if not os.path.isfile(cfgfile):
            logconsole('Configuration file %s not found...' % cfgfile)
        else:
            logconsole('Using configuration file %s...' % cfgfile)
            
        return configparser.parse_xml_config_file(self, cfgfile)
        
    def get_program_options(self):
        """ Umbrella method for reading the program configuration
        from a configuration file or the command-line or both """

        # Now load system wide configuration file...
        system_conf_file = os.path.join(self.etcdir, "config.xml")
        if os.path.isfile(system_conf_file):
            logconsole("Loading system configuration...")
            configparser.parse_xml_config_file(self, system_conf_file)

        # Then load user configuration file
        user_conf_file = os.path.join(self.userconfdir, 'config.xml')
        if os.path.isfile(user_conf_file):
            logconsole("Loading user configuration...")
            configparser.parse_xml_config_file(self, user_conf_file)

        # first check in argument list, if failed
        # check in config file
        res = self.parse_arguments()

        if res == CONFIG_INVALID_ARGUMENT:
            self.parse_config_file()

        # fix errors in config variables
        self.setup()

    def enable_controller(self):
        """ Return whether we need to start the controller
        thread. This is determined by whether we have
        any limits either on time, files or data """

        return (self.timelimit != -1) or \
               (self.maxfiles) or \
               (self.maxbytes) or \
               (self.bandwidthlimit)
    
    def reset_progress(self):
        """ Rests the progress bar object (used by Hget)"""
        
        self.progressobj = None
        self.progressobj = TextProgress()
        
    def __getattr__(self, name):
        """Overloaded __getattr__ method """
        
        try:
            return self[intern(name)]
        except KeyError:
            return

    def __setattr__(self, name, value):
        """ Overloaded __setattr__ method """
        
        self[intern(name)] = value

    def set_klass_plugin_func(self, klassname, funcname, func):
        """ Sets the plugin function for the given HarvestMan class
        'klassname'. The plugin target function is specified by
        'funcname' and the plugin source function is 'func' """
        
        try:
            d = self.__class__.klassmap[klassname + '_plugins']
            d[funcname] = func
        except KeyError:
            self.__class__.klassmap[klassname + '_plugins'] = { funcname: func }            

    def get_klass_plugins(self, klassname):
        """ Return the plugin function dictionary for the HarvestMan class
        with the name 'klassname' """
        
        return self.__class__.klassmap.get(klassname + '_plugins')

    def set_klass_callback_func(self, klassname, funcname, func, where):
        """ Sets the callback function for the given HarvestMan class
        'klassname'. The callback target function is specified by
        'funcname' and the callback source function is 'func'. The
        last argument specifies whether to insert the callback before
        or after the target function """
        
        try:
            d = self.__class__.klassmap[klassname + '_callbacks']
            d[funcname] = (func, where)
        except KeyError:
            self.__class__.klassmap[klassname + '_callbacks'] = { funcname: (func, where) }            

    def get_klass_callbacks(self, klassname):
        """ Return the callbacks function dictionary for the HarvestMan class
        with the name 'klassname' """
        
        return self.__class__.klassmap.get(klassname + '_callbacks')    

    def generate_projects_xml(self):
        """ Generates and returns content for the <projects> config file XML element """

        content = "<projects>\n\n"
        for x in range(len(self.projects)):
            entry = self.projects[x]
            
            project = entry.get('project')
            url = entry.get('url')
            verb = entry.get('verbosity')
            basedir = entry.get('basedir')
            
            projcontent = '<project skip="0">\n'
            projcontent += '<url>' + url + '</url>\n'
            projcontent += '<name>' + project + '</name>\n'
            projcontent += '<basedir>' + basedir + '</basedir>\n'            
            projcontent += '<verbosity value="' + str(verb) + '"/>\n'
            projcontent += '</project>\n\n'

            content = content + projcontent

        content += "\n</projects>\n"

        return content

    def generate_current_configuration(self):
        """ Generates and returns the XML configuration string for the current configuration """

        projcontent = self.generate_projects_xml()
        self['@PROJECTS_ELEMENT'] = projcontent
        return CONFIG_XML_TEMPLATE % self

    def generate_system_configuration(self):
        """ Generates and returns configuration content for the system wide
        HarvestMan configuration file """

        self['@PROJECTS_ELEMENT'] = ''
        return CONFIG_XML_TEMPLATE % self

    def generate_user_configuration(self):
        """ Generates and returns configuration content for the user specific
        HarvestMan configuration file """

        return self.generate_system_configuration()

def set_aliases():

    import datamgr
    import rules
    import connector
    import urlqueue
    import event
    import logger
    from common.common import SetAlias
    
    SetAlias(HarvestManStateObject())
    SetAlias(logger.HarvestManLogger())

    # Data manager object
    dmgr = datamgr.HarvestManDataManager()
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
        

if __name__ == "__main__":
    s = HarvestManStateObject()
    print s.generate_system_configuration()
    
