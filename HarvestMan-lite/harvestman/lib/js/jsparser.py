# -- coding: utf-8
""" jsparser - This module provides classes which perform
Javascript extraction from HTML and Javascript parsing to
process DOM objects.

The module consists of two classes. HTMLJSParser
is an HTML Javascript extractor which can extract javascript
code present in HTML pages. JSParser builds upon HTMLJSParser
to provide a Javascript parser which can parse HTML pages
and process Javascript which performs DOM modifications.
Currently this class can process document.write* functions
and Javascript based redirection which changes the location
of a page.

Both classes are written trying to mimic the behaviour
of Firefox (2.0) as closely as possible.

This module is part of the HarvestMan program. For licensing
information see the file LICENSE.txt that is included in this
distribution.

Created Anand B Pillai <abpillai at gmail dot com> Aug 31 2007
Modified Anand B Pillai Oct 2 2007 Added JSParser class and renamed
                                   old JSParser to HTMLJSParser.

Modified Anand B Pillai  Jan 18 2008 Rewrote regular expressions in
                                     HTMLJSParser using pyparsing.

Copyright (C) 2007 Anand B Pillai.

"""

import sys, os
import re
import urllib2
from pyparsing import *
from jsdom import *

class HTMLJSParser(object):
   """ Javascript parser which extracts javascript statements
   embedded in HTML. The parser only performs extraction, and no
   Javascript tokenizing """

   script_content = Literal("<") + Literal("script") + ZeroOrMore(Word(alphas) + Literal("=") + Word(alphanums + "."+ "/"  + '"' + "'")) + Literal(">") + SkipTo(Literal("</") + Literal("script") + Literal(">"), True)

   comment_open = Literal("<!--") + SkipTo("\n", True)
   comment_close = Literal("//") + ZeroOrMore(Word(alphanums)) + Literal("-->")

   brace_open = Literal("{")
   brace_close = Literal("}")
   
   syntaxendre = re.compile(r';$')

   def __init__(self):
      self.comment_open.setParseAction(replaceWith(''))
      self.comment_close.setParseAction(replaceWith(''))
      self.brace_open.setParseAction(replaceWith(''))
      self.brace_close.setParseAction(replaceWith(''))            
      self.reset()
       
   def reset(self):
       self.rawdata = ''
       self.buffer = ''
       self.statements = []
       self.positions = []
       
   def feed(self, data):

       self.rawdata = self.rawdata + data
       # Extract javascript content
       self.extract()
    
   # Internal - parse the HTML to extract Javascript
   def extract(self):

      rawdata = self.rawdata
      for match in self.script_content.scanString(rawdata):
         if not match: continue
         if len(match) != 3: continue
         if len(match[0])==0: continue
         if len(match[0][-1])==0: continue         
         statement = match[0][-1][0]
         # print 'Statement=>',statement
         self.statements.append(statement.strip())
         self.positions.append((match[-2], match[-1]))

      # print 'Length=>',len(self.statements)

      # If the JS is embedded in HTML comments <!--- js //-->
      # remove the comments. This logic takes care of trimming
      # any junk before/after the comments modeling the
      # behaviour of a browser (Firefox) as closely as possible.
      
      flag  = True
      for x in range(len(self.statements)):
         s = self.statements[x]
         # Remove any braces
         s = self.brace_close.transformString(self.brace_open.transformString(s))
         s = self.comment_open.transformString(s)
         s = self.comment_close.transformString(s)         

         # Clean up any syntax end chars
         s = self.syntaxendre.sub('', s).strip()
         
         if s:self.statements[x] = s

      # Trim any empty statements
      # print 'Length=>',len(self.statements)
      # print self.statements
      
class JSParserException(Exception):
   """ An exception class for JSParser """
   
   def __init__(self, error, context=None):
      self._error = error
      # Context: line number, js statement etc.
      self._context =context

   def __str__(self):
      return str(self._error)

   def __repr__(self):
      return '@'.join((str(self._error), str(self._context)))

  
