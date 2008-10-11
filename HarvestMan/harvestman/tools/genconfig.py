"""
genconfig.py - Interactive web-based HarvestMan configuration
file generator using web.py .

Created Anand B Pillai <abpillai at gmail dot com> May 29 2008
Modified Anand B Pillai  Moved most code to lib/gui.py Jun 01 2008
                         and trimmed this modul.e
Modified Lukasz Szybalski 
    Created main function and will be added to harvestman menu as harvestman --genconfig.

Copyright (C) 2008 Anand B Pillai.
"""

import sys
import webbrowser
import threading
import time
import web

from harvestman.lib import gui

index = gui.HarvestManConfigGenerator
urls = ('/', 'index')

def open_page():
    print 'Opening page...'
    webbrowser.open("http://localhost:5940")

if __name__=="__main__":
    sys.argv.append("5940")
    print "Starting web.py at port 5940..."
    web.internalerror = web.debugerror
    # Start timer thread to run after 5 seconds
    print 'Waiting for page to load in browser...'
    threading.Timer(5.0, open_page).start()
    web.run(urls, globals(), web.reloader)

#Allows to be imported and run
def main():
    #if __name__=="__main__":
    #sys.argv.append("5940")
    #Because web.py expects the port to be passed on argv[1] I will replace it here. The original argv[1] is '--genconf'
    sys.argv[1]='5940'
    print "Starting web.py at port 5940..."
    web.internalerror = web.debugerror
    # Start timer thread to run after 5 seconds
    print 'Waiting for page to load in browser...'
    threading.Timer(5.0, open_page).start()
    web.run(urls, globals(), web.reloader)
