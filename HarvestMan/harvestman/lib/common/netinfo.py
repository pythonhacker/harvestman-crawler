"""
netinfo - Module summarizing information regarding protocols,
ports, file extensions, regular expressions for analyzing URLs etc
for HarvestMan.

Created Anand B Pillai <abpillai at gmail dot com> Feb 22 2008, moving
                                                   content from urlparser.py

Copyright (C) 2008, Anand B Pillai.
"""

import re

URLSEP = '/'          # URL separator character
PROTOSEP = '//'       # String which separates a protocol string from the rest of URL
DOTDOT = '..'         # A convenient name for the .. string
DOT = '.'             # A convenient name for the . string
PORTSEP = ':'         # Protocol separator character, character which separates the protocol
                      # string from rest of URL
BACKSLASH = '\\'      # A convenient name for the backslash character

# Mapping popular protocols to most widely used port numbers
protocol_map = { "http://" : 80,       
                 "ftp://" : 21,
                 "https://" : 443,
                 "file://": 0,
                 "file:": 0
                 }

# Popular image types file extensions
image_extns = ('.bmp', '.dib', '.dcx', '.emf', '.fpx', '.gif', '.ico', '.img',
               '.jp2', '.jpc', '.j2k', '.jpf', '.jpg', '.jpeg', '.jpe',
               '.mng', '.pbm', '.pcd', '.pcx', '.pgm', '.png', '.ppm', 
               '.psd', '.ras', '.rgb', '.tga', '.tif', '.tiff', '.wbmp',
               '.xbm', '.xpm')

# Popular video types file extensions
movie_extns = ('.3gp', '.avi', '.asf','.asx', '.avs', '.bay',
               '.bik', '.bsf', '.dat', '.dv' ,'.dvr-ms', 'flc',
               '.flv', '.ivf', '.m1v', '.m2ts', '.m2v', '.m4v',
               '.mgv', '.mkv', '.mov', '.mp2v', '.mp4', '.mpe',
               '.mpeg', '.mpg', '.ogm', '.qt', '.ratDVD', '.rm',
               '.smi', '.vob', '.wm', '.wmv', '.xvid' )

# Popular audio types file extensions
sound_extns = ('.aac', '.aif', '.aiff', '.aifc', '.aifr', '.amr',
               '.ape' ,'.asf', '.au', '.aud', '.aup', '.bwf', 
               '.cda', '.dct', '.dss', '.dts', '.dvf', '.esu',
               '.eta', '.flac', '.gsm', '.jam', '.m4a', '.m4p',
               '.mdi', '.mid', '.midi', '.mka', '.mod', '.mp1', '.mp2',
               '.mp3', '.mpa', '.mpc', '.mpega', '.msv', '.mus',
               '.nrj', '.nwc', '.nwp', '.ogg', '.psb', '.psm', '.ra',
               '.ram', '.rel', '.sab', '.shn', '.smf', '.snd', '.speex',
               '.tta', '.vox', '.vy3', '.wav', '.wave', '.wma', '.wpk',
               '.wv', '.wvc')

# Most common web page url file extensions
# including dynamic server pages & cgi scripts.
webpage_extns = ('', '.htm', '.html', '.shtm', '.shtml', '.php',
                 '.php3','.php4','.asp', '.aspx', '.jsp','.psp','.pl',
                 '.cgi', '.stx', '.cfm', '.cfml', '.cms', '.ars')


# Document extensions
document_extns = ('.doc','.rtf','.odt','.odp','.ott','.sxw','.stw',
                  '.sdw','.vor','.pdf','.ps')

# Web-page extensions which automatically default to directories
# These are special web-page types which are web-pages as well
# as directories. Most common example is the .ars file extension
# of arstechnica.com.
default_directory_extns = ('.ars',)

# Most common stylesheet url file extensions
stylesheet_extns = ( '.css', )

# Regular expression for matching
# urls which contain white spaces
wspacere = re.compile(r'\s+\S+', re.LOCALE|re.UNICODE)

# Regular expression for anchor tags
anchore = re.compile(r'\#+')

# jkleven: Regex if we still don't recognize a URL address as HTML.  Only
# to be used if we've looked at everything else and URL still isn't
# a known type.  This regex is similar to one in pageparser.py but 
# we changed a few '*' to '+' to get one or more matches.  
# form_re = re.compile(r'[-.:_a-zA-Z0-9]+\?[-.:_a-zA-Z0-9]+=[-.a:_-zA-Z0-9]*', re.UNICODE)

# Made this more generic and lenient.
form_re = re.compile(r'([^&=\?]*\?)([^&=\?]*=[^&=\?])*', re.UNICODE)

