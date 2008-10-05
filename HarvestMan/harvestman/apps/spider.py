#! /usr/bin/python

# -- coding: utf-8

""" HarvestMan - Extensible, modular, flexible, multithreaded Internet
    spider program using urllib2 and other python modules. This is
    the main module of HarvestMan.
    
    Version      - 2.0 alpha 1.

    Author: Anand B Pillai <abpillai at gmail dot com>

    HARVESTMAN is free software. See the file LICENSE.txt for information
    on the terms and conditions of usage, and a DISCLAIMER of ALL WARRANTIES.

 Modification History

    Created: Aug 2003

     Jan 23 2007          Anand      Changes to copy config file to ~/.harvestman/conf
                                     folder on POSIX systems. This file is also looked for
                                     if config.xml not found in curdir.
     Jan 25 2007          Anand      Simulation feature added. Also modified config.py
                                     to allow reading cmd line arguments when passing
                                     a config file using -C option.
     Feb 7 2007          Anand       Finished implementation of plugin feature. Crawl
                                     simulator is now a plugin.
     Feb 8 2007          Anand       Added swish-e integration as a plugin.
     Feb 11 2007         Anand       Changes in the swish-e plugin implementation,
                                     by using callbacks.
     Mar 2 2007          Anand       Renamed finish to finish_project. Moved
                                     Finish method from common.py to here and
                                     renamed it as finish(...). finish is never
                                     called at project end, but by default at
                                     program end.
     Mar 7 2007          Anand       Disabled urlserver option.
     Mar 15 2007         Anand       Added bandwidth calculation for determining
                                     max filesize before crawl. Need to add
                                     code to redetermine bandwidth when network
                                     interface changes.
     Apr 18 2007         Anand       Added the urltypes module for URL type
                                     definitions and replaced entries with it.
                                     Upped version number to 2.0 since this is
                                     almost a new program now!
     Apr 19 2007         Anand       Disabled urlserver option completely. Removed
                                     all referring code from this module, crawler
                                     and urlqueue modules. Moved code for grabbing
                                     URL to new hget module.
    Apr 24 2007          Anand       Made to work on Windows (XP SP2 Professional,
                                     Python 2.5)
    Apr 24 2007          Anand       Made the config directory creation/session
                                     saver features to work on Windows also.
    Apr 24 2007          Anand       Modified connector algorithm to flush data to
                                     temp files for hget. This makes sure that hget
                                     can download huge files as multipart.
    May 7 2007           Anand       Added plugin as option in configuration file.
                                     Added ability to process more than one plugin
                                     at once. Modified loading logic of plugins.
    May 10 2007          Anand       Replaced a number of private attributes in classes
                                     (with double underscores), to semi-private (one
                                     underscore). This helps in inheriting from these
                                     classes.
    Dec 12 2007          Anand       Re-merged code from harvestmanklass module to this
                                     and moved common initialization code to appbase.py
                                     under HarvestManAppBase class.
    Feb 12-14 08        Anand        Major datastructure enhancements/revisions, fixes
                                     etc in datamgr, rules, urlparser, connector, crawler,
                                     ,urlqueue, urlthread modules.

   Copyright (C) 2004 Anand B Pillai.     
"""     

__version__ = '2.0 a1'
__author__ = 'Anand B Pillai'

import __init__
import os, sys

from shutil import copy
import cPickle, pickle
import time
import threading
import shutil
import glob
import re
import copy
import signal
import locale

from harvestman.lib.event import HarvestManEvent
from harvestman.lib.common.common import *
from harvestman.lib.common.macros import *
from harvestman.lib import urlqueue
from harvestman.lib import connector
from harvestman.lib import rules
from harvestman.lib import datamgr
from harvestman.lib import utils
from harvestman.lib import urlparser
from harvestman.lib.db import HarvestManDbManager
from harvestman.lib.methodwrapper import MethodWrapperMetaClass

# Current folder - okay
from appbase import HarvestManAppBase

# Defining callback points
__callbacks__ = { 'run_saved_state_callback':'HarvestMan:run_saved_state',
                  'restore_state_callback':'HarvestMan:restore_state',
                  'run_projects_callback':'HarvestMan:run_projects',
                  'start_project_callback':'HarvestMan:start_project',
                  'finish_project_callback':'HarvestMan:finish_project',
                  'finalize_callback':'HarvestMan:finalize',                  
                  'init_callback' : 'HarvestMan:init'}

