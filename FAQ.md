## This is still a work under progress and has been lifted verbatim from the HarvestMan web-site with little or no modifications. A lot of information is out of date and needs to be updated. Also the FAQ doesn't confirm to wiki style, so proceed with care ! ##

HarvestMan - FAQ
Version 2.0
NOTE: The FAQ is being modified currently to be in sync with HarvestMan 1.4, so you might find that some parts of the FAQ are inconsistent with the rest of it. This is because some of the FAQ is modified, while the rest is still to be modified.

  * 1. Overview
> > o 1.1. What is HarvestMan?
> > o 1.2. Why do you call it HarvestMan?
> > o 1.3. What HarvestMan can be used for?
> > o 1.4. What HarvestMan cannot be used for...
> > o 1.5. What do I need to run HarvestMan?
  * 2. Usage
> > o 2.1. What is the HarvestMan Configuration File?
> > o 2.2. Can HarvestMan be run as a command-line application?
  * 3. Architecture
> > o 3.1.What are "tracker" threads and what is their function?
> > o 3.2.What are "crawler" threads?
> > o 3.3.What are "fetcher" threads?
> > o 3.4.How do the crawlers and fetchers co-operate?
> > o 3.5.How many different Queues of information flow are there?
> > o 3.6.What are worker (downloader) threads?
> > o 3.7.How does a HarvestMan project finish?
  * 4. Protocols & File Types
> > o 4.1. What are the protocols supported by HarvestMan?
> > o 4.2. What kind of files can be downloaded by HarvestMan?
> > o 4.3. Can HarvestMan run javascript code?
> > o 4.4. Can HarvestMan run java applets?
> > o 4.5. How to prevent downloading of HTML & CGI forms?
> > o 4.6. Does HarvestMan download dynamically generated cgi files (server-side) ?
> > o 4.7. How does HarvestMan determine the filetype of dynamically generated server side files?
> > o 4.8. Does HarvestMan obey the Robots Exclusion Protocol?
> > o 4.9. Can I restart a project to download links that failed (Caching Mechanism)?
  * 5. Network, Security & Access Rules
> > o 5.1. Can HarvestMan work across proxies?
> > o 5.2. Does HarvestMan support proxy authentication?
> > o 5.3. Does HarvestMan work inside an intranet?
> > o 5.4. Can HarvestMan crawl a site that requires HTTP authentication?
> > o 5.5. Can HarvestMan crawl a site that requires HTTPS(SSL) authentication?
> > o 5.6. Can I prevent the program from accessing specific domains?
> > o 5.7. Can I specify download filters to prevent download of certain files or directories on a server?
> > o 5.8. Is it possible to control the depth of traversal in a domain?
  * 6. Download Control - Basic
> > o 6.1. Can I set a limit on the maximum number of files that are downloaded?
> > o 6.2 .Can I set a limit on the number of external servers crawled?
> > o 6.3. Can I set a limit on the number of outside directories that are crawled?
> > o 6.4. How can I prevent download of images?
> > o 6.5. How can I prevent download of stylesheets?
> > o 6.6. How to disable traversal of external servers?
> > o 6.7. Can I specify a project timeout?
> > o 6.8. Can I specify a thread timeout for worker threads?
> > o 6.9. How to tell the program to retry failed links?
  * 7. Download Control - Advanced
> > o 7.1. What are fetchlevels and how can I use them?
  * 8. Application development & customization
> > o 8.1. I want to customize HarvestMan for a research project. Can you help out ?
> > o 8.2. I want to customize HarvestMan for a commercial project. Can you help out ?
  * 9. Diagrams
> > o 9.1. HarvestMan Class Diagram

1. Overview

1.1. What is HarvestMan?
HarvestMan (with a capital 'H' and a capital 'M') is a webcrawler program. HarvestMan belongs to a family of programs frequently addressed as webcrawlers, webbots, web-robots, offline browsers etc.

These programs are used to crawl a distributed network of computers like the Internet and download files locally.

1.2. Why do you call it HarvestMan?
The name "HarvestMan" is derived from a kind of small spider found in different parts of the world called "Daddy long legs" or Opiliones.

Since this program is a web-spider, the analogy was compelling to name it after some species of spiders. The process of downloading data from websites is sometimes called harvesting.

Both these similarities gave arise to the name HarvestMan.

1.3. What HarvestMan can be used for?
HarvestMan is a desktop tool for web search/data gathering. It works on the client side.