# Junk chars which cannot be part of valid filenames
junk_chars = ('?','*','"','<','>','!',':','/','\\')

# Replacement chars
junk_chars_repl = ('',)*len(junk_chars)

# Dirty chars which need to be hex encoded in URLs (apart from white-space)
# We are assuming that there won't be many idiots who would put a backslash in a URL...
dirty_chars = ('<','>','(',')','{','}','[',']','^','`','|')

# These are replaced with their hex counterparts
dirty_chars_repl = ('%3C','%3E','%28','%29','%7B','%7D','%5B','%5D','%5E','%60','%7C')

# %xx char replacement regexp
percent_repl = re.compile(r'\%[a-f0-9][a-f0-9]', re.IGNORECASE)
# params_re = re.compile(r'([-.:_a-zA-Z0-9]*=[-.a:_-zA-Z0-9]*)+', re.UNICODE)
# params_re = re.compile(r'([-.:_a-zA-Z0-9]*=[^\&]*)+', re.UNICODE)

# Regexp which extracts params from query URLs, most generic
params_re = re.compile(r'([^&=\?]*=[^&=\?]*)', re.UNICODE)
# Regular expression for validating a query param group (such as "lang=en")
param_re = re.compile(r'([^&=\?]+=[^&=\?\s]+)', re.UNICODE)

# ampersand regular expression at URL end
ampersand_re = re.compile(r'\&+$')
# question mark regular expression at URL end
question_re = re.compile(r'\?+$')
# Regular expression for www prefixes at front of a string
www_re = re.compile(r'^www(\d*)\.')
# Regular expression for www prefixes anywhere
www2_re = re.compile(r'www(\d*)\.')

# List of TLD (top-level domain) name endings from http://data.iana.org/TLD/tlds-alpha-by-domain.txt

tlds = ['ac', 'ad', 'ae', 'aero', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq',
        'ar', 'arpa', 'as', 'asia', 'at', 'au', 'aw','ax', 'az', 'ba', 'bb', 'bd',
        'be', 'bf', 'bg', 'bh', 'bi', 'biz', 'bj', 'bm', 'bn', 'bo', 'br', 'bs',
        'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cat', 'cc', 'cd', 'cf', 'cg', 'ch',
        'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'coop', 'cr', 'cu', 'cv', 'cx',
        'cy', 'cz', 'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'edu', 'ee', 'eg',
        'er', 'es', 'et', 'eu', 'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb',
        'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gov', 'gp', 'gq',
        'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu',
        'id', 'ie', 'il', 'im', 'in', 'info', 'int', 'io', 'iq', 'ir', 'is',
        'it', 'je', 'jm', 'jo', 'jobs', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn',
        'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls',
        'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mil', 'mk',
        'ml', 'mm', 'mn', 'mo', 'mobi', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu',
        'museum', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'name', 'nc', 'ne', 'net',
        'nf', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'org', 'pa',
        'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'pro', 'ps', 'pt',
        'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd',
        'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'st',
        'su', 'sv', 'sy', 'sz', 'tc', 'td', 'tel', 'tf', 'tg', 'th', 'tj', 'tk',
        'tl', 'tm', 'tn', 'to', 'tp', 'tr', 'travel', 'tt', 'tv', 'tw', 'tz',
        'ua', 'ug', 'uk', 'um', 'us', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi',
        'vn', 'vu', 'wf', 'ws', 'xn--0zwm56d', 'xn--11b5bs3a9aj6g', 'xn--80akhbyknj4f',
        'xn--9t4b11yi5a', 'xn--deba0ad', 'xn--g6w251d', 'xn--hgbk6aj7f53bba',
        'xn--hlcj6aya9esc7a', 'xn--jxalpdlp', 'xn--kgbechtv', 'xn--zckzah',
        'ye', 'yt', 'yu', 'za', 'zm', 'zw']

def get_base_server(server):
    """ Return the base server name of  the passed
    server (domain) name """

    # If the server name is of the form say bar.foo.com
    # or vodka.bar.foo.com, i.e there are more than one
    # '.' in the name, then we need to return the
    # last string containing a dot in the middle.
    if server.count('.') > 1:
        dotstrings = server.split('.')
        # now the list is of the form => [vodka, bar, foo, com]

        # Skip the list for skipping over tld domain name endings
        # such as .org.uk, .mobi.uk etc. For example, if the
        # server is games.mobileworld.mobi.uk, then we
        # need to return mobileworld.mobi.uk, not mobi.uk
        dotstrings.reverse()
        idx = 0

        for item in dotstrings:
            if item.lower() in tlds:
                idx += 1

        return '.'.join(dotstrings[idx::-1])
    else:
        # The server is of the form foo.com or just "foo"
        # so return it straight away
        return server
