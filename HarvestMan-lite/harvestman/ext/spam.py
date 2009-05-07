# -- coding: utf-8
""" Test plugin for HarvestMan. This demonstrates
how to write a simple plugin based on callbacks.

Author: Anand B Pillai <anand at harvestmanontheweb.com>

Created Feb 7 2007  Anand B Pillai <abpillai at gmail dot com>

Copyright (C) 2007 Anand B Pillai
   
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

from harvestman.lib import hooks
from harvestman.lib.common.common import *

def func(self):
    print 'Before running projects...'

def apply_plugin():
    """ All plugin modules need to define this method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.
    
    hooks.register_pre_callback_method('harvestman:run_projects_callback', func)