As of the recent version, HarvestMan can be used for,

  1. Downloading a website or a part of it.

> 2. Download certain files from a website (matching certain patterns)
> 3. Search a website for keywords & download the files containing them
> 4. Scan a website for links and download them specifically using filters.

1.4. What HarvestMan cannot be used for...
HarvestMan is a small-medium size web-crawler mostly intended for personal use or for use by a small group. It cannot be used for massive data harvesting from the web. However a project to create a large-scale, distributed web crawler based on HarvestMan is underway. It is calld 'Distributed HarvestMan' or 'D-HarvestMan' in short. D-HarvestMan is currently at a prototype stage.

Projects like EIAO has been able to customize HarvestMan for medium-large scale data gathering from the Internet. The EIAO project uses HarvestMan to download as much as 100,000 files from European websites daily.

What HarvestMan is not,

  1. HarvestMan is not an Internet search engine.
> 2. HarvestMan is not an indexer or taxonomy tool for web documents
> 3. HarvestMan is not a server-side program.

1.5. What do I need to run HarvestMan?
HarvestMan is written in a programming language called Python. Python is an interactive, interpreted, object-oriented programming language created by Guido Van Rossum and maintained by a team of volunteers from all over the world. Python is a very versatile language which can be used for a variety of tasks ranging from scripting to web frameworks to developing highly complex applications.

HarvestMan is written completely in Python. It works with Python version 2.3 upward on all platforms where Python runs. However, HarvestMan has some performance optimizations that require the latest version of Python which is Python 2.4. The suggested version is Python 2.4. Anyway, HarvestMan will also work with Python 2.3 too, but with reduced performance.

You need a machine with a rather large amount of RAM to run HarvestMan. HarvestMan tends to heavily use the system memory especially when performing large data downloads or when run with more than 10 threads. It is preferable to have a machine with 512 MB RAM and a fast CPU (Intel Pentium IV or higher) to run HarvestMan efficiently.

2. Usage

2.1. How do I run HarvestMan?
HarvestMan is a command-line application. It has no GUI.

From the 1.4 version, HarvestMan can be run by calling the main HarvestMan module as an executable script on the command-line as follows:


% harvestman.py


This will work, considering that you have edited your environment PATH variable to include the local HarvestMan installation directory on your machine. If you have not, you can run HarvestMan by running the harvestman.py module as an argument to the python interpreter, as follows:
% python harvestman.py


On Win32 systems, if you have associated the ".py" extension to the appropriate python.exe, you can run HarvestMan without invoking the interpreter explicitly.


Note that this assumes that you have a config file named config.xmlin the directory from where you invoke HarvestMan. If you dont have a config file locally, you need to use the command-line options of HarvestMan to pass a different configuration file to the program.
2.2. What is the HarvestMan Configuration (config) file?

The standard way to run HarvestMan is to run the program with no arguments, allowing it to pick up its configuration parameters from an XML configuration file which is named config.xml by default.

It is also possible to pass command-line options to HarvestMan. HarvestMan supports a limited set of command-line options which allow you to run the program without using a configuration file. You can learn more about the command-line options in the HarvestMan command-line options FAQ.
The HarvestMan configuration is an XML file with the configuration options split into different elements and their hieararchies. A typical HarvestMan configuration file looks as follows:


<?xml version="1.0" encoding="utf-8"?>

<!DOCTYPE HarvestMan SYSTEM "HarvestMan.dtd">


&lt;HarvestMan&gt;


> 

&lt;config version="3.0" xmlversion="1.0"&gt;


> > 

&lt;project&gt;


> > > 

&lt;url&gt;

http://www.python.org/doc/current/tut/tut.html

&lt;/url&gt;




> 

&lt;name&gt;

pytut

&lt;/name&gt;


> 

&lt;basedir&gt;

~/websites

&lt;/basedir&gt;


> 

&lt;verbosity value="3"/&gt;


> 

&lt;timeout value="600.0"/&gt;



> 

&lt;/project&gt;



> 

&lt;network&gt;


> > 

&lt;proxy&gt;


> > > 

&lt;proxyserver&gt;



&lt;/proxyserver&gt;


> > > 

&lt;proxyuser&gt;



&lt;/proxyuser&gt;




> 

&lt;proxypasswd&gt;



&lt;/proxypasswd&gt;


> 

&lt;proxyport value=""/&gt;


