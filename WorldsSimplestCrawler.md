## World's Simplest Crawler - Crawling the Web from Python prompt with HarvestMan ##

Once you install HarvestMan, it is very easy to do a quick crawl
of a web-site or URL from the Python interpreter prompt. This page
explains how.

At the very first, make sure you have installed HarvestMan to
Python. Check InstallHarvestMan for a guide to this.

Once you have done so, here are the rest of the steps.

---

First start up Python.

```
[anand@localhost ~]$ python
Python 2.5.1 (r251:54863, Jul 17 2008, 13:21:31) 
[GCC 4.3.1 20080708 (Red Hat 4.3.1-4)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Now, import the HarvestMan application.
```
>>> from harvestman.apps.spider import HarvestMan
```

Next, create an instance of the crawler class.
```
>>> spider = HarvestMan()
```

Initialize the instance. (This has to be done explicitly when running the crawler like this on the interactive prompt).
```
>>> spider.init()
```

Now, get the configuration of the crawler. This is done by the "get\_config" method.
(The config object is an instance of _harvestman.lib.config.HarvestManStateObject).
```
>>> cfg = spider.get_config()
>>> type(cfg)
<class 'harvestman.lib.config.HarvestManStateObject'>
```_

The config object defines an _add_ method to add URLs as projects to it directly. The method is as follows.
```
>>> help(cfg.add)
Help on method add in module harvestman.lib.config:

add(self, url, name='', basedir='.', verbosity=20) method of harvestman.lib.config.HarvestManStateObject in
stance
    Adds a crawl project to the crawler. The arguments
    are the starting URL, and optional name for the project,
    a base directory for saving files and project verbosity
```

So, let us add a project with starting URL _http://docs.python.org/tutorial/index.html_ with the name _pytut_. Let us save the files to _$HOME/websites_.

```
>>> cfg.add(url='http://docs.python.org/tutorial/index.html',name='pytut',basedir='~/websites')
```

_(Of course, the name in front of the arguments are not necessary. But it has been added to clarify what each argument stands for)_.

Finally, we need to setup the configuration object and call the _main_ method on the crawler.

```
>>> cfg.setup()
>>> spider.main()
```

That is it! The crawl starts immediately in the Python command line!

```
>>> spider.main()
[]
Starting HarvestMan 2.0 alpha 1... 
Copyright (C) 2004, Anand B Pillai 
  
[17:34:25] *** Log Started ***
 
[17:34:25] Starting project pytut ...
[17:34:25] Writing Project Files... 
[17:34:25] Starting download of url http://docs.python.org/tutorial/index.html ...
[17:34:25] Reading Project Cache... 
[17:34:25] Project cache not found 
[17:34:25] Downloading file for url http://docs.python.org/tutorial/index.html
[17:34:27] Saved to /home/anand/websites/pytut/docs.python.org/tutorial/index.html
[17:34:28] Fetching links for url http://docs.python.org/tutorial/index.html
[17:34:28] Not Found =>  http://docs.python.org/robots.txt
[17:34:29] Downloading file for url http://docs.python.org/tutorial/stdlib2.html
[17:34:29] Downloading file for url http://docs.python.org/tutorial/interpreter.html
...
```

Ain't that cool. So summarizing the steps, the world's simplest (and coolest!) crawl can be done right in the Python command line with the following  steps.

```
>>> from harvestman.apps.spider import HarvestMan
>>> spider = HarvestMan()
>>> spider.init()
>>> cfg = spider.get_config()
>>> cfg.add(url='http://docs.python.org/tutorial/index.html',name='pytut',basedir='~/websites')
>>> cfg.setup()
>>> spider.main()
```

That is about 6 lines of code excluding the import line. Guess it does not get simpler than that ;)

Now, what if you want to re-crawl the same site. Ok, let us try the
same crawl again.

```
>>> spider.main()
[]
Starting HarvestMan 2.0 alpha 1... 
Copyright (C) 2004, Anand B Pillai 
  
[17:38:37] *** Log Started ***
 
Traceback (most recent call last):
  File "/usr/lib64/python2.5/logging/__init__.py", line 750, in emit
    self.stream.write(fs % msg)
ValueError: I/O operation on closed file
[17:38:37] Starting project pytut ...
Traceback (most recent call last):
  File "/usr/lib64/python2.5/logging/__init__.py", line 750, in emit
    self.stream.write(fs % msg)
ValueError: I/O operation on closed file
...
```

Oops, something has gone wrong!

The problem is that the crawler state has to be reset, before you attempt to recrawl again using the same instance of the crawler. This is automatically done if you run the
program non-interactively, but in the interactive prompt, this has to be done manually.

But there is no problem, since it just boils down to a single line of code...!

```
>>> spider.reset()   
```

That is it! This resets the state, so now you can crawl to your heart's content :)

Let us crawl again...

```
>>> spider.main()
[]
Starting HarvestMan 2.0 alpha 1... 
Copyright (C) 2004, Anand B Pillai 
  
[17:41:01] *** Log Started ***
 
[17:41:01] Starting project pytut ...
[17:41:01] Writing Project Files... 
[17:41:01] Starting download of url http://docs.python.org/tutorial/index.html ...
[17:41:01] Reading Project Cache... 
[17:41:01] Downloading file for url http://docs.python.org/tutorial/index.html
...
```


Watch this space. More cool tutorials are coming on custom crawling the web with
HarvestMan!


**NOTE: This works only with the most recent trunk code (since Oct 6 2008), as
the code referencing the application classes have changed in the last few days.**


---

_Please send your feedbacks regarding this tutorial to the project owner(s)_.