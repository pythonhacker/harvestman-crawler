# -- coding: utf-8
"""
logger.py -  Logging functions for HarvestMan.
This module is part of the HarvestMan program.

Author: Anand B Pillai <abpillai at gmail dot com>

Created: Jan 23 2005

Modification History

   Aug 17 06 Anand   Made this to use Python logging module.

Copyright (C) 2005 Anand B Pillai.

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import logging, logging.handlers
import os, sys

class HandlerFactory(object):
    """ Factory class to create handlers of different families for use by SIMLogger """
    
    def createHandle(handlertype, *args):
        """ Return a logging handler of the given type.
        The handler will be initialized using params from the args
        argument tuple """

        if handlertype == 'StreamHandler':
            return logging.StreamHandler(*args)
        elif handlertype == 'FileHandler':
            return logging.FileHandler(*args)
        elif handlertype == 'SocketHandler':
            return logging.handlers.SocketHandler(*args)        
        
    createHandle = staticmethod(createHandle)



# Useful macros for setting
# the log level.
    
DISABLE = 0
INFO = 1
MOREINFO  = 2
EXTRAINFO = 3
DEBUG   = 4
MOREDEBUG = 5
        
class HarvestManLogger(object):
    """ A customizable logging class for HarvestMan with different
    levels of logging support """

    alias = 'logger'
    
    # Dictionary from levels to level names
    _namemap = { 0: 'DISABLE',
                 1: 'INFO',
                 2: 'MOREINFO',
                 3: 'EXTRAINFO',
                 4: 'DEBUG',
                 5: 'MOREDEBUG' }

    # Map of instances
    _instances = {'default': None}
    
    def __init__(self, severity=1, logflag=2):
        """ Initialize the logger class with severity and logflag """
        
        self._severity = severity
        # Handler cache
        self._cachehandler = None
        
        if logflag==0:
            self._severity = 0
        else:
            self._severity = severity
            if logflag == 2:
                self.consolelog = True

    def make_logger(self):
        
        self._logger = logging.Logger('HarvestMan')
        self._logger.setLevel(logging.DEBUG)
            
        if self.consolelog:
            formatter = logging.Formatter('[%(asctime)s] %(message)s',
                                          '%H:%M:%S')
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
        else:
            pass

    def _getMessage(self, arg, *args):
        """ Private method to create a message string from the supplied arguments """

        try:
            return ''.join((str(arg),' ',' '.join([str(item) for item in args])))
        except UnicodeEncodeError:
            try:
                return ''.join((str(arg),' ',' '.join([str(item.encode('iso-8859-1')) for item in args])))
            except UnicodeDecodeError:
                return str(arg)
        
    def getLevelName(self, level):
        """ Return the level name, given the level value """
        
        return self._namemap.get(level, '')

    def getLogLevel(self):
        """ Return the current log level """

        # Same as severity
        return self.getLogSeverity()

    def getLogSeverity(self):
        """ Return the current log severity """

        return self._severity

    def getLogLevelName(self):
        """ Return the name of the current log level """

        return self.getLevelName(self._severity)

    def setLogSeverity(self, severity):
        """ Set the log severity """

        self._severity = severity

    def addLogHandler(self, handlertype, *args):
        """ Generic method to add a handler to the logger """

        # handlertype should be a string
        # Call helper function here
        handler = HandlerFactory.createHandle(handlertype, *args)
        formatter = logging.Formatter('%(asctime)s %(message)s',
                                          '(%d-%m-%y) [%H:%M:%S]')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        
    def enableConsoleLogging(self):
        """ Enable console logging - if console logging is already
        enabled, this method does not have any effect """

        console = 'StreamHandler' in [h.__class__.__name__ for h in self._logger.handlers]
        
        if not console:
            if self._cachehandler.__class__.__name__ == 'StreamHandler':
                handler = self._cachehandler
            else:
                formatter = logging.Formatter('[%(asctime)s] %(message)s',
                                              '%H:%M:%S')
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                
            self._logger.addHandler(handler)
        else:
            pass

    def disableConsoleLogging(self):
        """ Disable console logging - if console logging is already
        disabled, this method does not have any effect """

        # Find out streamhandler if any
        for h in self._logger.handlers:
            if h.__class__.__name__ == 'StreamHandler':
                # Cache the handler if we want to readd quickly
                self._cachehandler = h
                # Remove the handler
                self._logger.removeHandler(h)
                break
        else:
            pass

    def disableFileLogging(self):
        """ Disable file logging - if file logging is already
        disabled, this method does not have any effect """

        # Find out filehandler if any
        for h in self._logger.handlers:
            if h.__class__.__name__ == 'FileHandler':
                # Remove the handler
                self._logger.removeHandler(h)
                break
        else:
            pass

    def setPlainFormat(self):
        """ Set format to displaying messages-only without any timestamps etc """

        formatter = logging.Formatter('%(message)s')
        for h in self._logger.handlers:
            h.setFormatter(formatter)
        
    def info(self, msg, *args):
        """ Perform logging at the INFO level """
        
        try:
            (self._severity>=INFO) and self._logger.info(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass

    def moreinfo(self, msg, *args):
        """ Perform logging at the MOREINFO level """

        try:
            (self._severity>=MOREINFO) and self._logger.info(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def extrainfo(self, msg, *args):
        """ Perform logging at the EXTRAINFO level """

        try:
            (self._severity>=EXTRAINFO) and self._logger.info(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def debug(self, msg, *args):
        """ Perform logging at the DEBUG level """

        try:
            (self._severity>=DEBUG) and self._logger.info(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def moredebug(self, msg, *args):
        """ Perform logging at the MOREDEBUG level """

        try:
            (self._severity>=MOREDEBUG) and self._logger.info(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def logconsole(self, msg, *args):
        """ Directly log to console using sys.stdout """

        try:
            (self._severity>DISABLE) and sys.stdout.write(self._getMessage(msg, *args)+'\n')
        except ValueError, e:
            pass
        except IOError, e:
            pass

    def getDefaultLogger(cls):
        """ Return the default logger instance """

        return cls._instances.get('default')
    
    def Instance(cls, name='default', *args):
        """ Return an instance of this class """

        inst = cls(*args)
        cls._instances[name] = inst

        return inst

    def clean_up(self):
        # Remove all handlers...
        for h in self._logger.handlers:
            if h.__class__.__name__ == 'FileHandler':            
                # Remove the handler
                self._logger.removeHandler(h)

    def shutdown(self):
        logging.shutdown()
        
    Instance = classmethod(Instance)
    getDefaultLogger = classmethod(getDefaultLogger)
    
if __name__=="__main__":
    import sys
    
    mylogger = HarvestManLogger.Instance()
    mylogger.addLogHandler('FileHandler','report.log')
    # mylogger.setLogSeverity(1)
    
    p = 'HarvestMan'
    mylogger.info("Test message 1",p)
    mylogger.moreinfo("Test message 2",p)
    mylogger.extrainfo("Test message 3",p)
    mylogger.debug("Test message 4",p)
    mylogger.moredebug("Test message 5",p)
    
    print mylogger.getLogSeverity()
    print mylogger.getLogLevelName()

    mylogger.enableConsoleLogging()
    # mylogger.disableConsoleLogging()    
    mylogger.disableFileLogging()
    
    mylogger.info("Test message 1",p)
    mylogger.moreinfo("Test message 2",p)
    mylogger.extrainfo("Test message 3",p)
    mylogger.debug("Test message 4",p)
    mylogger.moredebug("Test message 5",p)


    print HandlerFactory.createHandle('StreamHandler', sys.stdout)
    print HandlerFactory.createHandle('FileHandler', 'my.txt')
    print HandlerFactory.createHandle('SocketHandler', 'localhost', 5555)

    mylogger.info("Test message 1",p)
    mylogger.moreinfo("Test message 2",p)
    mylogger.extrainfo("Test message 3",p)
    mylogger.debug("Test message 4",p)
    mylogger.moredebug("Test message 5",p)    

    print HarvestManLogger.getDefaultLogger()==mylogger
    print HarvestManLogger._instances
