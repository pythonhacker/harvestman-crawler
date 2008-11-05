# -- coding: utf-8
""" filethread.py - File saver thread module.
    This module is part of the HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
   Copyright (C) 2007 Anand B Pillai.
    
"""

# Currently no code from this module is being used anywhere
# in the program.

import threading
from common.common import *
from common.singleton import Singleton
import sys, os
import shutil
from Queue import Queue

class FileQueue(Queue, Singleton):
    """ File saver queue class """
    
    def push(self, filename, directory, url, datastring):
        self.put((filename, directory, url, datastring))

class HarvestManFileThread(threading.Thread):
    """ File saver thread """
    
    def __init__(self):
        self.q = FileQueue.getInstance()
        self._flag = False
        self._cfg = objects.config
        threading.Thread.__init__(self, None, None, 'Saver')
            
    def _write_url_filename(self, data, filename):
        """ Write downloaded data to the passed file """

        try:
            extrainfo('Writing file ', filename)
            f=open(filename, 'wb')
            # print 'Data len=>',len(self._data)
            f.write(data.getvalue())
            f.close()
        except IOError,e:
            debug('IO Exception' , str(e))
            return 0
        except ValueError, e:
            return 0

        return 1

    def stop(self):
        self._flag = True
        
    def run(self):

        while not self._flag:
            item = self.q.get()
            if item:
                filename, directory, url, datastring = item
                if self.create_local_directory(directory) == 0:
                    self._write_url_filename( datastring, filename )
                else:
                    extrainfo("Error in creating local directory for", url)

    def create_local_directory(self, directory):
        """ Create the directories on the disk named 'directory' """

        # new in 1.4.5 b1 - No need to create the
        # directory for raw saves using the nocrawl
        # option.
        if self._cfg.rawsave:
            return 0

        try:
            # Fix for EIAO bug #491
            # Sometimes, however had we try, certain links
            # will be saved as files, whereas they might be
            # in fact directories. In such cases, check if this
            # is a file, then create a folder of the same name
            # and move the file as index.html to it.
            path = directory
            while path:
                if os.path.isfile(path):
                    # Rename file to file.tmp
                    fname = path
                    os.rename(fname, fname + '.tmp')
                    # Now make the directory
                    os.makedirs(path)
                    # If successful, move the renamed file as index.html to it
                    if os.path.isdir(path):
                        fname = fname + '.tmp'
                        shutil.move(fname, os.path.join(path, 'index.html'))
                    
                path2 = os.path.dirname(path)
                # If we hit the root, break
                if path2 == path: break
                path = path2
                
            if not os.path.isdir(directory):
                os.makedirs( directory )
                extrainfo("Created => ", directory)
            return 0
        except OSError:
            moreinfo("Error in creating directory", directory)
            return -1

        return 0

                    
            
