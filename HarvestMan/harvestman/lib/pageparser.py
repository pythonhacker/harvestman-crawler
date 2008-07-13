# -- coding: utf-8
""" pageparser.py - Module to parse an html page and
    extract its links. This module is part of the
    HarvestMan program.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Modification History
    ====================


   Jan 2007       Anand              Complete support for META robot tags implemented.
                                     Requested by jim sloan of MCHS.
   Mar 06 2007    Anand              Added support for HTML EMBED & OBJECT tags.
   Apr 18 2007    Anand              Made to use the urltypes module.
   Apr 19 2007    Anand              Created class HarvestManCSSParser to take
                                     care of parsing stylesheet content to extract
                                     URLs.
   Aug 28 2007    Anand              Added a parser baed on Effbot's sgmlop
                                     to parse pages with errors - as a part of
                                     fixes for #491.
   Sep 05 2007    Anand              Added a basic javascript parser to parse
                                     Javascript statements - currently this can
                                     perform Javascript based site redirection.
   Sep 10 2007    Anand              Added logic to filter junk links produced
                                     by web-directory pages.
   Oct 3  2007    Anand              Removed class HarvestManJSParser since its
                                     functionality and additional DOM processing
                                     is done by the new JSParser class.

   Apr 4 2008     Anand              Fix for EIAO bug #812.
   Apr 6 2008     Anand              Added ParseTag class and features for EIAO bug
                                     #808.
   
   
  Copyright (C) 2004 Anand B Pillai.                                     
                                     
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

from sgmllib import SGMLParser
from urltypes import *
from common.common import *
from common.macros import *

import re

class ParseTag(object):
    """ Class representing a tag which is parsed by the HTML parser(s) """
    
    def __init__(self, tag, tagdict, pattern=None, enabled=True):
        # Tag is the name of the tag (element) which will be parsed.
        # Tagdict is a dictionary which contains the attributes
        # of the tag which we are interested as keys and the type
        # of URL the value of the attribute will be saved as, as
        # the value. If there are more than one type of URL for this
        # attribute key, then the value is a list.
        
        # For example valid tagdicts are {'href': [URL_TYPE_ANY, URL_TYPE_ANCHOR] },
        # {'codebase': URL_TYPE_JAPPLET_CODEBASE, 'code': URL_TYPE_JAPPLET'}.
        self.tag = tag
        self.tagdict = tagdict
        self.enabled = enabled
        self.pattern = pattern

    def disable(self):
        """ Disable parsing of this tag """
        self.enabled = False

    def enable(self):
        """ Enable parsing of this tag """
        self.enabled = True

    def isEnabled(self):
        """ Is this tag enabled ? """
        
        return self.enabled

    def setPattern(self, pattern):
        self.pattern = pattern

    def __eq__(self, item):
        return self.tag.lower() == item.lower()
    
class HarvestManSimpleParser(SGMLParser):
    """ An HTML/XHTML parser derived from SGMLParser """

    # query_re = re.compile(r'[-.:_a-zA-Z0-9]*\?[-.:_a-zA-Z0-9]*=[-.a:_-zA-Z0-9]*', re.UNICODE)
    # A more lenient form of query regular expression
    query_re = re.compile(r'([^&=\?]*\?)([^&=\?]*=[^&=\?])*', re.UNICODE) 
    skip_re = re.compile(r'(javascript:)|(mailto:)|(news:)')
    # Junk URLs obtained by parsing HTML of web-directory pages
    # i.e pages with title "Index of...". The filtering is done after
    # looking at the title of the page.
    index_page_re = re.compile(r'(\?[a-zA-Z0-9]=[a-zA-Z0-9])')

    features = [ ParseTag('a', {'href': URL_TYPE_ANY}),
                 ParseTag('base', {'href' : URL_TYPE_BASE}),
                 ParseTag('frame', {'src' : URL_TYPE_FRAME}),
                 ParseTag('img', {'src': URL_TYPE_IMAGE}),
                 ParseTag('form', {'action': URL_TYPE_FORM}),
                 ParseTag('link', {'href': URL_TYPE_ANY}),
                 ParseTag('body', {'background' : URL_TYPE_IMAGE}),
                 ParseTag('script', {'src': URL_TYPE_JAVASCRIPT}),
                 ParseTag('applet', {'codebase': URL_TYPE_JAPPLET_CODEBASE, 'code' : URL_TYPE_JAPPLET}),
                 ParseTag('area', {'href': URL_TYPE_ANY}),
                 ParseTag('meta', {'CONTENT': URL_TYPE_ANY, 'content': URL_TYPE_ANY}),
                 ParseTag('embed', {'src': URL_TYPE_ANY}),
                 ParseTag('object', {'data': URL_TYPE_ANY}),
                 ParseTag('option', {'value': URL_TYPE_ANY}, enabled=False) ]
                 

    handled_rel_types = ( URL_TYPE_STYLESHEET, )
    
    def __init__(self):
        self.url = None
        self.links = []
        self.linkpos = {}
        self.images = []
        # Keywords
        self.keywords = []
        # Description of page
        self.description = ''
        # Title of page
        self.title = ''
        # Fix for <base href="..."> links
        self.base_href = False
        # Base url for above
        self.base = None
        # anchor links flag
        self._anchors = True
        # For META robots tag
        self.can_index = True
        self.can_follow = True
        # Current tag
        self._tag = ''
        SGMLParser.__init__(self)
        # Type
        self.typ = 0
        
    def save_anchors(self, value):
        """ Set the save anchor links flag """

        # Warning: If you set this to true, anchor links on
        # webpages will be saved as separate files.
        self._anchors = value

    def enable_feature(self, tag):
        """ Enable the given tag feature if it is disabled """

        if tag in self.features:
            parsetag = self.features[self.features.index(tag)]
            parsetag.enable()

    def disable_feature(self, tag):
        """ Disable the given tag feature if it is enabled """

        if tag in self.features:
            parsetag = self.features[self.features.index(tag)]
            parsetag.disable()
                
    def filter_link(self, link):
        """ Function to filter links, we decide here whether
        to handle certain kinds of links """

        if not link:
            return LINK_EMPTY

        # ignore javascript links (From 1.2 version javascript
        # links of the form .js are fetched, but we still ignore
        # the actual javascript actions since there is no
        # javascript engine.)
        llink = link.lower()

        # Skip javascript, mailto, news and directory special tags.
        if self.skip_re.match(llink):
            return LINK_FILTERED

        # If this is a web-directory Index page, then check for
        # match with junk URLs of such index pages
        if self.title.lower().startswith('index of'):
            if self.index_page_re.match(llink):
                # print 'Filtering link',llink
                return LINK_FILTERED
            
        # Check if we're accepting query style URLs
        if not objects.config.getquerylinks and self.query_re.search(llink):
            debug('Query filtering link',link)
            return LINK_FILTERED

        return LINK_NOT_FILTERED

    def handle_anchor_links(self, link):
        """ Handle links of the form html#..."""

        # if anchor tag, then get rid of anchor #...
        # and only add the webpage link
        if not link:
            return LINK_EMPTY

        # Need to do this here also
        self.check_add_link(URL_TYPE_ANCHOR, link)

        # No point in getting #anchor sort of links
        # since typically they point to anchors in the
        # same page

        index = link.rfind('.html#')
        if index != -1:
            newhref = link[:(index + 5)]
            self.check_add_link(URL_TYPE_WEBPAGE, newhref)
            return ANCHOR_LINK_FOUND
        else:
            index = link.rfind('.htm#')
            if index != -1:
                newhref = link[:(index + 4)]
                self.check_add_link(URL_TYPE_WEBPAGE, newhref)
                return ANCHOR_LINK_FOUND

        return ANCHOR_LINK_NOT_FOUND

    def unknown_starttag(self, tag, attrs):
        """ This method gives you the tag in the html
        page along with its attributes as a list of
        tuples """

        # Raise event for anybody interested in catching a tagparse event...
        if objects.eventmgr and objects.eventmgr.raise_event('beforetag', self.url, None, tag=tag, attrs=attrs)==False:
            # Don't parse this tag..
            return
                                     
        # Set as current tag
        self._tag = tag
        # print self._tag, attrs
        
        if not attrs: return
        isBaseTag = not self.base and tag == 'base'
        # print 'Base=>',isBaseTag
        
        if tag in self.features:

            d = CaselessDict(attrs)
            parsetag = self.features[self.features.index(tag)]

            # Don't do anything if the feature is disabled
            if not parsetag.isEnabled():
                return
            
            tagdict = parsetag.tagdict
            
            link = ''

            for key, typ in tagdict.items():
                # If there is a <base href="..."> tag
                # set self.base_href
                if isBaseTag and key=='href':
                    self.base_href = True
                    try:
                        self.base = d[key]
                    except:
                        self.base_href = False
                        continue
                
                # if the link already has a value, skip
                # (except for applet tags)
                if tag != 'applet':
                    if link: continue

                if tag == 'link':
                    try:
                        # Fix - only reset typ if it is one
                        # of the valid handled rel types.
                        foundtyp = d['rel'].lower()
                        if foundtyp in self.handled_rel_types:
                            typ = getTypeClass(foundtyp)
                    except KeyError:
                        pass

                try:
                    if tag == 'meta':
                        # Handle meta tag for refresh
                        foundtyp = d.get('http-equiv','').lower()
                        if foundtyp.lower() == 'refresh':
                            link = d.get(key,'')
                            if not link: continue
                            # This will be of the form of either
                            # a time-gap (CONTENT="600") or a time-gap
                            # with a URL (CONTENT="0; URL=<url>")
                            items = link.split(';')
                            if len(items)==1:
                                # Only a time-gap, skip it
                                continue
                            elif len(items)==2:
                                # Second one should be a URL
                                reqd = items[1]
                                # print 'Reqd=>',reqd
                                if (reqd.find('URL') != -1 or reqd.find('url') != -1) and reqd.find('=') != -1:
                                    link = reqd.split('=')[1].strip()
                                    # print 'Link=>',link
                                else:
                                    continue
                        else:
                            # Handle robots meta tag
                            name = d.get('name','').lower()
                            if name=='robots':
                                robots = d.get('content','').lower()
                                # Split to ','
                                contents = [item.strip() for item in robots.split(',')]
                                # Check for nofollow
                                self.can_follow = not ('nofollow' in contents)
                                # Check for noindex
                                self.can_index = not ('noindex' in contents)
                            elif name=='keywords':
                                self.keywords = d.get('content','').split(',')
                                # Trim the keywords list
                                self.keywords = [word.lower().strip() for word in self.keywords]
                            elif name=='description':
                                self.description = d.get('content','').strip()
                            else:
                                continue

                    elif tag != 'applet':
                        link = d[key]
                    else:
                        link += d[key]
                        if key == 'codebase':
                            if link:
                                if link[-1] != '/':
                                    link += '/'
                            continue                                
                except KeyError:
                    continue

                # see if this link is to be filtered
                if self.filter_link(link) != LINK_NOT_FILTERED:
                    # print 'Filtered link',link
                    continue

                # anchor links in a page should not be saved        
                # index = link.find('#')

                # Make sure not to wrongly categorize '#' in query strings
                # as anchor URLs.
                if link.find('#') != -1 and not self.query_re.search(link):
                    # print 'Is an anchor link',link
                    self.handle_anchor_links(link)
                else:
                    # append to private list of links
                    self.check_add_link(typ, link)

    def unknown_endtag(self, tag):
        self._tag = ''
        
    def handle_data(self, data):

        if self._tag.lower()=='title':
            self.title += data

    def check_add_link(self, typ, link):
        """ To avoid adding duplicate links """

        f = False

        if typ == 'image':
            if not (typ, link) in self.images:
                self.images.append((typ, link))
        elif not (typ, link) in self.links:
                # print 'Adding link ', link, typ
                pos = self.getpos()
                self.links.append((typ, link))
                self.linkpos[(typ,link)] = (pos[0],pos[1])
                

    def add_tag_info(self, taginfo):
        """ Add new tag information to this object.
        This can be used to change the behavior of this class
        at runtime by adding new tags """

        # The taginfo object should be a dictionary
        # of the form { tagtype : (elementname, elementype) }

        # egs: { 'body' : ('background', 'img) }
        if type(taginfo) != dict:
            raise AttributeError, "Attribute type mismatch, taginfo should be a dictionary!"

        # get the key of the dictionary
        key = (taginfo.keys())[0]
        if len(taginfo[key]) != 2:
            raise ValueError, 'Value mismatch, size of tag tuple should be 2'

        # get the value tuple
        tagelname, tageltype = taginfo[key]

        # see if this is an already existing tagtype
        if key in self.handled.keys:
            _values = self.handled[key]

            f=0
            for index in xrange(len(_values)):
                # if the elementname is also
                # the same, just replace it.
                v = _values[index]

                elname, eltype = v
                if elname == tagelname:
                    f=1
                    _values[index] = (tagelname, tageltype)
                    break

            # new element, add it to list
            if f==0: _values.append((tagelname, tageltype))
            return 
        else:
            # new key, directly modify dictionary
            elements = []
            elements.append((tagelname, tageltype))
            self.handled[key] = elements 

    def reset(self):
        SGMLParser.reset(self)

        self.url = None
        self.base = None
        self.links = []
        self.images = []
        self.base_href = False
        self.base_url = ''
        self.can_index = True
        self.can_follow = True
        self.title = ''
        self.description = ''
        self.keywords = []
        
    def base_url_defined(self):
        """ Return whether this url had a
        base url of the form <base href='...'>
        defined """

        return self.base_href

    def get_base_url(self):
        return self.base

    def set_url(self, url):
        """ Set the URL whose data is about to be parsed """
        self.url = url