> 

&lt;/proxy&gt;


> 

&lt;urlserver status="0"&gt;


> > 

&lt;urlhost&gt;

localhost

&lt;/urlhost&gt;




> 

&lt;urlport value="3081"/&gt;


> 

&lt;/urlserver&gt;


> 

&lt;/network&gt;



> 

&lt;download&gt;


> > 

&lt;types&gt;




> 

&lt;html value="1"/&gt;


> 

&lt;images value="1"/&gt;


> 

&lt;javascript value="1"/&gt;


> 

&lt;javaapplet value="1"/&gt;



> 

&lt;forms value="0"/&gt;


> 

&lt;cookies value="1"/&gt;


> 

&lt;/types&gt;


> 

&lt;cache status="1"&gt;



> 

&lt;datacache value="1"/&gt;


> 

&lt;/cache&gt;


> 

&lt;misc&gt;


> > 

&lt;retries value="1"/&gt;


> > 

&lt;tidyhtml value="1"/&gt;




> 

&lt;/misc&gt;


> 

&lt;/download&gt;



> 

&lt;control&gt;


> > 

&lt;links&gt;


> > > 

&lt;imagelinks value="1"/&gt;




> 

&lt;stylesheetlinks value="1"/&gt;


> 

&lt;/links&gt;


> 

&lt;extent&gt;


> > 

&lt;fetchlevel value="0"/&gt;


> > 

&lt;extserverlinks value="0"/&gt;




> 

&lt;extpagelinks value="1"/&gt;


> 

&lt;depth value="10"/&gt;


> 

&lt;extdepth value="0"/&gt;


> 

&lt;subdomain value="0"/&gt;



> 

&lt;/extent&gt;


> 

&lt;limits&gt;


> > 

&lt;maxextservers value="0"/&gt;


> > 

&lt;maxextdirs value="0"/&gt;


> > 

&lt;maxfiles value="5000"/&gt;




> 

&lt;maxfilesize value="1048576"/&gt;


> 

&lt;connections value="5"/&gt;


> 

&lt;requests value="5"/&gt;


> 

&lt;timelimit value="-1"/&gt;



> 

&lt;/limits&gt;


> 

&lt;rules&gt;


> > 

&lt;robots value="1"/&gt;


> > 

&lt;urlpriority&gt;



&lt;/urlpriority&gt;


> > 

&lt;serverpriority&gt;



&lt;/serverpriority&gt;




> 

&lt;/rules&gt;


> 

&lt;filters&gt;


> > 

&lt;urlfilter&gt;



&lt;/urlfilter&gt;


> > 

&lt;serverfilter&gt;



&lt;/serverfilter&gt;


> > 

&lt;wordfilter&gt;



&lt;/wordfilter&gt;




> 

&lt;junkfilter value="0"/&gt;


> 

&lt;/filters&gt;


> 

&lt;/control&gt;



> 

&lt;system&gt;


> > 

&lt;workers status="1" size="10" timeout="200"/&gt;




> 

&lt;trackers value="4"/&gt;


> 

&lt;locale&gt;

american

&lt;/locale&gt;


> 

&lt;fastmode value="1"/&gt;


> 

&lt;/system&gt;



> 

&lt;files&gt;


> > 

&lt;urllistfile&gt;



&lt;/urllistfile&gt;


> > 

&lt;urltreefile&gt;



&lt;/urltreefile&gt;



> 

&lt;/files&gt;



> 

&lt;indexer&gt;



> 

&lt;localise value="2"/&gt;


> 

&lt;/indexer&gt;



> 

&lt;display&gt;


> > 

&lt;browsepage value="1"/&gt;




> 

&lt;/display&gt;



> 

&lt;/config&gt;





&lt;/HarvestMan&gt;




The current configuration file holds more than 60 configuration options. The variables that are essential to a project are project.url, project.name and project.basedir. These determine the identity of a HarvestMan crawl and normally require unique values for each HarvestMan project.

For a more detailed discussion on the config file, click here.

2.3. Can HarvestMan be run as a command-line application?
Yes, it can. For details on this, refer the Command line FAQ.
3. Architecture

3.1. HarvestMan is a multithreaded program. What is the threading architecture of HarvestMan ?
HarvestMan uses a multithreaded architecture. It assigns each thread with specific functions which help the program to complete the downloads at a relatively fast pace.

