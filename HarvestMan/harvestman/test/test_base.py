# -- coding: utf-8
""" Base module for unit tests

Created: Anand B Pillai <abpillai@gmail.com> Apr 17 2007

Copyright (C) 2007, Anand B Pillai.
"""

import sys, os

flag = False

def setUpPaths():
    """ Set up paths """

    f = globals()['__file__']
    parentdir = os.path.dirname(os.path.dirname(f))
    # Add modules in prev directory
    sys.path.append(parentdir)

def setUp():
    """ Set up """

    global flag
    if flag: return
    
    setUpPaths()

    from lib.common.common import SetAlias
    
    from lib import config
    SetAlias(config.HarvestManStateObject())

    from lib import datamgr
    from lib import rules
    from lib import connector
    from lib import urlqueue
    from lib import logger
    from lib import event

    SetAlias(logger.HarvestManLogger())
    
    # Data manager object
    dmgr = datamgr.HarvestManDataManager()
    dmgr.initialize()
    SetAlias(dmgr)
    
    # Rules checker object
    ruleschecker = rules.HarvestManRulesChecker()
    SetAlias(ruleschecker)
    
    # Connector manager object
    connmgr = connector.HarvestManNetworkConnector()
    SetAlias(connmgr)
    
    # Connector factory
    conn_factory = connector.HarvestManUrlConnectorFactory(5)
    SetAlias(conn_factory)
    
    queuemgr = urlqueue.HarvestManCrawlerQueue()
    SetAlias(queuemgr)
    
    SetAlias(event.HarvestManEvent())    

    flag = True
    
def clean_up():
    from lib.common.common import objects
    objects.datamgr.clean_up()
    