# Defining pluggable functions
__plugins__ = { 'clean_up_plugin':'HarvestMan:clean_up',
                'save_current_state_plugin': 'HarvestMan:save_current_state',
                'restore_state_plugin': 'HarvestMan:restore_state',
                'reset_state_plugin': 'HarvestMan:reset_state' }


class HarvestMan(HarvestManAppBase):
    """ The main crawler application class for HarvestMan """

    klassmap = {}
    __metaclass__ = MethodWrapperMetaClass
    alias = 'spider'
    
    USER_AGENT = "HarvestMan v2.0"
        
    def __init__(self):
        """ Initializing method """

        self._projectstartpage = 'file://'
        super(HarvestMan, self).__init__()
        
    def finish_project(self):
        """ Actions to take after download is over for the current project """

        if objects.eventmgr.raise_event('beforefinish', objects.queuemgr.baseurl, None)==False:
            return
        
        # Localise file links
        # This code sits in the data manager class
        objects.datamgr.post_download_setup()
        
        # if not objects.config.testing:
        if objects.config.browsepage:
            logconsole("Creating browser index page for the project...")
            browser = utils.HarvestManBrowser()
            browser.make_project_browse_page()
            logconsole("Done.")

        objects.eventmgr.raise_event('afterfinish', objects.queuemgr.baseurl, None)
        
    def finalize(self):
        """ This method is called at program exit or when handling signals to clean up """
        
        # If this was started from a runfile,
        # remove it.
        if objects.config.runfile:
            try:
                os.remove(objects.config.runfile)
            except OSError, e:
                error('Error removing runfile %s.' % objects.config.runfile)

        # inform user of config file errors
        if globaldata.userdebug:
            logconsole("Some errors were found in your configuration, please correct them!")
            for x in range(len(globaldata.userdebug)):
                logconsole(str(x+1),':', globaldata.userdebug[x])

        globaldata.userdebug = []
        logconsole('HarvestMan session finished.')

        objects.datamgr.clean_up()
        objects.rulesmgr.clean_up()
        objects.logger.shutdown()

    def save_current_state(self):
        """ Save state of objects to disk so program can be restarted from saved state """

        # If savesession is disabled, return
        if not objects.config.savesessions:
            extrainfo('Session save feature is disabled.')
            return
        
        # Top-level state dictionary
        state = {}
        # All state objects are dictionaries

        # Get state of queue & tracker threads
        state['trackerqueue'] = objects.queuemgr.get_state()
        # Get state of datamgr
        state['datamanager'] = objects.datamgr.get_state()
        # Get state of urlthreads 

        #if p: state['threadpool'] = p.get_state()
        #state['ruleschecker'] = objects.rulesmgr.get_state()

        # Get config object
        #state['configobj'] = objects.config.copy()
        
        # Dump with time-stamp 
        fname = os.path.join(objects.config.usersessiondir, '.harvestman_saves#' + str(int(time.time())))
        extrainfo('Saving run-state to file %s...' % fname)

        try:
            cPickle.dump(state, open(fname, 'wb'), pickle.HIGHEST_PROTOCOL)
            extrainfo('Saved run-state to file %s.' % fname)
        except (pickle.PicklingError, RuntimeError), e:
            logconsole(e)
            error('Could not save run-state !')
        
    def welcome_message(self):
        """ Prints a welcome message before start of the program """

        logconsole('Starting %s...' % objects.config.progname)
        logconsole('Copyright (C) 2004, Anand B Pillai')
        logconsole(' ')

    def register_common_objects(self):
        """ Create and register aliases for the common objects required by all program modules """

        # Set myself
        SetAlias(self)

        objects.logger.make_logger()
        # Set verbosity in logger object
        objects.logger.setLogSeverity(objects.config.verbosity)
        
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

        SetAlias(HarvestManEvent())
        
    def start_project(self):
        """ Starts crawl for the current project, crawling its URL  """

        if objects.eventmgr.raise_event('beforestart', objects.queuemgr.baseurl, None)==False:
            return
        
        # crawls through a site using http/ftp/https protocols
        if objects.config.project:
            info('*** Log Started ***\n')
            if not objects.config.resuming:
                info('Starting project',objects.config.project,'...')
            else:
                info('Re-starting project',objects.config.project,'...')                

            
            # Write the project file 
            if not objects.config.fromprojfile:
                projector = utils.HarvestManProjectManager()
                projector.write_project()

            # Write the project database record
            HarvestManDbManager.add_project_record()
            
        if not objects.config.resuming:
            info('Starting download of url',objects.config.url,'...')
        else:
            pass

        # Reset objects keeping project-specific states now
        # Reset and re-initialize datamgr
        objects.datamgr.clean_up()
        objects.datamgr.initialize()
        objects.rulesmgr.reset()
            
        # Read the project cache file, if any
        if objects.config.pagecache:
            objects.datamgr.read_project_cache()
            
        if not objects.config.resuming:
            # Configure tracker manager for this project
            if objects.queuemgr.configure():
                # start the project
                objects.queuemgr.crawl()
        else:
            objects.queuemgr.restart()

        objects.eventmgr.raise_event('afterstart', objects.queuemgr.baseurl, None)
        
    def clean_up(self):
        """ Performs clean up actions as part of the interrupt handling """

        # Shut down logging on file
        extrainfo('Shutting down logging...')
        objects.logger.disableFileLogging()
        objects.queuemgr.endloop()

    def calculate_bandwidth(self):
        """ Calculate bandwidth of the user by downloading a specific URL and timing it,
        setting a limit on maximum file size """

        # Calculate bandwidth
        bw = 0
        # Look for harvestman.conf in user conf dir
        conf = os.path.join(objects.config.userconfdir, 'harvestman.conf')
        if not os.path.isfile(conf):
            conn = connector.HarvestManUrlConnector()
            urlobj = urlparser.HarvestManUrl('http://harvestmanontheweb.com/schemas/HarvestMan.xsd')
            bw = conn.calc_bandwidth(urlobj)
            bwstr='bandwidth=%f\n' % bw
            if bw:
                try:
                    open(conf,'w').write(bwstr)
                except IOError, e:
                    pass
        else:
            r = re.compile(r'(bandwidth=)(.*)')
            try:
                data = open(conf).read()
                m = r.findall(data)
                if m:
                    bw = float(m[0][-1])
            except IOError, e:
                pass

        return bw
        
    def create_user_directories(self):
        """ Creates the user folders for HarvestMan. Creates folders for storing user specific
        configuration, session and crawl database information """

        # Create user's HarvestMan directory on POSIX at $HOME/.harvestman and 
        # on Windows at $USERPROFILE/Local Settings/Application Data/HarvestMan
        harvestman_dir = objects.config.userdir
        harvestman_conf_dir = objects.config.userconfdir
        harvestman_sessions_dir = objects.config.usersessiondir
        harvestman_db_dir = objects.config.userdbdir
        
        if not os.path.isdir(harvestman_dir):
            try:
                logconsole('Looks like you are running HarvestMan for the first time in this machine')
                logconsole('Doing initial setup...')
                logconsole('Creating folder %s for storing HarvestMan application data...' % harvestman_dir)
                os.makedirs(harvestman_dir)
            except (OSError, IOError), e:
                logconsole(e)

        if not os.path.isdir(harvestman_conf_dir):
            try:
                logconsole('Creating "conf" sub-directory in %s...' % harvestman_dir)
                os.makedirs(harvestman_conf_dir)

                # Create user configuration in .harvestman/conf
                conf_data = objects.config.generate_user_configuration()
                logconsole("Generating user configuration in %s..." % harvestman_conf_dir)
                try:
                    user_conf_file = os.path.join(harvestman_conf_dir, 'config.xml')
                    open(user_conf_file, 'w').write(conf_data)
                    logconsole("Done.")                    
                except IOError, e:
                    print e

            except (OSError, IOError), e:
                logconsole(e)

        if not os.path.isdir(harvestman_sessions_dir):
            try:
                logconsole('Creating "sessions" sub-directory in %s...' % harvestman_dir)
                os.makedirs(harvestman_sessions_dir)                        
                logconsole('Done.')
            except (OSError, IOError), e:
                logconsole(e)

        if not os.path.isdir(harvestman_db_dir):
            try:
                logconsole('Creating "db" sub-directory in %s...' % harvestman_dir)
                os.makedirs(harvestman_db_dir)                        
                logconsole('Done.')
            except (OSError, IOError), e:
                logconsole(e)

            try:
                HarvestManDbManager.create_user_database()
            except Exception, e:
                logconsole(e)
                
        
    def init(self):
        """ Initialize the crawler by creating, register common objects and creating the
        user folders """

        if objects.config.USER_AGENT=='':
            objects.config.USER_AGENT = self.__class__.USER_AGENT
            
        self.register_common_objects()
        self.create_user_directories()

        # Calculate bandwidth and set max file size
        # bw = self.calculate_bandwidth()
        # Max file size is calculated as bw*timeout
        # where timeout => max time for a worker thread
        # if bw: objects.config.maxfilesize = bw*objects.config.timeout
        
    def init_config(self):
        """ Initialize the configuration of the crawler """
        
        # Following 2 methods are inherited from the parent class
        self.get_options()
        self.process_plugins()
        # For the time being, save session set to false
        objects.config.savesessions = 0

    def get_config(self):
        """ Return the configuration object """

        return objects.config
        
    def initialize(self):
        """ Umbrella method to initialize the crawler configuration
        and the crawler object """
        
        self.init_config()
        self.init()

    def reset(self):
        """ Resets the state of the crawler, except the state of the
        configuration object """
        
        self.init()
        
    def run_projects(self):
        """ Run all the HarvestMan projects specified for the current session """

        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        locale.setlocale(locale.LC_ALL, '')

        objects.rulesmgr.make_filters()
        
        if objects.config.verbosity:
            self.welcome_message()

        for x in range(len(objects.config.projects)):
            # Get all project related vars
            entry = objects.config.projects[x]

            url = entry.get('url')
            project = entry.get('project')
            basedir = entry.get('basedir')
            verb = entry.get('verbosity')

            if not url or not project or not basedir:
                info('Invalid config options found!')
                if not url: info('Provide a valid url')
                if not project: info('Provide a valid project name')
                if not basedir: info('Provide a valid base directory')
                continue
            
            # Set the current project vars
            objects.config.url = url
            objects.config.project = project
            objects.config.verbosity = verb
            objects.config.basedir = basedir

            try:
                self.run_project()
            except Exception, e:
                # Note: This design means that when we are having more than
                # one project configured, HarvestMan exits only the current
                # project if an interrupt (Ctrl-C) is received. The next
                # project will continue when control comes back...This was
                # not intentional, but is a good side-effect.
                
                # However if a Python exception is received, we exit the
                # program after calling this function...
                self.handle_interrupts(-1, None, e)
                    
    def run_project(self):
        """ Run the current HarvestMan project by creating any project directories
        , initializing state and starting the project """

        # Set project directory
        # Expand any shell variables used in the base directory.
        objects.config.basedir = os.path.expandvars(os.path.expanduser(objects.config.basedir))
        
        if objects.config.basedir:
            objects.config.projdir = os.path.join( objects.config.basedir, objects.config.project )
            if objects.config.projdir and not os.path.exists( objects.config.projdir ):
                os.makedirs(objects.config.projdir)
                
            if objects.config.datamode == CONNECTOR_DATA_MODE_FLUSH:    
                objects.config.projtmpdir = os.path.join(objects.config.projdir, '.tmp')
                if objects.config.projtmpdir and not os.path.exists( objects.config.projtmpdir ):
                    os.makedirs(objects.config.projtmpdir)            

        # Set message log file
        if objects.config.projdir and objects.config.project:
            objects.config.logfile = os.path.join( objects.config.projdir, "".join((objects.config.project,
                                                                          '.log')))

        SetLogFile()

        if not objects.config.testnocrawl:
            self.start_project()

        self.finish_project()
            
    def restore_state(self, state_file):
        """ Restore state of some objects from the most recent run of the program.
        This helps to re-run the program from where it left off """

        try:
            state = cPickle.load(open(state_file, 'rb'))
            # This has six keys - configobj, threadpool, ruleschecker,
            # datamanager, common and trackerqueue.

            # First update config object
            localcfg = {}
            cfg = state.get('configobj')
            if cfg:
                for key,val in cfg.items():
                    localcfg[key] = val
            else:
                print 'Config corrupted'
                return RESTORE_STATE_NOT_OK

            # Now update trackerqueue
            ret = objects.queuemgr.set_state(state.get('trackerqueue'))
            if ret == -1:
                logconsole("Error restoring state in 'urlqueue' module - cannot proceed further!")
                return RESTORE_STATE_NOT_OK                
            else:
                logconsole("Restored state in urlqueue module.")
            
            # Now update datamgr
            ret = objects.datamgr.set_state(state.get('datamanager'))
            if ret == -1:
                logconsole("Error restoring state in 'datamgr' module - cannot proceed further!")
                return RESTORE_STATE_NOT_OK                
            else:
                dm.initialize()
                logconsole("Restored state in datamgr module.")                
            
            # Update threadpool if any
            pool = None
            if state.has_key('threadpool'):
                pool = dm._urlThreadPool
                ret = pool.set_state(state.get('threadpool'))
                logconsole('Restored state in urlthread module.')
            
            # Update ruleschecker
            ret = objects.rulesmgr.set_state(state.get('ruleschecker'))
            logconsole('Restored state in rules module.')

            # Everything is fine, copy localcfg to config object
            for key,val in localcfg.items():
                objects.config[key] = val

            # Open stream to log file
            SetLogFile()
                
            return RESTORE_STATE_OK
        except (pickle.UnpicklingError, AttributeError, IndexError, EOFError), e:
            return RESTORE_STATE_NOT_OK            

    def run_saved_state(self):
        """ Restart the program from a previous state, from state saved during
        the most recent run of the program, if any """
        
        # If savesession is disabled, return
        #if not objects.config.savesessions:
        extrainfo('Session save feature is disabled, ignoring save files')
        return SAVE_STATE_NOT_OK
        
        # Set locale - To fix errors with
        # regular expressions on non-english web
        # sites.
        # See if there is a file named .harvestman_saves#...
  ##       sessions_dir = objects.config.usersessiondir

