# -- coding: utf-8
"""
jsdom.py - Defines classes for Javascript DOM objects.
This module is part of the HarvestMan program.For licensing
information see the file LICENSE.txt that is included in this
distribution.

Created Anand B Pillai <abpillai at gmail dot com> Oct 2 2007

Copyright (C) 2007 Anand B Pillai.

"""

class Base(object):
    """ Base class for DOM objects """

    __slots__ = []

    def __init__(self):
        for item in self.__class__.__slots__:
            setattr(self, item, None)
        
class Window(Base):
    """ DOM class which mimics a browser Window """
    
    __slots__ = ['frames','closed','defaultStatus','document',
                 'history','length','location','name','opener',
                 'outerheight','outerwidth','pageXOffset','pageYOffset',
                 'parent','personalbar','scrollbars','status','toolbar',
                 'top']

    def __init__(self):
        super(Window, self).__init__()

class Location(Base):
    """ DOM class for page location """
    
    __slots__ = ['hash','host','hostname','href','pathname','port',
                 'protocol','search','hrefchanged']

    def __init__(self):
        super(Location, self).__init__()
        # Internal flag
        self.hrefchanged = False

    def replace(self, url):
        self.href =  url
        self.hrefchanged = True

    def assign(self, url):
        self.replace(url)
                 
class Document(Base):
    """ DOM class for the document """
    
    __slots__ = ['body','cookie','domain','lastModified','referrer',
                 'title','URL', 'content', 'domcontent', 'prescript',
                 'postscript','contentchanged']
    
    def __init__(self):
        super(Document, self).__init__()
        self.content = ''
        self.domcontent = ''
        # Text before <script...> tags
        self.prescript = ''
        # Text after </script>..
        self.postscript = ''
        # Internal flag
        self.contentchanged = False
        
    def chomp(self, start, end):
        """ Split content according to start and end of javascript tags """

        # All content before <script...>
        self.prescript = self.content[:start]
        # All content after </script>        
        self.postscript = self.content[end:]
        
    def write(self, text):
        # Called for document.write(...) actions
        self.domcontent = self.domcontent + text

    def writeln(self, text):
        # Called for document.writeln(...) actions        
        self.domcontent = self.domcontent + text + '\n'

    def construct(self):
        """ Reconstruct document content using modified DOM """
        
        self.contentchanged = True
        self.content = ''.join((self.prescript, self.domcontent, self.postscript))

    def __repr__(self):
        return self.content
