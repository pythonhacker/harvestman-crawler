# -- coding: utf-8
"""event.py - Module defining an event notification framework
associated with the data flow in HarvestMan.

Created Anand B Pillai <abpillai at gmail dot com> Feb 28 2008

Copyright (C) 2008 Anand B Pillai.
"""

from harvestman.lib.common.common import *
from harvestman.lib.common.singleton import Singleton

class Event(object):
    """ Event class for HarvestMan """

    def __init__(self):
        self.name = ''
        self.config = objects.config
        self.url = None
        self.document = None

class HarvestManEvent(Singleton):
    """ Event manager class for HarvestMan """

    alias = 'eventmgr'

    def __init__(self):
        self.events = {}
        
    def bind(self, event, funktion, *args):
        """ Register for a function 'funktion' to be bound to a certain event.
        The return value of the function will be used to determine the behaviour
        of the original function which raises the event in cases of events
        which are called before the original function bound to the event. For
        events which are raised after the original function is called, the
        behavior of the original function is not changed """

        # An event is a string, you can bind only one function to an event
        # The function should accept a default first argument which is the
        # event object. The event object will provide 4 attributes, namely
        # the event name, the url associated to the event (should be valid),
        # the document associated to the event (could be None) and the configuration
        # object of the system.
        self.events[event] = funktion
        # print self.events
        
    def raise_event(self, event, url, document=None, *args, **kwargs):
        """ Raise a certain event. This automatically calls back on any function
        registered for the event and returns the return value of that function. This
        is an internal method """

        try:
            funktion = self.events[event]
            eventobj = Event()
            eventobj.name = event
            eventobj.url = url
            eventobj.document = document
            # Other keyword arguments
            return funktion(eventobj, *args, **kwargs)
        except KeyError:
            pass