class HarvestManSGMLOpParser(HarvestManSimpleParser):
    """ A parser based on effbot's sgmlop """

    def __init__(self):
        # This module should be built already!
        import sgmlop
        
        self.parser = sgmlop.SGMLParser()
        self.parser.register(self)
        HarvestManSimpleParser.__init__(self)
        # Type
        self.typ = 1
        
    def finish_starttag(self, tag, attrs):
        self.unknown_starttag(tag, attrs)

    def finish_endtag(self, tag):
        self.unknown_endtag(tag)        

    def feed(self, data):
        self.parser.feed(data)
        
class HarvestManCSSParser(object):
    """ Class to parse stylesheets and extract URLs """

    # Regexp to parse stylesheet imports
    importcss1 = re.compile(r'(\@import\s+\"?)(?!url)([\w.-:/]+)(\"?)', re.MULTILINE|re.LOCALE|re.UNICODE)
    importcss2 = re.compile(r'(\@import\s+url\(\"?)([\w.-:/]+)(\"?\))', re.MULTILINE|re.LOCALE|re.UNICODE)
    # Regexp to parse URLs inside CSS files
    cssurl = re.compile(r'(url\()([^\)]+)(\))', re.LOCALE|re.UNICODE)

    def __init__(self):
        # Any imported stylesheet URLs
        self.csslinks = []
        # All URLs including above
        self.links = []

    def feed(self, data):
        self._parse(data)
        
    def _parse(self, data):
        """ Parse stylesheet data and extract imported css links, if any """

        # Return is a list of imported css links.
        # This subroutine uses the specification mentioned at
        # http://www.w3.org/TR/REC-CSS2/cascade.html#at-import
        # for doing stylesheet imports.

        # This takes care of @import "style.css" and
        # @import url("style.css") and url(...) syntax.
        # Media types specified if any, are ignored.
        
        # Matches for @import "style.css"
        l1 = self.importcss1.findall(data)
        # Matches for @import url("style.css")
        l2 = self.importcss2.findall(data)
        # Matches for url(...)
        l3 = self.cssurl.findall(data)
        
        for item in (l1+l2):
            if not item: continue
            url = item[1].replace("'",'').replace('"','')
            self.csslinks.append(url)
            self.links.append(url)
            
        for item in l3:
            if not item: continue
            url = item[1].replace("'",'').replace('"','')
            self.links.append(url)