class JSParser(object):
   """ Parser for Javascript DOM. This class can be used to parse
   javascript which contains DOM binding statements. It returns
   a DOM object. Calling a repr() on this object will produce
   the modified DOM text """

   # TODO: Rewrite this using pyparsing
   
   # Start signature of document.write* methods
   re1 = re.compile(r"(document\.write\s*\()|(document\.writeln\s*\()")
   
   re3 = re.compile(r'(?<![document\.write\s*|document\.writeln\s*])\(.*\)', re.MULTILINE)
   # End signature of document.write* methods
   re4 = re.compile(r'[\'\"]\s*\)|[\'\"]\s*\);', re.MULTILINE)

   # Pattern for contents inside document.write*(...) methods
   # This can be either a single string enclosed in quotes,
   # a set of strings concatenated using "+" or a set of
   # string arguments (individual or concatenated) separated
   # using commas. Text can be enclosed either in single or
   # double quotes.

   # Valid Examples...
   # 1. document.write("<H1>This is a heading</H1>\n");
   # 2. document.write("Hello World! ","Hello You! ","<p style='color:blue;'>Hello World!</p>");
   # 3. document.write("Hi, this is " + "<p>A paragraph</p>" + "and this is "  + "<p>Another one</p>");
   # 4. document.write("Hi, this is " + "<p>A paragraph</p>", "and this is "  + "<p>Another one</p>");

   # Pattern for content
   re5 = re.compile(r'(\".*\")|(\'.*\')', re.MULTILINE)
   re6 = re.compile(r'(?<=[\"\'\s])[\+\,]+')
   re7 = re.compile(r'(?<=[\"\'])(\s*[\+\,]+)')   
   re8 = re.compile(r'^[\'\"]|[\'\"]$')
   
   # JS redirect regular expressions
   # Form => window.location.replace("<url>") or window.location.assign("<url>")
   # or location.replace("<url>") or location.assign("<url>")
   jsredirect1 = re.compile(r'((window\.|this\.)?location\.(replace|assign))(\(.*\))', re.IGNORECASE)
   # Form => window.location.href="<url>" or location.href="<url>"
   jsredirect2 = re.compile(r'((window\.|this\.)?location(\.href)?\s*\=\s*)(.*)', re.IGNORECASE)
   
   quotechars = re.compile(r'[\'\"]*')
   newlineplusre = re.compile(r'\n\s*\+')
      
    
   def __init__(self):
      self._nflag = False
      self.parser = HTMLJSParser()
      self.resetDOM()
      self.statements = []
      self.js = []
      pass

   def resetDOM(self):
      self.page = None
      self.page = Window()
      self.page.document = Document()
      self.page.location = Location()
      self.locnchanged = False
      self.domchanged = False
      
   def _find(self, data):
      # Search for document.write* statements and return the
      # match group if found. Also sets the internal newline
      # flag, depending on whether a document.write or
      # document.writeln was found.
      self._nflag = False
      m = self.re1.search(data)
      if m:
         grp = m.group()
         if grp.startswith('document.writeln'):
            self._nflag = True
         return m

   def parse_url(self, url):
      """ Parse data from the given URL """
      
      try:
         data = urllib2.urlopen(url).read()
         # print 'fetched data'
         return self.parse(data)
      except Exception, e:
         print e
         
         
   def parse(self, data):
      """ Parse HTML, extract javascript and process it """

      self.js = []
      self.resetDOM()
      self.parser.reset()
      
      self.page.document.content = data
      
      # Create a jsparser to extract content inside <script>...</script>
      # print 'Extracting js content...'
      self.parser.feed(data)
      self.js = self.parser.statements[:]
      
      # print 'Extracted js content.'
      # print 'Found %d JS statements.' % len(self.js)
      
      # print 'Processing JS'
      for x in range(len(self.js)):
         statement = self.js[x]

         # First check for JS redirects and
         # then for JS document changes.
         jsredirect = self.processLocation(statement)
         if jsredirect:
            # No need to process further since we are redirecting
            # the location
            break
         else:
            # Further process the URL for document changes
            position = self.parser.positions[x]
            
            rawdata = statement.strip()
            self._feed(rawdata)
         
            if len(self.statements):
               self.processDocument(position)

      # Set flags for DOM/Location change
      self.locnchanged = self.page.location.hrefchanged
      self.domchanged = self.page.document.contentchanged

      # print 'Processed JS.'
      
   def processDocument(self, position):
      """ Process DOM document javascript """

      # The argument 'position' is a two tuple
      # containing the start and end positions of
      # the javascript tags inside the document.

      dom = self.page.document
      start, end = position
      
      # Reset positions on DOM content to empty string
      dom.chomp(start, end)
      
      for text, newline in self.statements:
         if newline:
            dom.writeln(text)
         else:
            dom.write(text)

      # Re-create content
      dom.construct()

   # Internal - validate URL strings for Javascript
   def validate_url(self, urlstring):
      """ Perform validation of URL strings """
      
      # Validate the URL - This follows Firefox behaviour
      # In firefox, the URL might be or might not be enclosed
      # in quotes. However if it is enclosed in quotes the quote
      # character at start and begin should match. For example
      # 'http://www.struer.dk/webtop/site.asp?site=5',
      # "http://www.struer.dk/webtop/site.asp?site=5" and
      # http://www.struer.dk/webtop/site.asp?site=5 are valid, but
      # "http://www.struer.dk/webtop/site.asp?site=5' and
      # 'http://www.struer.dk/webtop/site.asp?site=5" are not.
      if urlstring.startswith("'") or urlstring.startswith('"'):
         if urlstring[0] != urlstring[-1]:
            # Invalid URL
            return False
         
      return True

   def make_valid_url(self, urlstring):
      """ Create a valid URL string from the passed urlstring """
      
      # Strip off any leading/trailing quote chars
      urlstring = self.quotechars.sub('',urlstring)
      return urlstring.strip()
     
   def processLocation(self, statement):
      """ Process any changes in document location """

      locnchanged = False
      
      for line in statement.split('\n'):
         
         # print 'Expression=>',statement
         m1 = self.jsredirect1.search(line)
         if m1:
            tokens = self.jsredirect1.findall(line)
            if tokens:
                urltoken = tokens[0][-1]
                # Strip of trailing and leading parents
                url = urltoken.replace('(','').replace(')','').strip()
                # Validate URL
                if self.validate_url(url):
                   url = self.make_valid_url(url)
                   locnchanged = True
                   self.page.location.replace(url)
         else:
            m2 = self.jsredirect2.search(line)
            if m2:
               tokens = self.jsredirect2.findall(line)
               urltoken = tokens[0][-1]
               # Strip of trailing and leading parents
               url = urltoken.replace('(','').replace(')','').strip()
               if tokens and self.validate_url(url):
                  url = self.make_valid_url(url)
                  locnchanged = True
                  self.page.location.replace(url)                  
                  locnchanged = True

      return locnchanged
                
   def _feed(self, data):
      """ Internal method to feed data to process DOM document """
      
      self.statements = []
      self.rawdata = data
      self.goahead()
      self.process()
      
   def tryQuoteException(self, line):
      """ Check line for mismatching quotes """
      
      ret = 0
      # Check line for mismatching quotes
      if line[0] in ("'",'"') and line[-1] in ("'",'"'):
         ret = 1
         if line[0] != line[-1]:
            raise JSParserException("Mismatching quote characters", line)

      return ret
   
   def process(self):
      """ Process DOM document related javascript """

      # Process extracted statements
      statements2 = []
      for s, nflag in self.statements:

         m = self.re5.match(s)
         if m:
            # Well behaved string
            if self.re6.search(s):
               m = self.re7.search(s)
               newline = self.newlineplusre.match(m.groups(1)[0])
               items = self.re6.split(s)
               
               # See if any entry in the list has mismatching quotes, then
               # raise an error...
               for item in items:
                  # print 'Item=>',item
                  self.tryQuoteException(item)
                  
               # Remove any trailing or beginning quotes from the items
               items = [self.re8.sub('',item.strip()) for item in items]
               # Replace any \" with "
               items = [item.replace("\\\"", '"') for item in items]

               # If the javascript consists of many lines with a +
               # connecting them, there is a very good chance that it
               # breaks spaces across multiple lines. In such case we
               # need to join the pieces with at least a space.
               if newline:
                  s = ' '.join(items)
               else:
                  # If it does not consist of newline and a +, we don't
                  # need any spaces between the pieces.
                  s = ''.join(items)                  

            # Remove any trailing or beginning quotes from the statement
            s = self.re8.sub('', s)
            statements2.append((s, nflag))
         else:
            # Ill-behaved string, has some strange char either beginning
            # or end of line which was passed up to here.
            # print 'no match',s
            # Split and check for mismatched quotes
            if self.re6.search(s):
               items = self.re6.split(s)
               # See if any entry in the list has mismatching quotes, then
               # raise an error...
               for item in items:
                  self.tryQuoteException(item)
                  
            else:
               # Ignore it
               pass
            
      self.statements = statements2[:]
      pass
   
   def goahead(self):

      rawdata = self.rawdata
      self._nflag = False
      
      # Scans the document for document.write* statements
      # At the end of parsing, an internal DOM object
      # will contain the modified DOM if any.

      while rawdata:
         m = self._find(rawdata)
         if m:
            # Get start of contents
            start = m.end()
            rawdata = rawdata[start:]
            # Find the next occurence of a ')'
            # First exclude any occurences of pairs of parens
            # in the content
            contentdata, pos = rawdata, 0
            m1 = self.re3.search(contentdata)
            while m1:
               contentdata = contentdata[m1.end():]
               pos = m1.end()
               # print 'Pos=>',pos
               # print contentdata
               m1 = self.re3.search(contentdata)

            m2 = self.re4.search(rawdata, pos)
            if not m2:
               raise JSParserException('Missing end paren!')
            else:
               start = m2.start()
               statement = rawdata[:start+1].strip()
               # print 'Statement=>',statement
               # If statement contains a document.write*, then it is a
               # botched up javascript, so raise error
               if self.re1.search(statement):
                  raise JSParserException('Invalid javascript', statement)
               
               # Look for errors like mismatching start and end quote chars
               if self.tryQuoteException(statement) == 1:
                  pass
               elif statement[0] in ('+','-') and statement[-1] in ("'", '"'):
                  # Firefox seems to accept this case
                  print 'warning: garbage char "%s" in beginning of statement!' % statement[0]
               else:
                  raise JSParserException("Garbage in beginning/end of statement!")
                  
               # Add statement to list
               self.statements.append((statement, self._nflag))
               rawdata = rawdata[m2.end():]
         else:
            # No document.write* content found
            # print 'no content'
            break

   def getDocument(self):
      """ Return the DOM document object, this can be used to get
      the modified page if any """

      return self.page.document

   def getLocation(self):
      """ Return the DOM Location object, this can be used to
      get modified URL if any """

      return self.page.location

   def getStatements(self):
      """ Return the javascript statements in a list """

      return self.parser.statements

   