HarvestMan is a network-bound program. This means that most of the time for the program is spent in waiting for network connections, fetching network data and closing the connections. HarvestMan can be considered to be not IO-bound since we can assume that there is ample disk space for the downloads, at least in most common cases.

Whenever any program is network-boundor IO-bound, it helps to split the task to multiple threads of control, which perform their function without affecting other threads or the main thread.

HarvestMan uses this theory to create a multithreaded system of co-operating threads, most of which gather data from the network, processes the data and writes the files to the disk. These threads are calledtracker threads. The name is derived from the fact that the thread tracks a web-page, downloads its links and further tracks each of the pages pointed by the links, doing this recursively for each link.

HarvestMan uses a pre-emptive threaded architecture where trackers are launched when the program starts. They wait in turns for work, which is managed by a thread-safe Queueof data. Tracker threads post and retrieve data from the queue. These threads die only at the end of the program, spinning in a loop otherwise, looking for data.

There are two different kind of trackers, namely crawlers and fetchers.These are described in the sections below.
3.2. What are "crawler" threads?
Crawlersor crawler-threads are trackers which perform the specific function of  parsing a web-page. They parse the data from a web-page, extract the links, and post the links to a url queue.

The crawlers get their data from a dataqueue.


3.3. What are "fetcher" threads?
Fetchersor fetcher-threads are trackers which perform the function of "fetching", i.e downloading the files pointed to by urls. They download URLs which do not produce web-page content (HTML/XHTML) statically or dynamically. They download non-webpage URLs such as images, pdf files, zip files etc.

The fetchers get their data from the urlqueue and they post web-page data to the dataqueue.


3.4. How do the crawlers and fetchers co-operate?
The design of HarvestMan forces the crawlers and fetchers to be synergic. This is because, the crawlers obtain their data (web-page data) from the data queue, and post their results to the url queue. The fetchers in turn obtain their data (urls) from the url queue, and post their results to the data queue.

The program starts off by spawing the first thread which is a fetcher. It gets the web-page data for the starting page and posts it to the data queue. The first crawler in line gets this data, parses it and extracts the links, posting it to the url queue. The next fetcher thread waiting in the url queue gets this data, and the process repeats in a synergic manner, till the program runs out of urls to parse, when the project ends.

3.5. How many different Queues of information flow are there?
There are two queues of data flow, the url queue and the data queue.

The crawlers **feed the url queue and**feed-off the data queue.
The fetchers feed the data queue and feed-off the url queue.

**feed = post data to**feed-off = get data from


3.6. What are "worker" (downloader) threads?
Apart from the tracker threads, you can specify additional threads to take charge of downloading urls. The urls can be downloaded in these threads instead of consuming the time of the fetcher threads.

These threads are launched 'apriori', similar to the tracker threads, before the start of the crawl. By default, HarvestMan launches a set of 10 of these worker threads which are managed by a thread pool object. The fetcher threads delegate the actual job of downloading to the workers. However, if the worker threads are disabled, the fetchers will do the downloads themselves.

These threads also die only at the end of a HarvestMan crawl.

3.7. How does a HarvestMan project finish?
(Make sure that you have read items 3.1 - 3.6 before reading this.)

As mentioned before, HarvestMan works by the co-operation of crawler and fetcher family of tracker threads, each feeding on the data provided by the other.

A project nears its end when there are no more web-pages to crawl according to the configurations of the project. This means that the fetchers have less web-page data to fetch, which in-turn dries the data source for the crawlers. The crawlers in-turn go idle, thus posting less data to the url queue, which again dries the data source for the fetchers. The synergy works at this phase also, as it does when the project is active and all tracker threads are running.

After some time, all the tracker threads go idle, as there is no more data to feed from the queues. In the main thread of the HarvestMan program, there is a loop that spins continously checking for this event. Once all threads go idle, the loop detects it and exits; the project (and the program) comes to a halt.

HarvestMan main thread enters this loop immediately after spawning all the tracker threads and waits in the loop till. It checks for the idle condition every 1 or 2 seconds, spinning in a loop. Once it detects that all threads have gone idle, it ends the threads, performs post-download operations, cleanup etc and brings the program to an end.


4. Protocols & File Types

4.1. What are the protocols supported by HarvestMan?

HarvestMan supports the following protocols

  1. HTTP
> 2. FTP

