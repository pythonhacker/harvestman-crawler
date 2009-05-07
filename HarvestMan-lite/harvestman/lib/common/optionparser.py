# -- coding: utf-8
"""
optionparser.py - Generic option parser class. This class
can be used to write code that will parse command line options
for an application by invoking one of the standard Python
library command argument parser modules optparse or
getopt.

The class first tries to use optparse. It it is not there
(< Python 2.3), it invokes getopt. However, this is
transparent to the application which uses the class.

The class requires a list with tuple entries of the following
form for each command line option.

('option_var', 'short=<short option>','long=<long option>',
'help=<help string>', 'meta=<meta variable>','default=<default value>',
'type=<option type>')

where, 'option_var' is the key for the option in the final
dictionary of option-value pairs. The rest are strings of
the form 'key=value', where 'key' is borrowed from the way
optparse represents each variables for an option setting.

To parse the arguments, call the method 'parse_arguments'.
The return value is a dictionary of the option-value pairs.

This module is part of the HarvestMan program. For licensing
information see the file LICENSE.txt that is included in this
distribution.

This module was originally created as an ASPN cookbook
recipe http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/425345 .
The current module is a slightly modified form of the recipe.

Author: Anand B Pillai <anand at harvestmanontheweb.com>

Created: Feb 11 2007 by Anand B Pillai 


Copyright (C) 2007, Anand B Pillai.

"""

import sys

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

class GenericOptionParserError(Exception):
    
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return str(self.value)
    
