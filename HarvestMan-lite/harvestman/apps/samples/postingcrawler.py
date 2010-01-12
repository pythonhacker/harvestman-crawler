#!/usr/bin/env python

"""
postingcrawler.py - Demonstrating custom crawler writing by
subscribing to events. This is a crawler which crawls
BangPyper archives, finds job postings and posts it to
a specific blog.

Created by Anand B Pillai <abpillai at gmail dot com> 

Copyright (C) 2008 Anand B Pillai
"""
import __init__
from harvestman.apps.spider import HarvestMan
from harvestman.lib.common.common import objects
from harvestman.lib import logger

import sys
import blogger
import getpass
import re
import cPickle

class JobPostingCrawler(HarvestMan):
    """ A job-posting crawler by integrating HarvestMan
    with the google blogger API """

    month_re = re.compile(r'\d{4}-\w+')

    def __init__(self):
        self.jobs = {}
        # Archive and post later
        self.archive = True
        super(JobPostingCrawler, self).__init__()

    def after_parse_cb(self, event, *args, **kwargs):
        
        document = event.document
        url = event.url

        if document:
            content = document.content.lower()
            title = document.title.lower()
            
            if title.find('job') != -1:
                # If this is a reply to an original job post, ignore it...
                data = document.content
                
                idx = data.find('Previous message:')
                if idx != -1:
                    idx2 = data.find('</A>', idx)
                    # print 'String=>',data[idx:idx2]
                    # print 'Title=>',document.title
                    if not data[idx:idx2].endswith(document.title):
                        self.jobs[document.title] = (url.get_full_url(), document.content)
                else:
                    self.jobs[document.title] = (url.get_full_url(), document.content)                    

    def finish_event_cb(self, event, *args, **kwargs):

        if len(self.jobs):
            print 'Found %d job postings' % len(self.jobs)
            if self.archive:
                # Archive the data as a pickled file
                # get base URL
                post_month = self.month_re.findall(objects.config.url)[0]
                fname = 'pythonjobs-%s' % post_month
                f = open(fname, 'wb')
                cPickle.dump(self.jobs, f)
                f.close()
                print 'Wrote jobs data to file %s.' % fname
                return
                
            go_ahead = raw_input("Go ahead with posting [y/n] ? ")
            if go_ahead.lower().strip() == 'y':
                print 'Logging to blogger...'
                username = raw_input("Enter username: ").strip()
                passwd = getpass.getpass("Enter password: ").strip()
                b = blogger.BlogJobPoster(username, passwd)
                print 'Successfully logged into blogger.'

                count = 0
                content = ''

                for title, (url,data) in self.jobs.items():
                    # Extract date from the text...
                    print data
                    go_ahead = raw_input("Post this JOB [y/n] ? ")
                    if go_ahead.lower().strip() != 'y': continue
                    
                    count += 1
                    date = data[data.find('<I>')+3:data.find('</I>')]
                    title += '(Posted on: %s)' % date
                    content = data[data.find('<PRE>')+5:data.find('</PRE>')] + '<br>\n'
                    # Wrap content to text width nicely
                    # content = wrap(content) + '<br>'

                    content += 'Referrering URL: <i><a href="%s">%s</a></i>\n' % (url, url)
                    content = '<P>' + content + '</P>'

                    print 'Posting job ID %d for %s' % (count, url)
                    b.post_job(title, content)
            else:
                print 'Found %d jobs, but did not post.' % len(self.jobs)
        else:
            print 'No job postings found!'

if __name__ == "__main__":
    spider=JobPostingCrawler()
    spider.initialize()
    config = spider.get_config()
    config.verbosity = logger.EXTRAINFO
    config.robots = 0
    config.localise = 0

    spider.register('post_parse_url', spider.after_parse_cb)
    spider.register('before_finish_project', spider.finish_event_cb)    
    spider.main()
