*************************
*                       *
* HarvestMan Webcrawler *
*                       *
*************************

About
-----

HarvestMan is a web crawler application and framework written entirely
in the Python programming language. It can be used as a small, personal
crawler to quickly download files from websites or as a crawler library
/framework which can be used to develop large scale crawling applications.

In this release, there are two applications. The regular crawler application
(HarvestMan) and a new multithreaded web downloader application ("Hget")
which is built on top of HarvestMan framework. This release also splits
the HarvestMan source code into a well-defined library and a set
of applications which make use of the library. 

NOTE: For more information on Hget, read Readme.hget .

Author
------

Author: Anand B Pillai <abpillai at gmail dot com>

License
-------

See the file LICENSE.TXT.

Version
--------
2.0.4 beta (HarvestMan)


WWW
---
http://harvestmanontheweb.com
http://harvestman-crawler.googlecode.com/

Requirements
------------

HarvestMan depends upon:
1.  python2.4 or higher. (python2.3 untested) (required)
2. python-dev package (required for sgmlop)
3. sgmlop,pyparsing,web.py which will get installed automatically as part of the installation. 

Getting started 
---------------

You need to get the sourcecode. You can either checkout the source code from our subversion repository or download the tar/zip file which has the source code. If you want to install from source code see our wiki page for the most current up to date installation instructions: http://code.google.com/p/harvestman-crawler/wiki/InstallHarvestMan

If you get the tar archive you need to do the following:

Unarchive the file to a directory of your choice. 

% tar -xjf HarvestMan-<version>.tar.bz2

where <version> is the version number.

Go into the directory. 

cd HarvestMan-<version>


How to Install
--------------
Make sure you are at the top-level HarvestMan directory. 

On POSIX systems (Unix, Linux)

% sudo python setup.py install

On Win32 systems

% python setup.py install

The install script will work on Windows based Unix emulation
layers such as cygwin also.

The install script installs the HarvestMan framework to
your system Python folder and creates shortcuts for the
HarvestMan and Hget applications.

Running the program(s)
---------------------
        
First thing to do is to test your application.

harvestman --sefltest

To run harvestman you need a configuration file. This
is named 'config.xml' by default. To pass a different
configuration file, use the command-line argument '-C'
or '--configfile'.

harvestman -C config.xml

To create your configuration file run

harvestman --genconfig

Your browser will open and you will be able to enter what sites you will want to crawl. Save that file as mycrawl.xml and start harvestman

harvestman -C mycrawl.xml


There is a sample config file incuded in the 'apps' directory if you just want to test it right away.

To run HarvestMan application, just type "harvestman" in a command
prompt.

$ harvestman
or
$ harvestman -h

If the program finds a configuration file in the current directory
or in the users .harvestman folder, it will start. If it does not
find these files the program will exit with an error. 

Command line mode
-----------------
HarvestMan supports command-line options.

For information on the command line options, run the program 
with the --help or -h option.

For a complete FAQ on the command line options, visit
http://www.harvstmanontheweb.com/commandline.html .

Project file mode
-----------------

HarvestMan writes a project file before it starts crawling websites.
This file has the extension '.hpf' and is written in the base 
directory of the project.

You can read this file back to restart the project later on. 

For this, use the --projectfile or '-P option and pass the project file
path as argument. This reruns a previously ran project.

The Config file
---------------

The config file provides the program with its settings.
It is an xml file with top-level elements and children.
Each top-level element denotes a section of HarvestMan
configuration. Each child element denotes either a minor
section or an actual configuration element.

Example:

      <project skip="0">
        <url>http://www.python.org/doc/current/tut/tut.html</url>
        <name>pytut</name>
        <basedir>D:/websites</basedir>
        <verbosity value="3"/>
      </project>

The new version of the config file separates config variables into
8 different sections(elements) as described below.

Section                       Description

1. project                    All project related variables
2. network                    All network related variables lik proxy,
                              proxy username/password etc.
3. download                   All download related variables (html/image/
                              stylesheets/cookies etc)
4. control                    All download control variables (filters/
                              maximum limits/timeouts/depths/robots.txt)
5. system                     Any system related variable( fastmode/thread status/
                              thread timeouts/thread pool size etc)
6. indexer                    All indexer related variables (localize etc)
7. files                      All harvestman file settings (config/message log/ 
                              error log/url list file etc) 
8.display                    Display (GUI/browser) related setting
  
HarvestMan accepts about 60 configuration options in total.

For a detailed discussion on the options, refer the HarvestMan 
documentation files in the 'doc' sub-directory or point your browser
to http://code.google.com/p/harvestman-crawler/wiki/ConfigXml

Python Dependencies
-------------------
The minimal requirement is Python 2.4 and the latest version of pyparsing.
HarvestMan should work on all platforms where Python is supported. Due to one of the subpackages we use Python-dev version is required.

More Documentation
------------------
Read the HarvestMan documentation in the 'doc' sub-directory for
more information. More information is also available in the project
web page.

Changes & Fix History
---------------------    
See the file Changes.txt.

Change Log for this Version
---------------------------
See the file ChangeLog.txt.