##         files = glob.glob(os.path.join(sessions_dir, '.harvestman_saves#*'))

##         # Get the last dumped file
##         if files:
##             runfile = max(files)
##             res = raw_input('Found HarvestMan save file %s. Do you want to re-run it ? [y/n]' % runfile)
##             if res.lower()=='y':
##                 if self.restore_state(runfile) == RESTORE_STATE_OK:
##                     objects.config.resuming = True
##                     objects.config.runfile = runfile

##                     if objects.config.verbosity:
##                         self.welcome_message()
        
##                     if not objects.config.testnocrawl:
##                         try:
##                             self.start_project()
##                         except Exception, e:
##                             self.handle_interrupts(-1, None, e)

##                     try:
##                         self.finish_project()
##                         return SAVE_STATE_OK
                    
##                     except Exception, e:
##                         # To catch errors at interpreter shutdown
##                         pass
##                 else:
##                     logconsole('Could not re-run saved state, defaulting to standard configuration...')
##                     objects.config.resuming = False
##                     return SAVE_STATE_NOT_OK
##             else:
##                 logconsole('OK, falling back to default configuration...')
##                 return SAVE_STATE_NOT_OK
##         else:
##             return SAVE_STATE_NOT_OK
##         pass

    def handle_interrupts(self, signum, frame, e=None):
        """ Method which is called to handle program interrupts such as a Ctrl-C (interrupt) """

        # print 'Signal handler called with',signum
        if signum == signal.SIGINT:
            objects.config.keyboardinterrupt = True

        if e != None:
            logconsole('Exception received=>',e)
            print_traceback()

        logtraceback()
        # dont allow to write cache, since it
        # screws up existing cache.
        objects.datamgr.conditional_cache_set()
        # self.save_current_state()
        self.clean_up()

    def bind_event(self, event, funktion, *args):
        """ Binds a function to a specific event in HarvestMan """
        
        objects.eventmgr.bind(event, funktion, args)
        
    def main(self):
        """ The main sub-routine of the HarvestMan class """

        # Set stderr to dummy to prevent all the thread
        # errors being printed by interpreter at shutdown
        # sys.stderr = DummyStderr()
        signal.signal(signal.SIGINT, self.handle_interrupts)
        
        # See if a crash file is there, then try to load it and run
        # program from crashed state.
        if self.run_saved_state() == SAVE_STATE_NOT_OK:
            # No such crashed state or user refused to run
            # from crashed state. So do the usual run.
            self.run_projects()
            
        # Final cleanup
        self.finalize()

def callgraph_filter(call_stack, module_name, class_name, func_name, full_name):
    """ Function which is used to filter the call graphs when HarvestMan is
    run with 'pycallgraph' to generate call graph trees """
    
    if class_name.lower().find('harvestman') != -1 or \
       full_name.lower().find('harvestman') != -1:
        return True
    else:
        return False
    
if __name__=="__main__":
    spider = HarvestMan()
    spider.initialize()
    #import pycallgraph
    #pycallgraph.start_trace(filter_func=callgraph_filter)
    spider.main()
    #pycallgraph.make_dot_graph('harvestman.png')
    

               
        

