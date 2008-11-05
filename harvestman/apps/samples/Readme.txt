This directory contains sample crawler applications which extend
HarvestMan and override events to produce specific crawling behavior.
Each of the module in this directory implement a custom crawler class
which inherits from the "HarvestMan" class.

o htmlcrawler.py:     An html-only crawler
o imagecrawler.py:    A crawler which downloads only images
o searchingcrawler.py : A crawler which searches a web-site for pages matching  
                      a keyword or a regular expression and downloads  them.
o taganalyzer.py :    A crawler which analyzes tags in HTML pages.
o indexingcrawler.py: A crawler which indexes downloaded pages using PyLucene.
o linkchecker.py    : A crawler which checks a site for broken links and
		      reports them.
o postingcrawler.py:  A specific application example. This crawler is custom
                      written to crawl monthly archives of the Bangalore Python
                      User's group (BangPypers), retrieve JOB postings and post
                      them automatically to the blog http://pythonjobs.blogspot.com .
               