def localtests():
    print 'Doing local tests...'
    
    P = JSParser()
    P.parse(open('samples/bportugal.html').read())
    assert(repr(P.getDocument())==open('samples/bportugal_dom.html').read())
    assert(P.domchanged==True)
    assert(P.locnchanged==False)
    
    P.parse(open('samples/jstest.html').read())
    assert(repr(P.getDocument())==open('samples/jstest_dom.html').read())
    assert(P.domchanged==True)
    assert(P.locnchanged==False)

    P.parse(open('samples/jsnodom.html').read())
    assert(repr(P.getDocument())==open('samples/jsnodom.html').read())
    assert(P.domchanged==False)
    assert(P.locnchanged==False)    
    

    P.parse(open('samples/jstest2.html').read())
    assert(repr(P.getDocument())==open('samples/jstest2_dom.html').read())
    assert(P.domchanged==True)
    assert(P.locnchanged==False)    

    P.parse(open('samples/jstest3.html').read())
    assert(repr(P.getDocument())==open('samples/jstest3_dom.html').read())
    assert(P.domchanged==True)
    assert(P.locnchanged==False)

    P.parse(open('samples/jsredirect.html').read())
    assert(repr(P.getDocument())==open('samples/jsredirect.html').read())
    assert(P.domchanged==False)
    assert(P.locnchanged==True)
    assert(P.getLocation().href=="http://www.struer.dk/webtop/site.asp?site=5")

    P.parse(open('samples/jsredirect2.html').read())
    assert(repr(P.getDocument())==open('samples/jsredirect2.html').read())
    assert(P.domchanged==False)
    assert(P.locnchanged==True)
    assert(P.getLocation().href=="http://www.struer.dk/webtop/site.asp?site=5")    

    P.parse(open('samples/jsredirect3.html').read())
    assert(repr(P.getDocument())==open('samples/jsredirect3.html').read())
    assert(P.domchanged==False)
    assert(P.locnchanged==True)
    assert(P.getLocation().href=="fra/index.php")

    P.parse(open('samples/jsredirect4.html').read())
    assert(repr(P.getDocument())==open('samples/jsredirect4.html').read())
    assert(P.domchanged==False)
    assert(P.locnchanged==True)
    assert(P.getLocation().href=="http://www.szszm.hu/szigetszentmiklos.hu")
    
    P.parse(open('samples/jsredirect5.html').read())
    assert(repr(P.getDocument())==open('samples/jsredirect5.html').read())
    assert(P.domchanged==False)
    assert(P.locnchanged==True)
    assert(P.getLocation().href=="sopron/main.php")    

    print 'All local tests passed.'

def webtests():
    print 'Starting web tests...'
    P = JSParser()

    urls = [("http://www.skien.kommune.no/", 0), ("http://www.bayern.de/", 7),
            ("http://www.agsbs.ch/", 2), ("http://www.froideville.ch/", 1)]

    for url, number in urls:
       print 'Parsing URL %s...' % url
       P.parse_url(url)
       print 'Found %d statements.' % len(P.getStatements())
       assert(number==len(P.getStatements()))
       
def experiments():
   P = JSParser()
   P.parse(open('samples/test.html').read())
   
if __name__ == "__main__":
   localtests()
   #webtests()
   #experiments()
   
   
    


