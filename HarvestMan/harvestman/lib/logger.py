# -- coding: utf-8
"""
logger.py -  Logging functions for HarvestMan.
This module is part of the HarvestMan program.

Author: Anand B Pillai <abpillai at gmail dot com>

Created: Jan 23 2005

Modification History

   Aug 17 06 Anand   Made this to use Python logging module.
   Jul 11 08 Anand   Modified to suit standard logging with an
                     extra level named EXTRAINFO between INFO
                     and DEBUG.Fix for google code issue #12.

Copyright (C) 2005 Anand B Pillai.

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import logging, logging.handlers
import os, sys
from types import StringTypes

class HandlerFactory(object):
    """ Factory class to create handlers of different families for use by the logging class """
    
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

# Our logging levels are the following. We confirm
# to Python logging except for the additional level
# between DEBUG and INFO named "EXTRAINFO".
# CRITICAL 50
# ERROR         40
# WARNING 30
# INFO  20
# EXTRAINFO 15
# DEBUG         10
# NOTSET        0

CRITICAL=logging.CRITICAL
ERROR=logging.ERROR
WARNING=logging.WARNING
INFO=logging.INFO
EXTRAINFO=(logging.INFO+logging.DEBUG)/2
DEBUG=logging.DEBUG
DISABLE=NOTSET=logging.NOTSET

def getLogLevel(levelname):
    """ Return the loglevel given the level name """

    if type(levelname) in StringTypes:
        return eval(levelname.upper())
    elif type(levelname) is int:
        return levelname

def getLogLevelName(level):
    """ Return the loglevel name given the level """
    
    return HarvestManLogger.getLevelName(level)

class HarvestManLogger(object):
    """ A customizable logging class for HarvestMan with different
    levels of logging support """

    alias = 'logger'

    # Dictionary from levels to level names
    _namemap = { 0: 'NOTSET',
                 10: 'DEBUG',
                 15: 'EXTRAINFO',
                 20: 'INFO',
                 30: 'WARNING',
                 40: 'ERROR',
                 50: 'CRITICAL' }

    # Map of instances
    _instances = {'default': None}
    
    def __init__(self, severity=INFO, logflag=2):
        """ Initialize the logger class with severity and logflag """

        # Add our custom logging level to the module
        logging.addLevelName(EXTRAINFO, 'EXTRAINFO')
        
        self._severity = severity
        self._formattercache = {}
        
        if logflag==0:
            self._severity = DISABLE
        else:
            self._severity = severity
            if logflag == 2:
                self.consolelog = True

    def make_logger(self):
        
        self._logger = logging.Logger('HarvestMan')
        self._logger.setLevel(self._severity)
            
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
        
    @classmethod
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
        self._logger.setLevel(self._severity)        

    def addLogHandler(self, handlertype, *args):
        """ Generic method to add a handler to the logger """

        # handlertype should be a string
        # Call helper function here
        handler = HandlerFactory.createHandle(handlertype, *args)
        if handlertype != 'StreamHandler':
            formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s',
                                            '(%d-%m-%y) [%H:%M:%S]')
        else:
            # Minimal formatting for console log
            formatter = logging.Formatter('[%(asctime)s] %(message)s',
                                          '%H:%M:%S')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def removeLogHandlers(self, handlertype):
        """ Generic method to remove a handler from the logger """

        for h in self._logger.handlers:
            if h.__class__.__name__ == handlertype:
                # Remove the handler
                self._logger.removeHandler(h)

    def enableConsoleLogging(self):
        """ Enable console logging - if console logging is already
        enabled, this method does not have any effect """

        if not self.consolelog:
            self.addLogHandler('StreamHandler')
            self.consolelog = True

    def disableConsoleLogging(self):
        """ Disable console logging - if console logging is already
        disabled, this method does not have any effect """

        # Find out streamhandler if any
        self.removeLogHandlers('StreamHandler')
        self.consolelog=False

    def disableFileLogging(self):
        """ Disable file logging - if file logging is already
        disabled, this method does not have any effect """

        self.removeLogHandlers('FileHandler')

    def addLogFile(self, filename):
        """ Add a log file named 'filename' to the logger """

        self.addLogHandler('FileHandler', filename)

    def removeLogFile(self, filename):
        """ Remove log file named 'filename' from the logger. If
        only a filename is passed instead of a file path, the file
        is assumed to be in the current directory """
        
        for h in self._logger.handlers:
            if h.__class__.__name__ == 'FileHandler':
                fname = h.baseFilename
                if (os.path.abspath(filename)==os.path.abspath(fname)):
                    # Remove the handler
                    self._logger.removeHandler(h)
                    break

    def setPlainFormat(self):
        """ Set format to displaying messages-only without any timestamps etc """

        formatter = logging.Formatter('%(message)s')
        for h in self._logger.handlers:
            # Cache previous formatter for reverting later if requested
            self._formattercache[hash(h)] = h.formatter
            h.setFormatter(formatter)

    def revertFormatting(self):
        """ Revert formatting for all handlers if a cache is found """

        for h in self._logger.handlers:
            h.setFormatter(self._formattercache[hash(h)])
        
    def debug(self, msg, *args):
        """ Perform logging at the DEBUG level """

        try:
            self._logger.debug(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def info(self, msg, *args):
        """ Perform logging at the INFO level """
        
        try:
            self._logger.info(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass

    def extrainfo(self, msg, *args):
        """ Perform logging at the EXTRAINFO level """

        try:
            self._logger.log(EXTRAINFO, self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def warning(self, msg, *args):
        """ Perform logging at the WARNING level """

        try:
            self._logger.warning(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass

    def error(self, msg, *args):
        """ Perform logging at the ERROR level """

        try:
            self._logger.error(self._getMessage(msg, *args))
        except ValueError, e:
            pass
        except IOError, e:
            pass
        
    def critical(self, msg, *args):
        """ Perform logging at the CRITICAL level """

        try:
            self._logger.critical(self._getMessage(msg, *args))
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
    mylogger.make_logger()
    
    mylogger.addLogHandler('FileHandler','report.log')
    
    p = 'HarvestMan'
    mylogger.debug("Test message 1",p)
    mylogger.extrainfo("Test message 2",p)
    mylogger.info("Test message 3",p)
    mylogger.warning("Test message 4",p)
    mylogger.error("Test message 5",p)
    mylogger.critical("Test message 6",p)
    
    print mylogger.getLogSeverity()
    print mylogger.getLogLevelName()

    mylogger.enableConsoleLogging()
    # mylogger.disableConsoleLogging()    
    mylogger.disableFileLogging()

    mylogger.debug("Test message 1",p)
    mylogger.extrainfo("Test message 2",p)
    mylogger.info("Test message 3",p)
    mylogger.warning("Test message 4",p)
    mylogger.error("Test message 5",p)    
    mylogger.critical("Test message 6",p)    

    print HandlerFactory.createHandle('StreamHandler', sys.stdout)
    print HandlerFactory.createHandle('FileHandler', 'my.txt')
    print HandlerFactory.createHandle('SocketHandler', 'localhost', 5555)

    mylogger.addLogHandler('FileHandler','my.txt')
    
    # Change severity to extrainfo
    mylogger.setLogSeverity(EXTRAINFO)

    mylogger.debug("Test message 1",p)
    mylogger.extrainfo("Test message 2",p)
    mylogger.info("Test message 3",p)
    mylogger.warning("Test message 4",p)
    mylogger.error("Test message 5",p)    
    mylogger.critical("Test message 6",p)
    
    print HarvestManLogger.getDefaultLogger()==mylogger
    print HarvestManLogger._instances
    
    print getLogLevel('info')
    print getLogLevelName(EXTRAINFO)