class GenericOptionParser:
    """ Generic option parser using
    either optparse or getopt """

    def __init__(self, optlist, usage='', description=''):
        self._optlist = self.__process_optlist(optlist)
        self._optdict = {}
        self._args = ''
        self._usage = usage
        self._description = description
        self.maxw = 24

    def __process_optlist(self, optlist):
        """ Process options list """

        optionslist = []

        for optiontuple in optlist:
            # Option destination is first item
            optiondest = optiontuple[0]
            # Create empty dictionary
            itemdict = {}
            # Convert rest to a dictionary
            for item in optiontuple[1:]:
                key,val = item.split('=', 1)
                itemdict[key] = val

            # Append option dest as first val
            # and itemdict as second val in a list
            optionslist.append([optiondest, itemdict])

        return optionslist
            
    def parse_arguments(self):
        """ Parse command line arguments and
        return a dictionary of option-value pairs """

        try:
            self.optparse = __import__('optparse')
            # For invoking help, when no arguments
            # are passed.
            if len(sys.argv)==1:
                sys.argv.append('-h')

            self._parse_arguments1()
        except ImportError:
            try:
                import getopt
                self.getopt = __import__('getopt')                
                self._parse_arguments2()
            except ImportError:
                raise GenericOptionParserError,'Fatal Error: No optparse or getopt modules found'

        return (self._optdict, self._args)
                
    def _parse_arguments1(self):
        """ Parse command-line arguments using optparse """

        p = self.optparse.OptionParser(usage=self._usage, description=self._description)
        
        for option, itemdict in self._optlist:
            # Default action is 'store'
            action = 'store'
            # Short option string
            sopt = itemdict.get('short','')
            # Long option string
            lopt = itemdict.get('long','')
            # Help string
            helpstr = itemdict.get('help','')
            # Meta var
            meta = itemdict.get('meta','')
            # Default value
            defl = itemdict.get('default','')
            # Default type is 'string'
            typ = itemdict.get('type','string')
            
            # If bool type...
            if typ == 'bool':
                action = 'store_true'
                defl = bool(str(defl) == 'True')

            if sopt: sopt = '-' + sopt
            if lopt: lopt = '--' + lopt
            
            # Add option
            p.add_option(sopt,lopt,dest=option,help=helpstr,metavar=meta,action=action,
                         default=defl)

        (options,args) = p.parse_args()
        self._optdict = options.__dict__
        self._args = args
        
    def _parse_arguments2(self):
        """ Parse command-line arguments using getopt """

        # getopt requires help string to
        # be generated.
        if len(sys.argv)==1:
            sys.exit(self._usage())
        
        shortopt,longopt='h',['help']
        # Create short option string and long option
        # list for getopt
        for option, itemdict in self._optlist:
            sopt = itemdict.get('short','')
            lopt = itemdict.get('long','')
            typ = itemdict.get('type','string')            
            defl = itemdict.get('default','')

            # If bool type...
            if typ == 'bool':
                defl = bool(str(defl) == 'True')
            # Set default value
            self._optdict[key] = defl

            if typ=='bool':
                if sopt: shortopt += sopt
                if lopt: longopt.append(lopt)
            else:
                if sopt: shortopt = "".join((shortopt,sopt,':'))
                if lopt: longopt.append(lopt+'=')

        # Parse
        (optlist,args) = self.getopt.getopt(sys.argv[1:],shortopt,longopt)
        self._args = args
        
        # Match options
        for opt,val in optlist:
            # Invoke help
            if opt in ('-h','--help'):
                sys.exit(self._usage())
                
            for option,itemdict in self._optlist:
                sopt = '-' + itemdict.get('short','')
                lopt = '--' + itemdict.get('long','')
                typ = itemdict.get('type','string')
                
                if opt in (sopt,lopt):
                    if typ=='bool': val = True
                    self._optdict[key]=val
                    break

    def _split_help_str(self, help):
        """ Split help string into many lines """

        # According to following
        # Max number of chars per line is 52
        # If char count exceeds, split line,
        # preserving words.
        maxlen = 53
        helps,count=[],0
        if len(help)<=maxlen:
            return help
        
        while help:
            if len(help)<maxlen:
                helps.append(self.maxw*' ' + help.strip())
                break
            else:
                piece = help[0:maxlen]
                # Find max index of space char in this piece
                sindx = piece.rfind(' ')
                # Split according to space char
                piece = piece[0:sindx]
                if count>0:
                    piece = self.maxw*' ' + piece
                helps.append(piece)
                help = help[sindx+1:]
                count += 1
                
        return '\n'.join(helps)
    
    def _usage(self):
        """ Generate and return a help string
        for the program, similar to the one
        generated by optparse """

        if self._usage:
            usage = [self._usage]
        else:
            usage = ["usage: %s [options]\n\n" % sys.argv[0]]
            usage.append("options:\n")

        options = [('  -h, --help', 'show this help message and exit\n')]
        maxlen = 0
        for option, itemdict in self._optlist:
            sopt = itemdict.get('short','')
            lopt = itemdict.get('long','')
            help = itemdict.get('help','')
            meta = itemdict.get('meta','')
            
            optstr = ""
            if sopt: optstr="".join(('  -',sopt,' ',meta))
            if lopt: optstr="".join((optstr,', --',lopt))
            if meta: optstr="".join((optstr,'=',meta))

            help = self._split_help_str(help)
                
            l = len(optstr)
            if l>maxlen: maxlen=l
            options.append((optstr,help))
            
        for x in range(len(options)):
            optstr = options[x][0]
            helpstr = options[x][1]
            if maxlen<self.maxw - 1:
                usage.append("".join((optstr,(maxlen-len(optstr) + 2)*' ', helpstr,'\n')))
            elif len(optstr)<self.maxw - 1:
                usage.append("".join((optstr,(self.maxw-len(optstr))*' ', helpstr,'\n')))
            else:
                usage.append("".join((optstr,'\n',self.maxw*' ', helpstr,'\n')))                

        return "".join(usage)

if __name__=="__main__":
    l=[ ('infile', 'short=i','long=in','help=Input file for the program',
                    'meta=IN'),
        ('outfile', 'short=o','long=out','help=Output file for the program',
                    'meta=OUT'),
        ('verbose', 'short=V','long=verbose','help=Be verbose in output',
                    'type=bool') ]

    g=GenericOptionParser(l)
    optdict = g.parse_arguments()
 
    for key,value in optdict.items():
         # Use the option and the value in
         # your program
         print key,value