Support for HTTPS (SSL) protocol depends on the Python version you are running. Python 2.3 version and later has HTTPS support built into Python, so HarvestMan will support the HTTPS protocol, if you are running it using Python 2.3 or higher versions.

The GOPHERand FILE://protocols should also work with HarvestMan.


4.2. What kind of files can be downloaded by HarvestMan?
HarvestMan can download **any** kind of file as long as it is served up by a web-server using HTTP/FTP/HTTPS. There are no restrictions on the type of file or the size of a single file.

HarvestMan assumes that the URLs with the following extension are web-pages, static or dynamic.

'.htm', '.html', '.shtm', '.shtml', '.php','.php3','.php4','.asp', '.aspx', '.jsp','.psp','.pl','.cgi', '.stx', '.cfm', '.cfml', '.cms'

The URL with no extension is also assumed to be a web-page. However, the program has a mechanism by which it looks at the URL headers of the HTTP request and figures out the actual file type of the URL by doing a mimetype analysis. This happens immediately after the HTTP request is answered by the server. So if the program finds that the assumed type of a URL is different from the actual type, it sets the type correctly at this point.

You can restrict download of certain files by creating specific filters for HarvestMan. These are described in a section somewhere below.

A related question is the html-tagssupported by HarvestMan using which it downloads files.
These are listed below.

  1. Hypertext links of the form<a href='http://www.foo.com/bar/file.html'> .<br>
</li></ul><blockquote>2. Image links of the form <img src='http://www.foo.com/bar/img.jpg'>  .<br>
3. Stylesheets of the form   <br>
<br>
<link rel="stylesheet" type="text/css" href="style.css"><br>
<br>
.<br>
4. Javascript source files of the form <br>
<br>
<script src="http://www.foo.com/scripts/script.js"><br>
<br>
 .<br>
5. Java applets(.class files) of the form<applet...>  .</blockquote>


4.3. Can HarvestMan run javascript code?
HarvestMan does not include a javascript engine. So it cannot run javascript code like Netscape or I.E. But Harvestman can parse javascript code and fetch javascript source files. (See answer to item 4.2 above.)


4.4. Can HarvestMan run java applets?
No. HarvestMan does not include a java runtime environment, so it cannot execute java applets. It does not make much sense in doing so too, since HarvestMan is an off-line browser and not a browser which can host a Java Runtime Environment.

But HarvestMan can download java applets (class files) by parsing the java applet tags inside web pages. (See answer to item 4.2 above).


4.5. How to prevent downloading of CGI and HTML forms?
From version 1.4, this is the default action. The program skips cgi form links and html forms, by looking for the query string of the form http://www.foo.com/bar/query.html?param=pby using regular expression matching. However, there is a way to make the program download CGI forms by enabling a configuration variable in the config file.

4.6. Does HarvestMan download dynamically generated server-side files ?
Yes. Server side files are generated during a regular client request to a web server which runs the server-side script (asp, jsp, php etc), and serves up the resulting file. Since this is like a regular HTTP request for HarvestMan, it downloads such files. However HarvestMan does not have a mechanism to prevent duplicate downloads of server-side files which generate the same content, but with different parameters to the server query. This could be added in a future version.


4.7. How does HarvestMan determine the file type of dynamically generated server side files (cgi)?
Since server-side requests can generate a wide variety of files and there is no way to find out the file type directly, adding logic to identify all such types is not an easy task.The current HarvestMan code contains logic to identify some files and it renames the files accordingly to match the extension of the particular type.

HarvestMan can identify GIF, BMP andJPEG image files by comparing the file signature with the standard signatures of these file types.

Since this is a rather errorprone approach, there is no guarantee it will work perfectly. Hence it is better not to rely on this feature if you are using HarvestMan.

4.8. Does HarvestMan obey the Robots Exclusion Protocol ?
Yes.

HarvestMan respects the rules laid down by website managers in the robots.txtrules in the web server. These rules specify certain limitations to crawling certain areas of the web site depending upon the user agent of the browser client. (Some site owners block entire sections to all clients).

HarvestMan obeys the robot exclusion protocol by default. There is way to bypass this protocol by disabling this feature. However, it is a good idea to always enable it to follow Internet etiquette and also to prevent yourself getting fined or sued by website owners for not following the robots.txt rules.

Support for robots.txt rules is available in Python. HarvestMan uses a customised form of this module.


4.9. Can I restart a project to download only links that failed in a previous run (web-page caching)?
Yes. You can, since HarvestMan has an inbuilt caching mechanism for documents downloaded from the network.

