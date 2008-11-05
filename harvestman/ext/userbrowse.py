# -- coding: utf-8
""" User browse plugin. Simulate a scenario of a user
browsing a web-page.

(Requested by Roy Cheeran)

Author: Anand B Pillai <anand at harvestmanontheweb.com>

Created  Aug 13 2007     Anand B Pillai 

Copyright (C) 2007 Anand B Pillai

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

from harvestman.lib import hooks
from harvestman.lib.common.common import *

# User browsing plugin approximates how a webpage
# presents itself to a user. This means a few things
#
# 1. All images and stylesheets referenced by the page are fetched.
# 2. In addition, all links directly linked from the page are
# fetched and saved to disk. Nothing further is crawled.
#
# This is done by using a fetchlevel control of 2, a depth
# control of 0, and allowing images & stylesheets to skip
# constraints.

def apply_plugin():
    """ Apply the plugin - overrideable method """

    # This method is expected to perform the following steps.
    # 1. Register the required hook/plugin function
    # 2. Get the config object and set/override any required settings
    # 3. Print any informational messages.

    # The first step is required, the last two are of course optional
    # depending upon the required application of the plugin.

    cfg = objects.config
    # Set depth to 0
    cfg.depth = 0
    # Set fetchlevel to 2
    cfg.fetchlevel = 2
    # Images & stylesheets will skip rules
    cfg.skipruletypes = ['image','stylesheet']
    # One might have to set robots to 0
    # sometimes to fetch images - uncomment this
    # in such a case.
    # cfg.robots = 0
