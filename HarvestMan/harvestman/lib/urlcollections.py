# -- coding: utf-8
"""
urlcollections.py - Module which defines URL collection
and context classes.

URL collection classes allow a programmer to
create collections (aggregations) of URL objects
with respect to certain contexts. This allows to
treat URL objects belonging to the collection (and hence
the context) as a single unit allowing you to write
code based on the context rather than based on
the URL.

Examples of contexts include stylesheet context
where a web-page and its CSS files forms part of
this context. Other examples are frame contexts, where
a context is associated to all frame URLs originating
from a web-page and page contexts, which basically
associates all URLs in page to the page URL.

This module is part of the HarvestMan program.
For licensing information see the file LICENSE.txt that
is included in this distribution.

Author: Anand B Pillai <abpillai at gmail dot com>

Created Anand B Pillai April 17 2007 Based on inputs from
                                     the EIAO project.

Mod     Anand B Pillai May 26 2007   Added HarvestManAutoUrlCollection
                                     class which automatically categorizes
                                     URLs to contexts. Also, modified
                                     HarvestManUrlCollection class so that
                                     a collection class can be associated
                                     to multiple contexts.
                                     
Copyright (C) 2007, Anand B Pillai.

"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import urltypes
from urlparser import HarvestManUrl

class HarvestManUrlCollectionException(Exception):
    """ Exception class for collections """

    pass

class HarvestManUrlContext(object):
    """ This class defines the base URL context type for HarvestMan """

    # Name for the context
    name = 'BASE_URL_CONTEXT'
    # Description for the context
    description = 'Base type for URL contexts'
    # Source URL type for the context
    sourceurltype = urltypes.URL_TYPE_ANY
    # Bag URL types for the context
    bagurltype = urltypes.URL_TYPE_ANY
    
class HarvestManPageContext(HarvestManUrlContext):
    """ Page context class. This context ties a webpage URL
    with its child URLs """

    # Name for the context
    name = 'PAGE_URL_CONTEXT'
    # Description for the context
    description = 'Context type associating a page to its children'
    # Source URL type for the context
    sourceurltype = urltypes.URL_TYPE_WEBPAGE
    # Bag URL types for the context
    bagurltype = urltypes.URL_TYPE_ANY
    
class HarvestManFrameContext(HarvestManPageContext):
    """ Frame context. This context ties a frameset URL
    to the frame URLs """
    
    # Name for the context
    name = 'FRAME_URL_CONTEXT'
    # Description of the context
    description = 'Context for tying a frameset URL to its frame URLs'
    # Source URL type for the context
    sourceurltype = urltypes.URL_TYPE_FRAMESET
    # Bag URL types for the context
    bagurltype = urltypes.URL_TYPE_FRAME

class HarvestManStyleContext(HarvestManPageContext):
    """ Style context. This context ties a webpage URL to its
    stylesheet (css) URLs """

    # Name for the context
    name = 'STYLE_URL_CONTEXT'
    # Description of the context
    description = 'Context for tying a webpage to its stylesheets'
    # Source URL type for the context
    sourceurltype = urltypes.URL_TYPE_WEBPAGE
    # Bag URL types for the context
    bagurltype = urltypes.URL_TYPE_STYLESHEET


class HarvestManCSSContext(HarvestManPageContext):
    """ CSS context. This context ties a stylesheet URL to any
    URLs defined inside the stylesheet """

    # Name for the context
    name = 'CSS_URL_CONTEXT'
    # Description of the context
    description = 'Context for tying a stylesheet to its child URLs'
    # Source URL type for the context
    sourceurltype = urltypes.URL_TYPE_STYLESHEET
    # Bag URL types for the context
    bagurltype = urltypes.URL_TYPE_ANY

class HarvestManCSS2Context(HarvestManCSSContext):
    """ CSS2 context. This context ties a stylesheet URL to any
    other stylesheets imported in it """

    # Name for the context
    name = 'CSS2_URL_CONTEXT'
    # Description of the context
    description = 'Context for tying a stylesheet to any stylesheets imported in it'
    # Source URL type for the context
    sourceurltype = urltypes.URL_TYPE_STYLESHEET
    # Bag URL types for the context
    bagurltype = urltypes.URL_TYPE_STYLESHEET     
    
class HarvestManUrlCollection(object):
    """ URL collection classes for HarvestMan """

    # This class is designed as a bag for HarvestManUrl
    # objects, tied to a context. The key attributes of this
    # class are a list of such url objects, a main URL
    # object from which the context originates (the 'source'
    # URL object) and a corresponding context.

    def __init__(self, source = None):
        # For efficiency purposes, we do not
        # keep reference to urlobjects, only their indices.
        if source:
            self._source = source.index
            self._sourcetyp = source.typ
        else:
            self._source = None
            self._sourcetyp = urltypes.URL_TYPE_NONE
            
        self._collections = {}

    def _getContext(self, urlobj):
        """ Return the context at which the URL urlobj is to
        be inserted """

        # This class always returns HarvestManPageContext
        return HarvestManPageContext
        
    def addURL(self, urlobj):
        """ Add a url object to the collection """

        # Check if the type of the urlobject matches the
        # bagurltype defined for this context. Here we
        # do a isA check since the url object's type can
        # be a specialized form (derived class) of the
        # bagurltype.

        if not isinstance(urlobj, HarvestManUrl):
            raise HarvestManUrlCollectionException, 'Error: Wrong argument type, expecting HarvestManUrl instance!'

        # For efficiency on memory, we do not append
        # url objects to the list, only their indices.
        # Url objects can be mapped out later using their
        # index from the datamgr object.

        # Context is always HarvestManPageContext
        context = self._getContext(urlobj)
        # print 'CONTEXT for URL %s=>%s' % (urlobj.get_full_url(), context)
        if urlobj.typ.isA(context.bagurltype):
            # Check if this context exists as key in the collections dictionary
            try:
                listofurls = self._collections[context]
                listofurls.append(urlobj.index)
            except KeyError:
                self._collections[context] = [urlobj.index]
        else:
            raise HarvestManUrlCollectionException, 'Error: mismatch in context and bag URL types!'

    def getSourceURL(self):
        """ Return the source URL object """

        return self._source

    def getSourceURLType(self):
        """ Return the type of the source URL object """

        return self._sourcetyp
    
    def getURLs(self, context):
        """ Get list of URL objects for the given context """

        return self._collections.get(context)

    def getAllURLs(self):
        """ Get list of all URL objects for this collection """

        allurls = []
        for urls in self._collections.values():
            allurls.extend(urls)

        return allurls

    def getContextDict(self):
        """ Returns a copy of the internal context dictionary """

        return self._collections.copy()
    
class HarvestManAutoUrlCollection(HarvestManUrlCollection):
    """ A sub-class of HarvestManUrlCollection which
    automatically assigns contexts to URLs """

    def _getContext(self, urlobj):
        """ Return the context at which the URL urlobj is to be inserted """

        # For frames, return HarvestManFrameContext
        # For CSS files
        # 1. Source => webpage, return HarvestManStyleContext
        # 2. Source => stylesheet, return HarvestManCSS2Context
        # For other URLs
        # 1. Source => webpage, return HarvestManPageContext
        # 2. Source => stylesheet, return HarvestManCSSContext

        if urlobj.typ == urltypes.URL_TYPE_FRAME:
            return HarvestManFrameContext

        if urlobj.typ == urltypes.URL_TYPE_STYLESHEET:
            # If source is web-page
            if self._sourcetyp.isA(urltypes.URL_TYPE_WEBPAGE):
                return HarvestManStyleContext
            elif self._sourcetyp.isA(urltypes.URL_TYPE_STYLESHEET):
                return HarvestManCSS2Context
        else:
            # For all other url types
            if self._sourcetyp.isA(urltypes.URL_TYPE_STYLESHEET):
                return HarvestManCSSContext
            else:
                return HarvestManPageContext