From version 1.2, the caching mechanism is available and enabled by default. HarvestMan uses an MD5 checksum< of the data of a downloaded file to create a unique  signature for each file.  This is associated with the url location of that file (in the Internet or the LAN) and written to a cache file. This signature is generated for every file downloaded in a project and the data written to a compressed cache file in the disk. You can locate this file in the directory named hm-cache in the HarvestMan project directory.

When you re-start a project, HarvestMan loads the cache information for the project, if it exists. When it encounters a url, it compares the signature of the url data with the signature of the cache url and verifies if it is the same. If it is the same, the document has not changed, so HarvestMan skips this url. Otherwise it downloads it.

The cache is regenerated at the end of every project. HarvestMan catches any keyboard interrupts by the user and makes sure that the cache is generated if the user decides to end the program by sending a keyboard interrupt, thereby making sure that precious network bandwidth is not wasted.

You can disable web-page caching by disabling a configuration variable in HarvestMan configuration file.
5 . Network, Security & Access Rules

5.1. Can HarvestMan work across proxies?
Yes. HarvestMan can work transparently across proxy servers and firewalls.

HarvestMan supports proxies and firewalls by the following config variables in the config file
and their command-line counteparts.

> o proxyserver:               This is the name or ip of the proxy server
> o proxyport:                   This is the port to which the proxy listens for requests.
> o proxyuser:                  Username for proxy authentication, if any.
> o proxypasswd:              Password for proxy authentication, if any.

These variables are child elements of the top-level XML element network inside HarvestMan configuration file. The proxy handling is built into Python.

Note that if you use the config file generation script (in the HarvestMan site or the one included in the distribution), the proxy variables are encrypted to prevent misuse of the information by a third-party.


5.2. Does HarvestMan support proxy authentication?
Yes. HarvestMan can work with both authenticated and regular (unauthenticated) proxies and firewalls. For details, see answer to item 5.1 above.


5.3. Does HarvestMan work inside an Intranet?
Yes. HarvestMan can crawl servers inside intranets or LANs as long as HarvestMan is able to resolve the name of the intranet server. This typically requires that there is a DNS server somewhere in the intranet which performs the resolving for clients. If you dont have such a DNS server, you might need to provide this information locally on the machine, by editing the local hosts file in your machine.

HarvestMan makes no difference between Internet and Intranet crawling. This was not so in earlier versions. However from the 1.4 version, all servers are treated uniformly irrespective of whether they are part of the local intranet or the Internet.

5.4. Can HarvestMan crawl a site that requires HTTP authentication?
Currently, no. This feature is enabled in the code, but is not exposed since it is not working perfectly.


5.5. Can HarvestMan crawl a site that requires HTTPS authentication?
No. This is not possible with the current HarvestMan. This feature is targeted for a future release.
5.6. Can I prevent the program from accessing specific domains?
> This is possible by the use of specific domain filters.

HarvestMan provides a filtering mechanism by which certain areas of a network or the Internet can be specified out-of-bounds to the program. This is possible by the use
of a server filter.
The config variable serverfilter inside the top-level control element can be set to a pattern of string in this manner.

1. Prefix a server name with the minus sign to specify it as out of bounds to the program. HarvestMan will skip such domains.
2. Prefix a server name with the plus sign to specify that it can be crawled.

For example to prevent the server named server1.foo.com in the foo.com domain from
being crawled, set control.serverfilter to the following pattern.

control.serverfilter               -server1.foo.com

If you want skip certain areas of a website or prevent downloading certain kinds of files, you should use the urlfilter , described below.

5.7. Can I specify download filters to prevent download of certain files or directories on a server?
HarvestMan uses the urlfilter mechanism to make this possible.

You can specify a urlfilter as the config variable named urlfitler of the top-level control element to do this. The rules for creating urlfilters are similar to any other filter.

1. Prefix an area or pattern to be skipped with the minus sign.
2. Prefix an area or pattern to be included with the plus sign.

For example, to prevent the program from downloading gif files, you can use the following pattern.

control.urlfilter              -**.gif**

To create a sequence of filters, chain them one after the other.

For example, to prevent the download of microsoft word, excel and powerpoint files, use the following pattern.

control.urlfilter             -**.doc-**.xls-**.ppt**

You can use this mechanism to prevent the program from accessing specific directories also.

