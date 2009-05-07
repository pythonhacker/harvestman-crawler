# -- coding: utf-8
""" Base module for unit tests

Created: Anand B Pillai <abpillai@gmail.com> Apr 17 2007

Copyright (C) 2007, Anand B Pillai.
"""

import sys, os
import unittest

flag = False

def setUpPaths():
    """ Set up paths """

    f = globals()['__file__']
    parentdir = os.path.dirname(os.path.dirname(f))
    sys.path.append(os.path.dirname(parentdir))

def setUp():
    """ Set up """

    global flag
    if flag: return
    
    setUpPaths()

    from harvestman.lib.common.common import SetAlias
    
    from harvestman.lib import config
    cfg = config.HarvestManStateObject()
    # Enable testing flag
    cfg.testing = 1
    
    SetAlias(cfg)

    from harvestman.lib import datamgr
    from harvestman.lib import rules
    from harvestman.lib import connector
    from harvestman.lib import urlqueue
    from harvestman.lib import logger
    from harvestman.lib import event

    log=logger.HarvestManLogger()
    log.make_logger()
    SetAlias(log)
    
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
    from harvestman.lib.common.common import objects
    objects.datamgr.clean_up()

def run_test(testklass, result):
    suite = unittest.makeSuite(testklass)
    return suite.run(result)
