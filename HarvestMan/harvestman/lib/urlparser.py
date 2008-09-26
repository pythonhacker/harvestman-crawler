# -- coding: utf-8
"""urlparser.py - Module containing class HarvestManUrl,
representing a URL and its relation to disk files in
HarvestMan.

Creation Date: Nov 2 2004

Author: Anand B Pillai <abpillai at gmail dot com>


   Jan 01 2006      jkleven  Change is_webpage to return 'true'
                             if the URL looks like a form query.
   Jan 10 2006      Anand    Converted from dos to unix format (removed Ctrl-Ms).
   Oct 1 2006       Anand    Fixes for EIAO ticket #193 - added reduce_url
                             method to take care of .. chars inside URLs.

   Feb 25 2007      Anand    Added .ars as a web-page extension to support
                             the popular ars-technica website.
   Mar 12 2007      Anand    Added more fields for multipart. Fixed a bug in
                             is_webpage - anchor links should be returned
                             as web-page links.

   Apr 12 2007      Anand    Fixed a bug in anchor link parsing. The current
                             logic was not taking care of multiple anchor
                             links (#anchor1#anchor2). Fixed it by using
                             a regular expression.

                             Test page is
                             http://nltk.sourceforge.net/lite/doc/api/term-index.html

   Mar 05 2008     Anand    Many changes integrated. Method to get canonical form
                             of URL added .Generating index as hash of canonical URL
                             now. Added queue macros.
   Apr 24 2008     Anand    Fix for #829.

Copyright (C) 2004 Anand B Pillai.
   
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import os, sys
import re
import mimetypes
import copy
import urlproc
import md5
import itertools
import random
import document

from types import StringTypes

from common.common import *
from common.netinfo import *
from urltypes import *


# URL queueing status macros

URL_NOT_QUEUED=0       # Fresh URL, not queued yet
URL_QUEUED=1           # Fresh URL sent to queue, but not yet in queue
URL_IN_QUEUE=2         # URL is in queue
URL_IN_DOWNLOAD=3      # URL is out of queue and in download
URL_DONE_DOWNLOAD=4    # URL has completed download, though this may not mean
                       # that the download was successful.

class HarvestManUrlError(Exception):
    """ Error class for HarvestManUrl """
    
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return str(self.value)
    
class HarvestManUrl(object):
    """ A class representing a URL in HarvestMan """

    TEST = False
    hashes = {}
    
    def __init__(self, url, urltype = URL_TYPE_ANY, cgi = False, baseurl  = None, rootdir = ''):

        # Remove trailing wspace chars.
        url = url.rstrip()
        try:
            try:
                try:
                    url.encode("utf-8")
                except UnicodeDecodeError:
                    url = url.decode("iso-8859-1")
            except UnicodeDecodeError, e:
                url = url.decode("latin-1")
        except UnicodeDecodeError, e:
            pass
                
        # For saving original url
        # since self.url can get
        # modified
        self.origurl = url
        
        self.url = url
        self.url = urlproc.modify_url(self.url)
        
        self.typ = urltype
        self.cgi = cgi
        self.anchor = ''
        self.index = 0
        self.filename = 'index.html'
        self.validfilename = 'index.html'
        self.lastpath = ''
        self.protocol = ''
        self.defproto = False
        # If the url is a file like url
        # this value will be true, if it is
        # a directory like url, this value will
        # be false.
        self.filelike = False
        # download status, a number indicating
        # whether this url was downloaded successfully
        # or not. 0 indicates a successful download, and
        # any number >0 indicates a failed download
        self.status = -1
        # Url scheduled status, a number indicating
        # how the URL is queued for download.
        # It has the following values
        # URL_NOT_QUEUED
        # URL_QUEUED
        # URL_IN_DOWNLOAD
        # URL_DONE_DOWNLOAD
        # The fact that the URL has URL_DONE_DOWNLOAD
        # need not mean that the download was successful!
        self.qstatus = URL_NOT_QUEUED
        # Fatal status
        self.fatal = False
        # is starting url?
        self.starturl = False
        # Flag for files having extension
        self.hasextn = False
        # Relative path flags
        self.isrel = False
        # Relative to server?
        self.isrels = False
        self.port = 80
        self.domain = ''
        self.rpath = []
        # Recursion depth
        self.rdepth = 0
        # Url headers
        self.contentdict = {}
        # Url generation
        self.generation = 0
        # Url priority
        self.priority = 0
        # rules violation cache flags
        self.violatesrules = False
        self.rulescheckdone = False
        # Bytes range - used for HTTP/1.1
        # multipart downloads. This has to
        # be set to an xrange object 
        self.range = None
        # Flag to try multipart
        self.trymultipart = False
        # Multipart index
        self.mindex = 0
        # Original url for mirrored URLs
        self.mirror_url = None
        # Flag set for URLs which are mirrored from
        # a different server than the original URL
        self.mirrored = False
        # Content-length for multi-part
        # This is the content length of the original
        # content.
        self.clength = 0
        self.dirpath = []
        # Re-computation flag
        self.reresolved = False
        # URL redirected flag
        self.redirected = False
        # Flag indicating we are using an old URL
        # which was redirected, again for producing
        # further redirections. This is used in Hget
        # for automatic split-mirror downloading
        # for URLs that auto-forward to mirrors.
        self.redirected_old = False
        self.baseurl = None
        # Hash of page data
        self.pagehash = ''
        # Flag to decide whether to recalculate get_full_url(...)
        # if flag is False, recalculate...
        self.urlflag = False
        # Cached full URL string
        self.absurl = ''
        # Base Url Dictionary
        if baseurl:
            if isinstance(baseurl, HarvestManUrl):
                self.baseurl = baseurl
            elif type(baseurl) in StringTypes:
                self.baseurl = HarvestManUrl(baseurl, 'generic', cgi, None, rootdir)
                      
        # Root directory
        if rootdir == '':
            if self.baseurl and self.baseurl.rootdir:
                self.rootdir = self.baseurl.rootdir
            else:
                self.rootdir = os.getcwd()
        else:
            self.rootdir = rootdir
            
        self.anchorcheck()
        self.resolveurl()

        # For starting URL, the index is 0, for the rest
        # it is as hash of the canonical URL string...
        self.index = hash(self.get_canonical_url())
        # If this is a URL similar to start URL,
        # reset its index to zero. The trick is
        # to store only the hash of the start URL
        # as key in the attribute 'hashes'.
        
        try:
            val = self.hashes[self.index]
            self.index = 0
        except KeyError:
            pass

        # Copy of myself, this will be saved if
        # a re-resolving is requested so that old
        # parameters can be requested if needed
        self.orig_state = None
        
    def reset(self):
        """ Reset all the key attributes """

        # Archive previous state
        self.orig_state = copy.copy(self)

        self.url = urlproc.modify_url(self.url)
        self.lastpath = ''
        self.protocol = ''
        self.defproto = False
        self.hasextn = False
        self.isrel = False
        self.isrels = False
        self.port = 80
        self.domain = ''
        self.rpath = []
        # Recursion depth
        self.rdepth = 0
        self.dirpath = []
        self.rpath = []
        self.filename = 'index.html'
        self.validfilename = 'index.html'
        # Set urlflag to False
        self.urlflag = False
        self.absurl = ''

    def __str__(self):
        return self.absurl
    
    def wrapper_resolveurl(self):
        """ Called forcefully to re-resolve a URL, typically after a re-direction
        or change in URL has been detected """

        self.reset()
        self.anchorcheck()
        self.resolveurl()
        self.reresolved = True
        
    def anchorcheck(self):
        """ Checking for anchor tags and processing accordingly """

        if self.typ == 'anchor':
            if not self.baseurl:
                raise HarvestManUrlError, 'Base url should not be empty for anchor type url'

            if '#' in self.url:
                # Split with re
                items = anchore.split(self.url)
                # First item is the original url
                if len(items):
                    if items[0]:
                        self.url = items[0]
                    else:
                        self.url = self.baseurl.get_full_url()
                    # Rest forms the anchor tag
                    self.anchor = '#' + '#'.join(items[1:])
                    
    def resolve_protocol(self):
        """ Resolve the protocol of the url """

        url2 = self.url.lower()
        for proto in protocol_map.keys():
            if url2.find(proto) != -1:
                self.protocol = proto
                self.port = protocol_map.get(proto)
                return True
        else:
            # Fix: Use regex for detecting WWW urls.
            # Check for WWW urls. These can begin
            # with a 'www.' or 'www' followed by
            # a single number (www1, www3 etc).
            if www_re.match(url2):
                self.protocol = 'http://'
                self.url =  "".join((self.protocol, self.url))
                return True

            # We accept FTP urls beginning with just
            # ftp.<server>, and consider it as FTP over HTTP
            if url2.startswith('ftp.'):
                # FTP over HTTP
                self.protocol = 'http://'
                self.url = ''.join((self.protocol, self.url))
                return True
            
            # Urls relative to server might
            # begin with a //. Then prefix the protocol
            # string to them.
            if self.url.find('//') == 0:
                # Pick protocol from base url
                if self.baseurl and self.baseurl.protocol:
                    self.protocol = self.baseurl.protocol
                else:
                    self.protocol = "http://"   
                self.url = "".join((self.protocol, self.url[2:]))
                return True

            # None of these
            # Protocol not resolved, so check
            # base url first, if not found, set
            # default protocol...
            if self.baseurl and self.baseurl.protocol:
                self.protocol = self.baseurl.protocol
            else:
                self.protocol = 'http://'

            self.defproto = True
        
            return False
        
    def resolveurl(self):
        """ Resolves the url finding out protocol, port, domain etc
        . Also resolves relative paths and builds a local file name
        for the url based on the root directory path """

        if len(self.url)==0:
            raise HarvestManUrlError, 'Error: Zero Length Url'

        proto = self.resolve_protocol()

        paths = ''
        
        if not proto:
            # Could not resolve protocol, must be a relative url
            if not self.baseurl:
                raise HarvestManUrlError, 'Base url should not be empty for relative urls'

            # Set url-relative flag
            self.isrel = True
            # Is relative to server?
            if self.url[0] == '/':
                self.isrels = True
            
            # Split paths
            relpaths = self.url.split(URLSEP)
            try:
                idx = relpaths.index(DOTDOT)
            except ValueError:
                idx = -1

            # Only reduce if the URL itself does not start with
            # .. - if it does our rpath algorithm takes
            # care of it.
            print 'Relpaths=>',relpaths
            if idx > 0:
                relpaths = self.reduce_url(relpaths)

            # Build relative path by checking for "." and ".." strings
            self.rindex = 0
            for ritem in relpaths:
                # If path item is ., .. or empty, increment
                # relpath index.
                if ritem in (DOT, DOTDOT, ""):
                    self.rindex += 1
                    # If path item is not empty, insert
                    # to relpaths list.
                    if ritem:
                        self.rpath.append(ritem)

                else:
                    # Otherwise, add the rest to paths
                    # with the separator
                    for entry in relpaths[self.rindex:]:
                        paths = "".join((paths, entry, URLSEP))

                    # Remove the last entry
                    paths = paths[:-1]
                    
                    # Again Trim if the relative path ends with /
                    # like href = /img/abc.gif/ 
                    #if paths[-1] == '/':
                    #    paths = paths[:-1]
                    break
            
        else:
            # Absolute path, so 'paths' is the part of it
            # minus the protocol part.
            paths = self.url.replace(self.protocol, '')            

            # Split URL
            items = paths.split(URLSEP)
            
            # If there are nonsense .. and . chars in the paths, remove
            # them to construct a sane path.
            #try:
            #    idx = items.index(DOTDOT)
            #except ValueError:
            #    idx = -1            
            flag = (DOT in items) or (DOTDOT in items)
            
            if flag:
                # Bugfix: Do not allow a URL like http://www.foo.com/../bar
                # to become http://bar. Basically if the index of .. is
                # 1, then remove the '..' entirely. This bug was encountered
                # in EIAO testing of http://www.fylkesmannen.no/ for the URL
                # http://www.fylkesmannen.no/osloogakershu
                
                items = self.reduce_url(items)
                # Re-construct URL
                paths = URLSEP.join(items)
                
        # Now compute local directory/file paths

        # For cgi paths, add a url separator at the end 
        #if self.cgi:
        #    paths = "".join((paths, URLSEP))

        self.compute_dirpaths(paths)
        if not self.protocol.startswith('file:'):
            self.compute_domain_and_port()

        # For some file extensions, automatically set as directory URL.
        if self.validfilename:
            extn = ((os.path.splitext(self.validfilename))[1]).lower()
            if extn in default_directory_extns:
                self.set_directory_url()

        # print self.dirpath, self.domain
        
    def reduce_url(self, paths):
        """ Remove nonsense .. and . chars from URL paths """

        print 'Paths=>',paths
        if paths[0]=='?':
            # Don't reduce if URL has ? in the beginning
            return paths
        
        for x in range(len(paths)):
            path = paths[x]
            try:
                nextpath = paths[x+1]
                if nextpath == '..':
                    paths.pop(x+1)
                    # Do not allow to remove the domain for
                    # stupid URLs like 'http://www.foo.com/../bar' or
                    # 'http://www.foo.com/camp/../../bar'. If allowed
                    # they become nonsense URLs like http://bar.

                    # This bug was encountered in EIAO testing of
                    # http://www.fylkesmannen.no/ for the URL
                    # http://www.fylkesmannen.no/osloogakershu
                    
                    if self.isrel or x>0:
                        paths.remove(path)
                    return self.reduce_url(paths)
                elif nextpath=='.':
                    paths.pop(x+1)
                    return self.reduce_url(paths)                    
            except IndexError:
                return paths
        
        
    def compute_file_and_dir_paths(self):
        """ Compute file and directory paths """

        if self.lastpath:
            dotindex = self.lastpath.find(DOT)
            if dotindex != -1:
                self.hasextn = True

            # If there is no extension or if there is
            # an extension which is occuring in the middle
            # of last path...
            if (dotindex == -1) or \
                ((dotindex >0) and (dotindex < (len(self.lastpath)-1))):
                self.filelike = True
                # Bug fix - Strip leading spaces & newlines
                self.validfilename =  self.make_valid_filename(self.lastpath.strip())
                self.filename = self.lastpath.strip()
                self.dirpath  = self.dirpath [:-1]
        else:
            if not self.isrel:
                self.dirpath  = self.dirpath [:-1]

        # Remove leading spaces & newlines from dirpath
        dirpath2 = []
        for item in self.dirpath:
            dirpath2.append(item.strip())

        # Copy
        self.dirpath = dirpath2[:]
            
    def compute_dirpaths(self, path):
        """ Computer local file & directory paths for the url """

        self.dirpath = path.split(URLSEP)
        self.lastpath = self.dirpath[-1]
        # print self.dirpath, self.lastpath
        
        if self.isrel:
            # Construct file/dir names - This is valid only if the path
            # has more than one component - like www.python.org/doc .
            # Otherwise, the url is a plain domain
            # path like www.python.org .
            self.compute_file_and_dir_paths()
            print 'Dirpath1=>',self.dirpath
            # print 'Rpath=>',self.rpath
            
            # Interprets relative path
            # ../../. Nonsense relative paths are graciously ignored,
            self.rpath.reverse()
            # print 'Base url dirpath=>',self.baseurl.dirpath
            # print 'Rindex=>',self.rindex
            
            if len(self.rpath) == 0 :
                print '1'
                if not self.rindex:
                    # This simple logic is fine for most paths except
                    # when a base URL has a "?" as part of its dirpath.
                    # Example: http://razor.occams.info/code/repo/?/govtrack/sec .
                    # In that case, any pieces of the base URL after the
                    # ? is to be omitted.
                    if '?' in self.baseurl.dirpath:
                        # Trim base url to the part before ?
                        qindex = self.baseurl.dirpath.index('?')
                        self.baseurl.dirpath = self.baseurl.dirpath[:qindex]
                    
                    self.dirpath = self.baseurl.dirpath + self.dirpath
            else:
                pathstack = self.baseurl.dirpath[0:]
                
                for ritem in self.rpath:
                    if ritem == DOT:
                        pathstack = self.baseurl.dirpath[0:]
                    elif ritem == DOTDOT:
                        if len(pathstack) !=0:
                            pathstack.pop()
            
                self.dirpath  = pathstack + self.dirpath 

            # print 'Dirpath2=>',self.dirpath
            
            # Support for NONSENSE relative paths such as
            # g/../foo and g/./foo 
            # consider base = http:\\bar.com\bar1
            # then g/../foo => http:\\bar.com\bar1\..\foo => http:\\bar.com\foo
            # g/./foo  is utter nonsense and we feel free to ignore that.
            index = 0
            for item in self.dirpath:
                if item in (DOT, DOTDOT):
                    self.dirpath.remove(item)
                if item == DOTDOT:
                    self.dirpath.remove(self.dirpath[index - 1])
                index += 1
        else:
            if len(self.dirpath) > 1:
                self.compute_file_and_dir_paths()
            
    def compute_domain_and_port(self):
        """ Computes url domain and port &
        re-computes if necessary """

        # Resolving the domain...
        
        # Domain is parent domain, if
        # url is relative :-)
        if self.isrel:
            self.domain = self.baseurl.domain
        else:
            # If not relative, then domain
            # if the first item of dirpath.
            self.domain = self.dirpath[0]
            self.dirpath = self.dirpath[1:]

        # Find out if the domain contains a port number
        # for example, server:8080
        dom = self.domain
        index = dom.find(PORTSEP)
        if index != -1:
            self.domain = dom[:index]
            # A bug here => needs to be fixed
            try:
                self.port   = int(dom[index+1:])
            except:
                pass

        # Now check if the base domain had a port specification (other than 80)
        # Then we need to use that port for all its children, otherwise
        # we can use default value.
        if self.isrel and \
               self.baseurl and \
               self.baseurl.port != self.port and\
               self.baseurl.protocol != 'file://':
            
            self.port = self.baseurl.port

        # Convert domain to lower case
        if self.domain != '':
            self.domain = self.domain.lower()
        
    def make_valid_filename(self, s):
        """ Replace junk characters to create a valid filename """

        # Replace any %xx strings
        percent_chars = percent_repl.findall(s)
        for pchar in percent_chars:
            try:
                s = s.replace(pchar, chr(int(pchar.replace('%','0x'), 16)))
            except UnicodeDecodeError:
                try:
                    s = s.decode('iso-8859-1')
                    s = s.replace(pchar, chr(int(pchar.replace('%','0x'), 16)))
                except UnicodeDecodeError, e:
                    pass
                
        for x,y in itertools.izip(junk_chars, junk_chars_repl):
            s = s.replace(x, y)

        return s

    def make_valid_url(self, url):
        """ Make a valid url """

        for x,y in itertools.izip(dirty_chars, dirty_chars_repl):
            if x in url:
                url = url.replace(x, y)

        # Replace spaces between words
        # with '%20'.
        # For example http://www.foo.com/bar/this file.html
        # Fix: Use regex instead of blind
        # replacement.
        if wspacere.search(url):
            url = re.sub(r'\s', '%20', url)
        
        # Replace all % chars with their capital counterparts
        # i.e %3a => %3A, %5b => %5B etc. This helps in
        # canonicalization.
        percent_chars = percent_repl.findall(url)
        for pchar in percent_chars:
            url = url.replace(pchar, pchar.upper())
            
        return url

    def is_filename_url(self):
        """ Return whether this is file name url """

        # A directory url is something like http://www.python.org
        # which points to the <index.html> file inside the www.python.org
        # directory.A file name url is a url that points to an actual
        # file like http://www.python.org/doc/current/tut/tut.html

        return self.filelike

    def is_cgi(self):
        """ Check whether this url is a cgi (dynamic/form) link """

        return self.cgi

    def is_relative_path(self):
        """ Return whether the original url was a relative one """

        return self.isrel

    def is_relative_to_server(self):
        """ Return whether the original url was relative to the server """
        
        return self.isrels

    def is_image(self):
        """ Find out if the file is an image """

        if self.typ == 'image':
            return True
        elif self.typ == 'generic':
            if self.validfilename:
                extn = ((os.path.splitext(self.validfilename))[1]).lower()
                if extn in image_extns:
                    return True
             
        return False

    def is_multimedia(self):
        """ Found out if the file is a multimedia (vide or audio) type """

        return (self.is_video() or self.is_audio())
        
    def is_audio(self):
        """ Find out if the file is a multimedia audio type """

        if self.typ == 'audio':
            return True
        elif self.typ == 'generic':
            if self.validfilename:
                extn = ((os.path.splitext(self.validfilename))[1]).lower()
                if extn in sound_extns:
                    return True
             
        return False

    def is_video(self):
        """ Find out if the file is a multimedia video type """

        if self.typ == 'video':
            return True
        elif self.typ == 'generic':
            if self.validfilename:
                extn = ((os.path.splitext(self.validfilename))[1]).lower()
                if extn in movie_extns:
                    return True
             
        return False
            
    def is_webpage(self):
        """ Find out by if the file is a webpage type """

        # Note: right now we treat dynamic server-side scripts namely
        # php, psp, asp, pl, jsp, and cgi as possible html candidates, though
        # actually they might be generating non-html content (like dynamic
        # images.)
        
        if self.typ.isA(URL_TYPE_WEBPAGE):
            return True
        elif self.typ==URL_TYPE_ANY:
            if self.validfilename:
                extn = ((os.path.splitext(self.validfilename))[1]).lower()
                
                if extn in webpage_extns:
                    return True
                
                elif extn not in document_extns and extn not in image_extns:
                    return True
                else:
                    # jkleven: 10/1/06.  Forms were never being parsed for links.

                    # If we are allowing download of query forms (i.e., bin?asdf=3 style URLs)
                    # then run the URL through a regex if we're still not sure if its ok.
                    # if it matches the from_re precompiled regex then we'll assume its
                    # a query style URL and we'll return true.
                    if objects.config and objects.config.getquerylinks and form_re.search(self.get_full_url()):
                        return True

        return False

    def is_stylesheet(self):
        """ Find out whether the url is a style sheet type """

        if self.typ == 'stylesheet':
            return True
        elif self.typ == 'generic':
            if self.validfilename:
                extn = ((os.path.splitext(self.validfilename))[1]).lower()
                if extn in stylesheet_extns:
                    return True
             
        return False

    def is_document(self):
        """ Return whether the url is a document """

        # This method is useful for Indexers which use HarvestMan.
        # We define any URL which is not an image, is either a web-page
        # or any of the following types as a document.

        # Microsoft word documents
        # Openoffice documents
        # Adobe PDF documents
        # Postscript documents

        if self.is_image(): return False
        if self.is_webpage(): return True

        # Check extension
        if self.validfilename:
            extn = ((os.path.splitext(self.validfilename))[1]).lower()
            if extn in document_extns:
                return True

        return False
    
    def is_equal(self, url):
        """ Find whether the passed url matches
        my url """

        # Try 2 tests, one straightforward
        # other with a "/" appended at the end
        myurl = self.get_full_url()
        if url==myurl:
            return True
        #else:
        #    myurl += URLSEP
        #    if url==myurl:
        #        return True

        return False
        
    # ============ End - Is (Boolean Get) Methods =========== #  
    # ============ Begin - General Get Methods ============== #
    def get_url_content_info(self):
        """ Get the url content information """
        
        return self.contentdict
    
    def get_anchor(self):
        """ Return the anchor tag of this url """

        return self.anchor

    def get_anchor_url(self):
        """ Get the anchor url, if this url is an anchor type """

        return "".join((self.get_full_url(), self.anchor))

    def get_generation(self):
        """ Return the generation of this url """
        
        return self.generation    

    def get_priority(self):
        """ Get the priority for this url """

        return self.priority

    def get_download_status(self):
        """ Return the download status for this url """

        return self.status

    def get_type(self):
        """ Return the type of this url as a string """
        
        return self.typ

    def get_parent_url(self):
        """ Return the parent url of this url """
        
        return self.baseurl

    def get_url_directory(self):
        """ Return the directory path (url minus its filename if any) of the url """
        
        # get the directory path of the url
        fulldom = self.get_full_domain()
        urldir = fulldom

        if self.dirpath:
            newpath = "".join((URLSEP, "".join([ x+'/' for x in self.dirpath])))
            urldir = "".join((fulldom, newpath))

        return urldir

    def get_url_directory_sans_domain(self):
        """ Return url directory minus the domain """

        # New function in 1.4.1
        urldir = ''
        
        if self.dirpath:
            urldir = "".join((URLSEP, "".join([ x+'/' for x in self.dirpath])))

        return urldir        
        
    def get_url(self):
        """ Return the url of this object """
        
        return self.url

    def get_original_url(self):
        """ Return the original url of this object """
        
        return self.origurl

    def get_canonical_url(self):
        """ Return the canonicalized form of this URL """

        # A canonical URL or 'normalized' URL is a URL modified
        # to a standardized form so that similar URLs can be
        # found out by comparing their canonical forms. HarvestMan
        # uses canonical URLs to remove DUST (Duplicate URLs with
        # similar text) to some extent.

        # Wikipedia describes canonicalization of a URL
        # {http://en.wikipedia.org/wiki/URL_normalization}
        #
        # 1. Converting the scheme and host to lower case...
        # 2. Adding trailing to directory URLs...
        # 3. Removing directory index, i.e
        #    http://www.example.com/default.asp => http://www.example.com/
        #    http://www.example.com/index.html => http://www.example.com/
        # 4. Case insensitive files => If the URL is running on a case insensitive
        #    file system (Windows, example: FAT*, NTFS etc), then the canonical
        #    form should use lower case.
        # 5. Capitalizing letters in escape sequences - All letters within a
        # percent-encoding triplet (e.g., "%3A") are case-insensitive, and should
        # be capitalized.
        # Egs: http://www.example.com/a%c2%b1b → http://www.example.com/a%C2%B1b
        # 6. Removing the anchor fragment 
        # Egs: http://www.example.com/bar.html#section1 → http://www.example.com/bar.html
        # 7. Removing the default port.
        # 8. Removing dot segments. { http://example/com/b/c/.././file.html => http://example.com/b/file.html }
        # 9. Removing www as the first domain label. i.e www.example.com => example.com
        # 10. Sorting the variables of active pages (dynamic pages) -> 
        #  {http://www.example.com/display?lang=en&article=fred → http://www.example.com/display?article=fred&lang=en}
        # 11. Removing default querystring variables. A default value in the querystring will
        # render identically whether it is there or not. When a default value appears in the querystring,
        # it should be removed. {http://www.example.com/display?id=&sort=ascending =>  http://www.example.com/display}
        # 12. Removing the "?" when the querystring is empty. When the querystring is
        # empty, there is no need for the "?
        # { http://www.example.com/display? → http://www.example.com/display  }

        # HarvestMan does 1,2,3,5,6,7,8,9,10,11,12 in order. Note that HarvestMan
        # performs 6,7,8 automatically when processing the original URL.

        # 1 is already done when resolving the URL.
        # 2 is already done when resolving the URL
        # 3 is already done for root domains. i.e http://www.example.com
        #  becomes http://www.example.com/ . However this is not done
        # for directory URL since we are not sure if this would be a
        # file or directory i.e http://www.example.com/docs/ and
        # http://www.example.com/docs will parse to
        # http://www.example.com/docs without the trailing slash since
        # by default we assume that the URL refers to the file "/docs"
        # rather than the directory index for "/docs" folder.
        # Skip 4
        # 5 is done by make_valid_url()...
        # 6,7,8 are automatically done
        # Doing 9, 10,11 and 12 and specifically. 

        # Get full url first...
        url = self.get_full_url()
        params = params_re.findall(url)
        lp = len(params)
        if lp>1:
            # Rule#11: Remove those params which are using a default value
            # i.e which does not specify a value.
            params = [param for param in params if param_re.match(param)]
            # More than one param, sort it
            params.sort()
            url_sans_params = ampersand_re.sub('', params_re.sub('', url))
            # Now put the params back in sorted order
            url = url_sans_params + '&'.join(params)
        elif lp==0:
            # If no params but there is a ? at end, rule 12 applies
            # Remove trailing ? at the end
            url = question_re.sub('', url)

        # Finally we strip off the www. from the beginning of the URL
        url = www2_re.sub('', url)

        return url
        
    def get_full_url(self):
        """ Return the full url path of this url object after
        resolving relative paths, filenames etc """

        if self.urlflag:
            return self.absurl
        else:
            rval = ''
            
            if not self.protocol.startswith('file:'):
                rval = self.get_full_domain_with_port()

                if self.dirpath:
                    newpath = "".join([ x+URLSEP for x in self.dirpath if x and not x[-1] ==URLSEP])
                    rval = "".join((rval, URLSEP, newpath))

                if rval[-1] != URLSEP:
                    rval += URLSEP

                if self.filelike:
                    rval = "".join((rval, self.filename))
                
            else:
                rval = ''
                if self.dirpath:
                    newpath = "/".join([x for x in self.dirpath if ((x and not x[-1] ==URLSEP) or (not x))])            
                    rval += newpath
                    
                if self.filelike:
                    rval = "".join((rval, URLSEP, self.filename))

                return self.protocol + rval
            
            self.urlflag = True
            self.absurl = self.make_valid_url(rval)

            return self.absurl

  ##       # If this is already calculated, return the cached value...
##         if self.urlflag:
##             return self.absurl
##         else:
##             rval = self.get_full_domain_with_port()
##             if self.dirpath:
##                 newpath = "".join([ x+URLSEP for x in self.dirpath if x and not x[-1] ==URLSEP])
##                 rval = "".join((rval, URLSEP, newpath))
            
##             if rval[-1] != URLSEP:
##                 rval += URLSEP

##             if self.filelike:
##                 rval = "".join((rval, self.filename))

##             self.urlflag = True
##             self.absurl = self.make_valid_url(rval)

##             return self.absurl
       # If this is already calculated, return the cached value...


    def get_full_url_sans_port(self):
        """ Return absolute url without the port number """

        rval = self.get_full_domain()
        if self.dirpath:
            newpath = "".join([ x+'/' for x in self.dirpath])
            rval = "".join((rval, URLSEP, newpath))

        if rval[-1] != URLSEP:
            rval += URLSEP

        if self.filelike:
            rval = "".join((rval, self.filename))

        return self.make_valid_url(rval)

    def get_port_number(self):
        """ Return the port number of this url """

        # 80 -> http urls
        return self.port

    def get_relative_url(self):
        """ Return relative path of url w.r.t the domain """

        newpath=""
        if self.dirpath:
            newpath =  "".join(("/", "".join([ x+'/' for x in self.dirpath])))

        if self.filelike:
            newpath = "".join((newpath, URLSEP, self.filename))
            
        return self.make_valid_url(newpath)

    def get_base_domain(self):
        """ Return the base domain for this url object """

        # Explanation: Base domain is the domain
        # at the root of a given domain. For example
        # base domain of stats.foo.com is foo.com.
        # If there is no subdomain, this will be
        # the same as the domain itself.

        # If the server name is of the form say bar.foo.com
        # or vodka.bar.foo.com, i.e there are more than one
        # '.' in the name, then we need to return the
        # last string containing a dot in the middle.

        # Get domain
        domain = self.domain
        
        if domain.count('.') > 1:
            dotstrings = domain.split('.')
            # now the list is of the form => [vodka, bar, foo, com]

            # Return the last two items added with a '.'
            # in between
            return "".join((dotstrings[-2], ".", dotstrings[-1]))
        else:
            # The server is of the form foo.com or just "foo"
            # so return it straight away
            return domain

    def get_base_domain_with_port(self):
        """ Return the base domain (server) with port number
        appended to it, if the port number is not the
        default for the current protocol """
        
        if ((self.protocol == 'http://' and int(self.port) != 80) \
            or (self.protocol == 'https://' and int(self.port) != 443) \
            or (self.protocol == 'ftp://' and int(self.port) != 21)):
            return self.get_base_domain() + ':' + str(self.port)
        else:
            return self.get_base_domain()

    def get_url_hash(self):
        """ Return a hash value for the URL """

        m = md5.new()
        m.update(self.get_full_url())
        return str(m.hexdigest())
    
    def get_domain_hash(self):
        """ Return the hask value for the domain """

        m = md5.new()
        m.update(self.get_full_domain())
        return str(m.hexdigest())

    def get_data_hash(self):
        """ Return the hash value for the URL data """

        return self.pagehash

    def get_domain(self):
        """ Return the domain (server) for this url object """
        
        return self.domain

    def get_full_domain(self):
        """ Return the full domain (protocol + domain) for this url object """
        
        return self.protocol + self.domain

    def get_full_domain_with_port(self):
        """ Return the domain (server) with port number
        appended to it, if the port number is not the
        default for the current protocol """

        if (self.protocol == 'http://' and int(self.port) != 80) \
           or (self.protocol == 'https://' and int(self.port) != 443) \
           or (self.protocol == 'ftp://' and int(self.port) != 21):
            return self.get_full_domain() + ':' + str(self.port)
        else:
            return self.get_full_domain()

    def get_domain_with_port(self):
        """ Return the domain (server) with port number
        appended to it, if the port number is not the
        default for the current protocol """

        if (self.protocol == 'http://' and self.port != 80) \
           or (self.protocol == 'https://' and self.port != 443) \
           or (self.protocol == 'ftp://' and self.port != 21):
            return self.domain + ':' + str(self.port)
        else:
            return self.domain

    def get_full_filename(self):
        """ Return the full filename of this url on the disk.
        This is created w.r.t the local directory where we save
        the url data """

        return os.path.join(self.get_local_directory(), self.get_filename())

    def get_filename(self):
        """ Return the filename of this url on the disk. """

        # NOTE: This is just the filename, not the absolute filename path
        return self.validfilename

    def get_relative_filename(self, filename=''):

        # NOTE: Rewrote this method completely
        # on Nov 18 for 1.4 b2.
        
        # If no file name given, file name
        # is the file name of the parent url
        if not filename:
            if self.baseurl:
                filename = self.baseurl.get_full_filename()

        # Still filename is NULL,
        # return my absolute path
        if not filename:
            return self.get_full_filename()
        
        # Get directory of 'filename'
        diry = os.path.dirname(filename)
        if diry[-1] != os.sep:
            diry += os.sep
            
        # Get my filename
        myfilename = self.get_full_filename()
        # If the base domains are different, we
        # cannot find a relative path, so return
        # my filename itself.
        bdomain = self.baseurl.get_domain()
        mydomain = self.get_domain()

        if mydomain != bdomain:
            return myfilename

        # If both filenames are the same,
        # return just the filename.
        if myfilename==filename:
            return self.get_filename()
        
        # Get common prefix of my file name &
        # other file name.
        prefix = os.path.commonprefix([myfilename, filename])
        relfilename = ''
        
        if prefix:
            if not os.path.exists(prefix):
                prefix = os.path.dirname(prefix)
            
            if prefix[-1] != os.sep:
                prefix += os.sep

            # If prefix is the name of the project
            # directory, both files have no
            # common component.
            try:
                if os.path.samepath(prefix,self.rootdir):
                    return myfilename
            except:
                if prefix==self.rootdir:
                    return myfilename
            
            # If my directory is a subdirectory of
            # 'dir', then prefix should be the same as
            # 'dir'.
            sub=False

            # To test 'sub-directoriness', check
            # whether dir is wholly contained in
            # prefix. 
            prefix2 = os.path.commonprefix([diry,prefix])
            if prefix2[-1] != os.sep:
                prefix2 += os.sep
            
            # os.path.samepath is not avlbl in all
            # platforms.
            try:
                if os.path.samepath(diry, prefix2):
                    sub=True
            except:
                if diry==prefix2:
                    sub=True

            # If I am in a sub-directory, relative
            # path is my filename minus the common
            # path.
            if sub:
                relfilename = myfilename.replace(prefix2, '')
                return relfilename
            else:
                # If I am not in sub-directory, then
                # we need to get the relative path.
                dirwithoutprefix = diry.replace(prefix, '')
                filewithoutprefix = myfilename.replace(prefix, '')
                relfilename = filewithoutprefix
                    
                paths = dirwithoutprefix.split(os.sep)
                for item in paths:
                    if item:
                        relfilename = "".join(('..', os.sep, relfilename))

                return relfilename
        else:
            # If there is no common prefix, then
            # it means me and the passed filename
            # have no common paths, so return my
            # full path.
            return myfilename
            
    def get_relative_depth(self, hu, mode=0):
        """ Get relative depth of current url object vs passed url object.
        Return a postive integer if successful and -1 on failure """

        # Fixed 2 bugs on 22/7/2003
        # 1 => passing arguments to find function in wrong order
        # 2 => Since we allow the notion of zero depth, even zero
        # value of depth should be returned.

        # This mode checks for depth based on a directory path
        # This check is valid only if dir2 is a sub-directory of dir1
        dir1=self.get_url_directory()
        dir2=hu.get_url_directory()

        # spit off the protocol from directories
        dir1 = dir1.replace(self.protocol, '')
        dir2 = dir2.replace(self.protocol, '')      

        # Append a '/' to the dirpath if not already present
        if dir1[-1] != '/': dir1 += '/'
        if dir2[-1] != '/': dir2 += '/'

        if mode==0:
            # check if dir2 is present in dir1
            # bug: we were passing arguments to the find function
            # in the wrong order.
            if dir1.find(dir2) != -1:
                # we need to check for depth only if the above condition is true.
                l1=dir1.split('/')
                l2=dir2.split('/')
                if l1 and l2:
                    diff=len(l1) - len(l2)
                    if diff>=0: return diff

            return -1
        # This mode checks for depth based on the base server(domain).
        # This check is valid only if dir1 and dir2 belong to the same
        # base server (checked by name)
        elif mode==1:
            if self.domain == hu.domain:
                # we need to check for depth only if the above condition is true.
                l1=dir1.split('/')
                l2=dir2.split('/')
                if l1 and l2:
                    diff=len(l1) - len(l2)
                    if diff>=0: return diff
            return -1

        # This check is done for the current url against current base server (domain)
        # i.e, this mode does not use the argument 'hu'
        elif mode==2:
            dir2 = self.domain
            if dir2[-1] != '/':
                dir2 += '/'

            # we need to check for depth only if the above condition is true.
            l1=dir1.split('/')
            l2=dir2.split('/')
            if l1 and l2:
                diff=len(l1) - len(l2)
                if diff>=0: return diff
            return -1

        return -1

    def get_root_dir(self):
        """ Return root directory """
        
        return self.rootdir
    
    def get_local_directory(self):
        """ Return the local directory path of this url w.r.t
        the directory on the disk where we save the files of this url """
        
        # Gives Local Direcory path equivalent to URL Path in server
        rval = ''
        if not self.protocol.startswith('file:'):
            rval = os.path.join(self.rootdir, self.domain)
            
            for diry in self.dirpath:
                if not diry: continue
                rval = os.path.abspath( os.path.join(rval, self.make_valid_filename(diry)))
        else:
            rval = self.rootdir
            
            for diry in self.dirpath:
                if not diry: continue
                rval = os.path.abspath( os.path.join(rval, self.make_valid_filename(diry)))                    
                    
        return os.path.normpath(rval)

    def get_original_state(self):
        """ Return the original state of this URL object. This is useful
        to obtain earlier attributes of a URL after it's state was
        changed by a URL modification """

        # It is up to the caller to check this value
        return self.orig_state
        
    # ============ Begin - Set Methods =========== #

    def set_directory_url(self):
        """ Set this as a directory url """

        self.filelike = False
        # print self.dirpath, self.lastpath, self.domain
        
        if (not self.dirpath and self.lastpath != self.domain) or (self.dirpath and (self.dirpath[-1] != self.lastpath)):
            self.dirpath.append(self.lastpath)
        self.validfilename = 'index.html'
        self.urlflag = False
        
    def set_url_content_info(self, headers):
        """ This function sets the url content information of this
        url. It is a convenient function which can be used by connectors
        to store url content information """

        if headers:
            self.contentdict = copy.deepcopy(headers)

    def violates_rules(self):
        """ Check if this url violates existing download rules """

        # If I am the base url object, violates rule checks apply
        # only if my original URL has changed.

        if self.starturl and not self.reresolved:
            return False
            
        if not self.rulescheckdone:
            self.violatesrules = objects.rulesmgr.violates_rules(self)
            self.rulescheckdone = True

        return self.violatesrules

    def recalc_locations(self):
        """ Recalculate filenames/directories etc """

        # Case 1 - trying to save as a file when the
        # parent "directory" is an existing file.
        # Solution - Change the paths of parent URL object
        # to change its filename...
        directory = self.get_url_directory()
        if os.path.isfile(directory):
            parent = self.baseurl
            # Anything can be done on this only if this
            # is a HarvestManUrl object
            if isinstance(parent, HarvestManUrl):
                parent.dirpath.append(parent.filename)
                parent.filename = 'index.html'
                parent.validfilename = 'index.html'

        # Case 2 - trying to save as file when the
        # path is an existing directory.
        # Solution - Save as index.html in the directory
        filename = self.get_full_filename()
        if os.path.isdir(filename):
            self.dirpath.append(self.filename)
            self.filename = 'index.html'
            self.validfilename = 'index.html'
        
    def manage_content_type(self, content_type):
        """ This function gets called from connector modules
        connect method, after retrieving information about
        a url. This function can manage the content type of
        the url object if there are any differences between
        the assumed type and the returned type """

        # Guess extension of type
        extn = mimetypes.guess_extension(content_type)
        
        if extn:
            if extn in webpage_extns:
                self.typ = URL_TYPE_WEBPAGE
            elif extn in image_extns:
                self.typ = URL_TYPE_IMAGE
            elif extn in stylesheet_extns:
                self.typ = URL_TYPE_STYLESHEET
            elif extn in sound_extns:
                self.typ = URL_TYPE_AUDIO
            elif extn in movie_extns:
                self.typ = URL_TYPE_VIDEO
            else:
                self.typ = URL_TYPE_FILE
        else:
            if content_type:
                # Do some generic tests
                klass, typ = content_type.split('/')
                if klass == 'image':
                    self.typ = URL_TYPE_IMAGE
                elif klass == 'audio':
                    self.typ = URL_TYPE_AUDIO
                elif klass == 'video':
                    self.typ = URL_TYPE_VIDEO
                elif typ == 'html':
                    self.typ = URL_TYPE_WEBPAGE
            else:
                # Do static checks
                if self.is_webpage():
                    self.typ = URL_TYPE_WEBPAGE
                elif self.is_image():
                    self.typ = URL_TYPE_IMAGE
                elif self.is_audio():
                    self.typ = URL_TYPE_AUDIO
                elif self.is_video():
                    self.typ = URL_TYPE_VIDEO
                elif self.is_stylesheet():
                    self.typ = URL_TYPE_STYLESHEET
                else:
                    self.typ = URL_TYPE_FILE

    def make_document(self, data, keywords, description, children):
        """ Return a HarvestManDocument object filling up all the fields """
        
        doc = document.HarvestManDocument(self)
        doc.content = data
        doc.keywords = keywords[:]
        doc.description = description
        doc.content_hash = self.pagehash
        doc.headers = self.contentdict.copy()
        for child in children:
            doc.add_child(child)
        
        doc.lastmodified = self.contentdict.get('last-modified','')
        doc.etag = self.contentdict.get('etag','')
        doc.content_type = self.contentdict.get('content-type','')
        doc.content_encoding = self.contentdict.get('content-encoding','plain')
        return doc
    
    # ============ End - Set Methods =========== #


def test():
    
    # Test code
    HarvestManUrl.TEST = 1
    hulist = [ HarvestManUrl('http://www.yahoo.com/photos/my photo.gif'),
               HarvestManUrl('http://www.rediff.com:80/r/r/tn2/2003/jun/25usfed.htm'),
               HarvestManUrl('http://cwc2003.rediffblogs.com'),
               HarvestManUrl('/sports/2003/jun/25beck1.htm',
                                   'generic', 0, 'http://www.rediff.com', ''),
               HarvestManUrl('http://ftp.gnu.org/pub/lpf.README'),
               HarvestManUrl('http://www.python.org/doc/2.3b2/'),
               HarvestManUrl('//images.sourceforge.net/div.png',
                                   'image', 0, 'http://sourceforge.net', ''),
               HarvestManUrl('http://pyro.sourceforge.net/manual/LICENSE'),
               HarvestManUrl('python/test.htm', 'generic', 0,
                                   'http://www.foo.com/bar/index.html', ''),
               HarvestManUrl('/python/test.css', 'generic',
                                   0, 'http://www.foo.com/bar/vodka/test.htm', ''),
               HarvestManUrl('/visuals/standard.css', 'generic', 0,
                                   'http://www.garshol.priv.no/download/text/perl.html',
                                   'd:/websites'),
               HarvestManUrl('www.fnorb.org/index.html', 'generic',
                                   0, 'http://pyro.sourceforge.net',
                                   'd:/websites'),
               HarvestManUrl('http://profigure.sourceforge.net/index.html',
                                   'generic', 0, 'http://pyro.sourceforge.net',
                                   'd:/websites'),
               HarvestManUrl('#anchor', 'anchor', 0, 
                                   'http://www.foo.com/bar/index.html',
                                   'd:/websites'),
               HarvestManUrl('nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html#__init__#index-after', 'anchor', 0, 'http://nltk.sourceforge.net/lite/doc/api/term-index.html', 'd:/websites'),               
               HarvestManUrl('../../icons/up.png', 'image', 0,
                                   'http://www.python.org/doc/current/tut/node2.html',
                                   ''),
               HarvestManUrl('../eway/library/getmessage.asp?objectid=27015&moduleid=160',
                                   'generic',0,'http://www.eidsvoll.kommune.no/eway/library/getmessage.asp?objectid=27015&moduleid=160'),
               HarvestManUrl('fileadmin/dz.gov.si/templates/../../../index.php',
                                   'generic',0,'http://www.dz-rs.si','~/websites'),
               HarvestManUrl('http://www.evvs.dk/index.php?cPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70','form',True,'http://www.evvs.dk'),
               HarvestManUrl('http://arstechnica.com/reviews/os/macosx-10.4.ars')]
                                  
                                  
    for hu in hulist:
        print 'Full filename = ', hu.get_full_filename()
        print 'Valid filename = ', hu.validfilename
        print 'Local Filename  = ', hu.get_filename()
        print 'Is relative path = ', hu.is_relative_path()
        print 'Full domain = ', hu.get_full_domain()
        print 'Domain      = ', hu.domain
        print 'Local Url directory = ', hu.get_url_directory_sans_domain()
        print 'Canonical Url = ', hu.get_canonical_url()
        print 'Absolute Url = ', hu.get_full_url()
        print 'Absolute Url Without Port = ', hu.get_full_url_sans_port()
        print 'Local Directory = ', hu.get_local_directory()
        print 'Is filename parsed = ', hu.filelike
        print 'Path rel to domain = ', hu.get_relative_url()
        print 'Connection Port = ', hu.get_port_number()
        print 'Domain with port = ', hu.get_full_domain_with_port()
        print 'Relative filename = ', hu.get_relative_filename()
        print 'Anchor url     = ', hu.get_anchor_url()
        print 'Anchor tag     = ', hu.get_anchor()
        print  'Index=>',hu.index
        

if __name__=="__main__":
    test()
