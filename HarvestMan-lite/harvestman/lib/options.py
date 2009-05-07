# -- coding: utf-8
""" options.py - Module keeping a list of command-line
options for HarvestMan. 

This module is part of the HarvestMan program.
For licensing information see the file LICENSE.txt that
is included in this distribution.

Author: Anand B Pillai <abpillai at gmail dot com>

Created Anand B Pillai - Feb 11 2007.

Copyright (C) 2007 Anand B Pillai
"""

hman_options=\
[ ('version', 'short=v','long=version','help=Print version information and exit', 'type=bool'),
  ('simulate', 'short=m','long=simulate','help=Simulates crawling with the given configuration, without performing any actual downloads (same as "-g simulator")','type=bool'),
  ('configfile', 'short=C','long=configfile','help=Read all options from the configuration file CFGFILE','meta=CFGFILE'),
  ('projectfile', 'short=P','long=projectfile','help=Load the project file PROJFILE','meta=PROJFILE'),
  ('urllist', 'short=F','long=urlfile',"help=Read a list of start URLs from file URLFILE and crawl them","meta=URLFILE"),  
  ('basedir', 'short=b','long=basedir','help=Set the (optional) base directory to BASEDIR','meta=BASEDIR'),
  ('project', 'short=p','long=project','help=Set the (optional) project name to PROJECT', 'meta=PROJECT'),
  ('verbosity', 'short=V','long=verbosity','help= Set the verbosity level to LEVEL. Ranges from 0-5, default is 2','meta=LEVEL'),
  ('fetchlevel', 'short=f','long=fetchlevel','help=Set the fetch-level of this project to LEVEL. Ranges from 0-4, default is 0','meta=LEVEL'),
  ('localise', 'short=l','long=localise','help=Localize urls after download (yes/no, default is yes)'),
  ('retries', 'short=r','long=retry','help=Set the number of retry attempts for failed urls to NUMRETRIES','meta=NUMRETRIES'),
  ('proxy', 'short=X','long=proxy','help=Enable and set proxy to PROXYSERVER (host:port)','meta=PROXYSERVER'),
  ('proxyuser', 'short=U','long=proxyuser','help=Set username for proxy server to USERNAME','meta=USERNAME'),
  ('proxypasswd', 'short=W','long=proxypass','help= Set password for proxy server to PASSWORD','meta=PASSWORD'),
  ('connections', 'short=n','long=connections','help=Limit number of simultaneous network connections to NUMCONNECTIONS','meta=NUMCONNECTIONS'),
  ('cache', 'short=c','long=cache',"help=Enable/disable caching of downloaded files. If enabled(default), files won't be saved unless their timestamp is newer than the cache timestamp"),
  ('depth', 'short=d','long=depth','help=Set the limit on the depth of urls to DEPTH','meta=DEPTH'),
  ('workers', 'short=w','long=workers','help=Enable worker threads and set the number of worker threads to NUMWORKERS','meta=NUMWORKERS'),
  ('maxthreads', 'short=T','long=maxthreads','help=Limit the number of tracker threads to NUMTHREADS','meta=NUMTHREADS'),
  ('maxfiles', 'short=M','long=maxfiles','help=Limit the number of files downloaded to NUMFILES','meta=NUMFILES'),
  ('timelimit', 'short=t','long=timelimit','help=Run the program for the specified time period PERIOD (in seconds)','meta=PERIOD'),
  ('subdomain','short=s','long=subdomain','help=If set, treats subdomains in the same parent domain (like my.foo.com & his.foo.com) as the same','type=bool','default=False','meta=SUBDOMAIN'),
#  ('savesessions', 'short=S','long=savesessions','help=Enable/disable session saver feature. If enabled(default), crashed sessions are automatically saved to disk and the program gives you the option of resuming them next time'),
  ('robots', 'short=R','long=robots','help=Enable/disable Robot Exclusion Protocol and checking of META ROBOTS tags.'),
  ('urlfilter', 'short=u','long=urlfilter','help=Use regular expression FILTER for filtering urls','meta=FILTER'),
  ('plugins', 'short=g','long=plugins',"help=Load the set of plugins PLUGINS (Specified as plugin1+plugin2+...)",'meta=PLUGINS'),
  ('option','short=o','long=option','meta=<name=value>','help=Pass a configuration param using <name=value> syntax'),
  ('ui','long=ui','help=Start HarvestMan in Web UI mode','meta=UI','type=bool','default=False'),
  ('genconfig','long=genconfig','help=Create Configuration File Using GenConfig Web UI mode','meta=genconfig','type=bool','default=False'),
  ('selftest','long=selftest','help=Run a self test','meta=SELFTEST','type=bool','default=False')]

def getOptList(appname):
    """ Return the list of options """

    return hman_options

if __name__=="__main__":
    print getOptList()
