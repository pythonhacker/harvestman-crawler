# -- coding: utf-8
"""
urltypes - Module defining types of URLs and their
relationships.

This module is part of the HarvestMan program.
For licensing information see the file LICENSE.txt that
is included in this distribution.

Author: Anand B Pillai <abpillai at gmail dot com>

Created Anand B Pillai April 18 2007

Copyright (C) 2007, Anand B Pillai.
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

# The URL types are defined as classes with easy-to-use
# string representations. 

# Also, these classes are to be used as "raw", in other words
# ideally the clients of these classes need not create instances
# from the classes. Instead they should use them as given,
# i.e as classes.

class URL_TYPE_META(type):
    """ Meta-class for type classes """

    def __eq__(cls, other):
        return (str(cls) == str(other))

    def __str__(cls):
        return cls.typ

    def isA(cls, baseklass):
        """ Check whether the passed class is a subclass of my class """
        
        return issubclass(cls, baseklass)

class URL_TYPE_ANY(str):
    """ Class representing a URL which belongs to any type.
    This is the base class for all other URL types """

    __metaclass__ = URL_TYPE_META
    
    typ = 'generic'

class URL_TYPE_NONE(URL_TYPE_ANY):
    """ Class representing the None type for URLs """

    __metaclass__ = URL_TYPE_META

    typ = 'none'
    
class URL_TYPE_WEBPAGE(URL_TYPE_ANY):
    """ Class representing a webpage URL. A webpage URL will
    consist of some (X)HTML markup which can be parsed by an
    (X)HTML parser. """

    typ = 'webpage'

class URL_TYPE_BASE(URL_TYPE_WEBPAGE):
    """ Class representing the base URL of a web site. This is
    a special kind of webpage type """

    typ = 'base'

class URL_TYPE_ANCHOR(URL_TYPE_WEBPAGE):
    """ Class representing HTML anchor links. Anchor links are
    part of the same web-page and are typically labels defined
    in the same page or in another page. They start with a '#'"""

    typ = 'anchor'

class URL_TYPE_FRAMESET(URL_TYPE_WEBPAGE):
    """ Class representing a URL which defines HTML frames. The
    children of this URL point to HTML frame documents """

    typ = 'frameset'


class URL_TYPE_FRAME(URL_TYPE_WEBPAGE):
    """ Class representing a URL which acts as the source for an
    HTML 'frame' element. This URL is typically the child of
    an HTML 'frameset' URL """

    typ = 'frame'
    
class URL_TYPE_QUERY(URL_TYPE_ANY):
    """ Class representing a URL which is used to submit queries to
    web servers. Such queries can result in html or non-html result,
    but typically they consist of session IDs """

    typ = 'query'
    
class URL_TYPE_FORM(URL_TYPE_QUERY):
    """ A URL which points to an action, usually used to submit
    form contents to a ReST endpoint. This URL is part of the submit
    action of an HTML <form> element """

    typ = 'form'

class URL_TYPE_IMAGE(URL_TYPE_ANY):
    """ Class representing a URL which points to a binary raster image """

    typ = 'image'

class URL_TYPE_MULTIMEDIA(URL_TYPE_ANY):
    """ Class representing a multimedia (audio/video) URL type """

    typ = 'multimedia'

class URL_TYPE_AUDIO(URL_TYPE_MULTIMEDIA):
    """ Class representing a multimedia audio URL type """

    typ = 'audio'        

class URL_TYPE_VIDEO(URL_TYPE_MULTIMEDIA):
    """ Class representing a multimedia video URL type """

    typ = 'video'        

class URL_TYPE_STYLESHEET(URL_TYPE_ANY):
    """ Class representing a URL which points to a stylesheet (CSS) file """

    typ = 'stylesheet'

class URL_TYPE_JAVASCRIPT(URL_TYPE_ANY):
    """ Class which defines a URL which stands for server-side javascript files """

    typ = 'javascript'

class URL_TYPE_JAPPLET(URL_TYPE_ANY):
    """ Class which defines a URL that points to a Java applet class """

    typ = 'javaapplet'

class URL_TYPE_JAPPLET_CODEBASE(URL_TYPE_ANY):
    """ Class which defines a URL that points to the code-base path of a Java applet """

    typ = 'appletcodebase'
    
class URL_TYPE_FILE(URL_TYPE_ANY):
    """ Class representing a URL which points to any kind of file other
    than webpages, images, stylesheets,server-side javascript files, java
    applets, form queries etc """

    # This is a generic catch-all for all URLs which are not defined so far.
    typ = 'file'

class URL_TYPE_DOCUMENT(URL_TYPE_ANY):
    """ Class which stands for URLs that point to documents which can be
    indexed by search engines. Examples are text files, xml files, PDF files,
    word documents, open office documents etc """

    # This type is not used in HarvestMan, but is useful for indexers
    # which work with HarvestMan, such as swish-e.
    typ = 'document'


# An easy-to-use dictionary for type string to type class mapping

type_map = { 'generic' : URL_TYPE_ANY,
             'webpage' : URL_TYPE_WEBPAGE,
             'base': URL_TYPE_BASE,
             'anchor': URL_TYPE_ANCHOR,
             'query': URL_TYPE_QUERY,
             'form' : URL_TYPE_FORM,
             'image': URL_TYPE_IMAGE,
             'multimedia': URL_TYPE_MULTIMEDIA,
             'audio' : URL_TYPE_AUDIO,
             'video' : URL_TYPE_VIDEO,
             'stylesheet': URL_TYPE_STYLESHEET,
             'javascript': URL_TYPE_JAVASCRIPT,
             'javaapplet': URL_TYPE_JAPPLET,
             'appletcodebase': URL_TYPE_JAPPLET_CODEBASE,
             'file': URL_TYPE_FILE,
             'document': URL_TYPE_DOCUMENT }


def getTypeClass(typename):
    """ Return the type class, given the type name """

    return type_map.get(typename, URL_TYPE_ANY)

if __name__ == "__main__":
    print URL_TYPE_ANY == 'generic'
    print URL_TYPE_WEBPAGE == 'webpage'
    print URL_TYPE_BASE == 'base'
    print URL_TYPE_ANCHOR == 'anchor'
    print URL_TYPE_QUERY == 'query'
    print URL_TYPE_FORM == 'form'
    print URL_TYPE_IMAGE == 'image'
    print URL_TYPE_STYLESHEET == 'stylesheet'
    print URL_TYPE_JAVASCRIPT == 'javascript'
    print URL_TYPE_JAPPLET == 'javaapplet'
    print URL_TYPE_JAPPLET_CODEBASE == 'appletcodebase'
    print URL_TYPE_FILE == 'file'
    print URL_TYPE_DOCUMENT == 'document'
    

    print URL_TYPE_ANY in ('generic','webpage')
    print issubclass(URL_TYPE_ANCHOR, URL_TYPE_WEBPAGE)
    print issubclass(URL_TYPE_BASE, URL_TYPE_WEBPAGE)    
    print type(URL_TYPE_ANCHOR), type(URL_TYPE_ANY)
    
    print URL_TYPE_ANCHOR.isA(URL_TYPE_WEBPAGE)
    print URL_TYPE_ANCHOR.isA(URL_TYPE_ANY)
    print URL_TYPE_IMAGE.isA(URL_TYPE_WEBPAGE)
    print URL_TYPE_ANY.isA(URL_TYPE_ANY)
    print URL_TYPE_IMAGE in ('image','stylesheet')