For example, to prevent the program from crawling the directory named "images" in the server foo.com, use the following pattern.

control.urlfilter            -foo.com/images/

You can modify the above rule to allow the program to download all files except gif images from the same directory, as follows.

control.urlfilter           -foo.com/images/**.gif**

To specify traversal rules for certain directories and their subdirectories, you can use the following pattern.

For example, you want to allow acces to the sub-directory named "public" inside the directory named "images" in foo.com server, but prevent access to all other sub-directories and files.

The following urlfilter pattern does the trick.

control.urlfilter          -foo.com/images/**+foo.com/images/public**

The urlfilter pattern always takes precedence over the server filter pattern.


5.8. Is it possible to specify the depth of traversal in a domain?

Yes, it is possible.

HarvestMan provides two configuration variables for specifying the maximum depth of
traversal in a web server. The depth of a directory is calculated from the root of the
web server.

For example, the directory named http://www.foo.com/images/public/  has a depth
of two from the server root directory.

HarvestMan provides the variable depth inside the top-level element control to control the depth of traversal in the starting server, and the variable extdepth in the top-level control element to control the depth of traversal in external servers.

The difference between both control options is that, for the starting server, depth of a directory is calculated with respect to the starting url's directory, whereas for external servers, it is calculated with respect to its root.

For example, if the starting url is http://www.foo.com/images/public/index.html,
and if control.depth is set to 2, the images in the directory named http://www.foo.com/images/public/picnic/hawaii
will be fetched since the depth of this directory with respect to the directory of the starting url is 2.

For the same url, if control.extdepth is set to 2, the images in the directory named http://www.foo2.com/images/public/picnic/hawaii will not be fetched, since it is an external server, and the depth of this directory w.r.t the root of its server is more than
2.

By default the value for control.depth is 10, and for control.extdepth is 0. This means that only the files in the root directory of external servers is fetched by default.


6. Download Control

6.1. Can I set a limit on the maximum number of files that are downloaded?
Yes. Use the config option named maxfiles inside the top-level control element for this. By default this is set to 5000.

When the number of downloaded files exceed this value, HarvestMan automatically kills all threads and terminates the projects. It might also do some deletion of already downloaded files to stick to this limit. You can get very good accuracy for this limit, with an average error of +/- 1.5 files.


6.2. Can I set a limit on the number of external servers crawled?
Yes. The config variable named maxextservers inside the top-level control element for this.

There is a variable named fetchlevel which supersedes this. Typically, you wont be setting the external server option directly, instead using fetchlevels to configure your download extents. This variable is explained in a different section of the FAQ.


6.3. Can I set a limit on the number of outside directories that are crawled?
Yes. The config variable named maxextdirs inside the top-level control element that helps to do this.

External directories are directory paths in the starting server, but outside the path of the directory of the starting url.

Again, the fetchlevel setting supersedes this, so you can crawl external directories by setting appropriate fetch levels. Typically you wont be using the external directory setting directly, instead using fetchlevel to control the option indirectly.



6.4. How can I prevent the download of images?
You can do this by setting the config variable named images inside the top-level download element to zero.


6.5. How can I prevent the download of stylesheets?
You can do this by setting the config variable named stylesheets inside the top-level download element to zero.


6.6. How do I disable the traversal of external servers?
By setting the config variable named extserverlinks inside the top-level control element to zero.

Note that the fetchlevel  setting supersedes this setting also. Typically, this setting is also not congfigured directly but instead controlled through fetchlevel.

6.7. Can I specify a project timeout?
> Yes you can.

A HarvestMan project can hang due to many reasons. Problems in the network, memory crunch situations, threads hogging the CPU, insufficient thread context switching are some of these. Most of the times this happens when the threads will be running but unable to do any actual work.

In such cases, the program has a mechanism to time-out the project, by monitoring the last time a thread got some useful data or finished a download, and comparing it with the current time. If the main thread of the program is running fine, it will monitor this period and timeout the project, if it exceeds a certain value which is hard-coded into the program. This is about 300 seconds (5 minutes).


6.8. Can I specify a thread timeout for worker threads?
Yes. (The worker threads are described above in section 3.8)

Worker threads are normally given the charge of downloading files that are not web-pages. These threads can block sometimes because the server is busy, or if the connection socket blocks due to a number of other reasons (network errors, hardware problems, denial of service attacks etc).

In such cases, HarvestMan ensures that the thread does not hang infinitely by providing a thread timeout mechanism. This is controlled by the config variable named timeout which is an attribute of the worker element inside the top-level system element of the config file. The value of this is 200 seconds by default.
If a thread takes more time than this to download a file, HarvestMan terminates the thread and cleans it up.

If you are crawling a website with a lot of traffic and/or huge files, it is a good idea to set this to a higher value to give the download threads more time to complete their downloads.


6.9. How to tell the program to retry failed links?
You can do this by editing the config variable named retries inside the top-level download element.

Downloads can fail due to a variety of reasons. File not found errors (HTTP 404), server busy, socket failure etc are some of those. HarvestMan can attempt to re-download failed files by attempting the downloads again.

This is controlled by the above mentioned variable. If it is set to zero, the program does not attempt to re-download failed links. If it is set to a value more than zero, HarvestMan will attempt to download links that failed with non-fatal errors
(Non-fatal errors are errors like socket failure, network busy, server error etc, whereas fatal errors are errors like "File not found") , by a count specified by this variable. Also, HarvestMan will attempt to re-download failed links once more at the end of the project.

For example if this variable is set to 2, 2  retry attempts will be made to download a link that failed with a non-fatal error.


7. Download Control - Advanced

7.1. What are fetchlevels and how can I use them?

Fetchlevels are the most useful download tweaking feature of HarvestMan. It is important to understand them in order to tweak your downloads.

HarvestMan defines five fetchlevels with values ranging from 0 - 4 inclusive. These define the rules for the download of files in different servers other the server of the starting URL.

In general increasing a fetch level allows the program to crawl more files on the Internet.

A fetchlevel of "0" provides the maximum constraint for the download. This limits the download of files to all paths in the starting server, only inside and below the directory of the starting URL.

For example, with a fetchlevel of zero, if you starting url is http://www.foo.com/bar/images/images.html, the program will download only those files inside the 

&lt;images&gt;

 sub-directory and directories below it, and no other file.

The next level, a fetch level of "1", again limits the download to the starting server (and sub-domains in it, if the sub-domain variable is not set), but does not allow it to crawl sites other than the starting server. In the above example, this will fetch all links in the server http://www.foo.com, encountered in the starting page.

A fetch level of "2" performs a fetching of all links in the starting server encountered in the starting URL, as well as any links in outside (external) servers linked directly from pages in the starting server. It does not allow the program to crawl pages linked further away, i.e the second-level links linked from the external servers.

A fetch level of "3", performs a similar operation with the main difference that it acts like a combination of fetchlevels "0" and "2" minus "1". That is, it gets all links under the directory of the starting URL and first level external links, but does not fetch links outside the directory of the starting URL.

A fetch level of "4" gives the user no control over the levels of fetching, and the program will crawl whichever link is available to it unless not limited by other download control options like depth control, domain filters ,url filters, file limits, maximum server limit etc.

In short we can summarize the above rules in the following download guidelines.

  1. If you just want to download all links directly below the directory of starting URL, use a fetch level of zero.
> 2. If you want to download all links linked to the starting url in the same server, use a fetch level of one.
> 3. If you want to download all links directly below the starting url, and also first level links linked to other websites, use a fetch level of three.
> 4. If you want to download all links linked to the starting url in the same server, and also first level links linked to other websites, use a fetch level of two.
> 5. If you dont want to prescribe any limits, set a fetch level of four and tweak other download control options like depth fetching, file limits etc.But since this will lead to to large scale downloads from different servers on the Web, you should think of using a distributed crawler such as D-HarvestMan.


8. Application development and Customization

8.1. I want to customize HarvestMan for a research project. Can you help out ?

HarvestMan is made available under the GPL license, so you are free to download the latest source code tar ball and customize it the way you want, for your research project.

If you belong to a research group which wants to use HarvestMan as a component of your software, I am happy to provide informal support as long as it is now and then. If you want regular support and also some customization, I am available for consulting, support and customization at regular offshore software consulting rates in India.
8.2. I want to customize HarvestMan for a commercial project. Can you help out ?

If you want to write a commercial webcrawler application or solution on top of HarvestMan I am available for consulting. You can contact me at my email address.

9. UML Diagrams

9.1. HarvestMan Class Diagram

I have generated a UML object diagram using the Dot toolkit of AT&T graphviz project and the PyUMLGraph utility. The diagram is available here (size 350 KB).