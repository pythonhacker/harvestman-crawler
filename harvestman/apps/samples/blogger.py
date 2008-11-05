"""
blogger.py - Job posting class using Google blogger API.

Created by Anand B Pillai <abpillai at gmail dot com> 28 May 2008

Copyright(C) 2008 Anand B Pillai.
"""

from gdata import service
import gdata
import atom
import getopt
import sys

class BlogJobPoster(object):
    """ Class which performs job posting to http://pythonjobs.blogspot.com """
    
    def __init__(self, email, password):
        # Authenticate using ClientLogin.
        self.service = service.GDataService(email, password)
        self.service.source = 'Blogger_Python_Sample-1.0'
        self.service.service = 'blogger'
        self.service.server = 'www.blogger.com'
        self.service.ProgrammaticLogin()
        self.blog_id = 0
        
        # Get the blog ID for http://pythonjobs.blogspot.com
        query = service.Query()
        query.feed = '/feeds/default/blogs'
        feed = self.service.Get(query.ToUri())
        
        for entry in feed.entry:
            # print "\t" + entry.title.text
            # print entry.link[0].href
            
            if entry.link[0].href=='http://pythonjobs.blogspot.com/':
                self_link = entry.GetSelfLink()
                self.blog_id = self_link.href.split('/')[-1]
                break

    def post_job(self, title, content):
        """ Post a job with given title and content """
        
        # Create the entry to insert.
        entry = gdata.GDataEntry()
        entry.author.append(atom.Author(atom.Name(text="Post Author")))
        entry.title = atom.Title(title_type='xhtml', text=title)
        entry.content = atom.Content(content_type='html', text=content)

        # Ask the service to insert the new entry.
        job_post = self.service.Post(entry, '/feeds/' + self.blog_id + '/posts/default')
        print "Successfully created post: \"" + job_post.title.text + "\".\n"

if __name__ == "__main__":
    pass


