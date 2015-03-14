![http://harvestman.everythingability.com/chrome/common/banner.png](http://harvestman.everythingability.com/chrome/common/banner.png)
# First Time Usage #

When using HarvestMan you have two options of downloading pages/files. You can either use command line options or use config.xml file.

## Command Line Options ##
  * To get a list of commands, type:
```
harvestman --help
```
  * Here are some available choices:
```
Options:
  -h, --help            show this help message and exit
  -v, --version         Print version information and exit
  -m, --simulate        Simulates crawling with the given configuration,
                        without performing any actual downloads (same as "-g
                        simulator")
  -C CFGFILE, --configfile=CFGFILE
                        Read all options from the configuration file CFGFILE
  -P PROJFILE, --projectfile=PROJFILE
                        Load the project file PROJFILE
  -F URLFILE, --urlfile=URLFILE
                        Read a list of start URLs from file URLFILE and crawl
                        them
  -b BASEDIR, --basedir=BASEDIR
                        Set the (optional) base directory to BASEDIR
  -p PROJECT, --project=PROJECT
                        Set the (optional) project name to PROJECT
  -V LEVEL, --verbosity=LEVEL
                         Set the verbosity level to LEVEL. Ranges from 0-5,
                        default is 2
  -f LEVEL, --fetchlevel=LEVEL
                        Set the fetch-level of this project to LEVEL. Ranges
                        from 0-4, default is 0
  -l LOCALISE, --localise=LOCALISE
                        Localize urls after download (yes/no, default is yes)
  -r NUMRETRIES, --retry=NUMRETRIES
                        Set the number of retry attempts for failed urls to
                        NUMRETRIES
  -X PROXYSERVER, --proxy=PROXYSERVER
                        Enable and set proxy to PROXYSERVER (host:port)
  -U USERNAME, --proxyuser=USERNAME
                        Set username for proxy server to USERNAME
  -W PASSWORD, --proxypass=PASSWORD
                         Set password for proxy server to PASSWORD
  -n NUMCONNECTIONS, --connections=NUMCONNECTIONS
                        Limit number of simultaneous network connections to
                        NUMCONNECTIONS
  -c CACHE, --cache=CACHE
                        Enable/disable caching of downloaded files. If
                        enabled(default), files won't be saved unless their
                        timestamp is newer than the cache timestamp
  -d DEPTH, --depth=DEPTH
                        Set the limit on the depth of urls to DEPTH
  -w NUMWORKERS, --workers=NUMWORKERS
                        Enable worker threads and set the number of worker
                        threads to NUMWORKERS
  -T NUMTHREADS, --maxthreads=NUMTHREADS
                        Limit the number of tracker threads to NUMTHREADS
  -M NUMFILES, --maxfiles=NUMFILES
                        Limit the number of files downloaded to NUMFILES
  -t PERIOD, --timelimit=PERIOD
                        Run the program for the specified time period PERIOD
                        (in seconds)
  -s, --subdomain       If set, treats subdomains in the same parent domain
                        (like my.foo.com & his.foo.com) as the same
  -R ROBOTS, --robots=ROBOTS
                        Enable/disable Robot Exclusion Protocol and checking
                        of META ROBOTS tags.
  -u FILTER, --urlfilter=FILTER
                        Use regular expression FILTER for filtering urls
  -g PLUGINS, --plugins=PLUGINS
                        Load the set of plugins PLUGINS (Specified as
                        plugin1+plugin2+...)
  -o <name=value>, --option=<name=value>
                        Pass a configuration param using <name=value> syntax
  --ui                  Start HarvestMan in Web UI mode
  --genconfig           Create Configuration File Using GenConfig Web UI mode
  --selftest            Run a self test
```


## Config.xml Options ##
  * To create config.xml you can run our generate configuration program.
```
harvestman --genconfig
```
  * Fill all the information and when done save the xml to myconfig.xml and run the following command:
```
harvestman -C myconfig.xml
```
  * Here is how the web interface look.

---

![http://lucasmanual.com/out/harvestman.png](http://lucasmanual.com/out/harvestman.png)

---