if __name__=="__main__":
    import os
    import config
    import logger
    
    SetAlias(config.HarvestManStateObject())
    SetAlias(logger.HarvestManLogger())
    
    cfg = objects.config
    cfg.verbosity = 5
    SetLogSeverity()
    
    cfg.getquerylinks = True
    
    p = HarvestManSimpleParser()
    #p.enable_feature('option')
    #p = HarvestManSGMLOpParser()
    
    urls = ['http://projecteuler.net/index.php?section=problems']
    urls = ['http://www.evvs.dk/index.php?cPath=30&osCsid=3b110c689f01d722dbbe53c5cee0bf2d']
    urls = ['http://nltk.sourceforge.net/lite/doc/api/nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html']
    urls = ['http://wiki.java.net/bin/view/Javawsxml/Rome05Tutorials']
    urls = ['http://bits.blogs.nytimes.com/2008/02/27/google-goes-after-another-microsoft-cash-cow/?ref=technology']
    urls = ['http://mail.python.org/pipermail/bangpypers/2008-March/000410.html']

    urls = ['http://www.bad-ischl.ooe.gv.at/system/web/default.aspx']
    urls = ['http://europa.eu/languages/']    
    urls = ['http://www.web2.cz/rs-reference/']
    urls = ['http://harvestmanontheweb.com/']
    urls = ['http://www.web2.cz/rs-uvod/']
    urls = ['http://digitallife.co.in/indian-cheerleaders-for-ipl/']
    urls = ['http://www.brodingberg.gv.at']
    urls = ["www.malvik.kommune.no"]
    urls = ["http://www.gr.ch/Deutsch/index.cfm"]
    
    for url in urls:
        if os.system('wget %s -O index.html' % url ) == 0:
            p.feed(open('index.html').read())
            print p.links, len(p.links)
            for link in p.links:
                print link[1]
                
            print p.keywords
            print p.description
            print p.title
            print p.base_href
            print p.base
            
            p.reset()

                                   




