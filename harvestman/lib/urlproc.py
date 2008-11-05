# -- coding: utf-8
""" urlproc.py - Module to process URLs and replace
    entity characters (characters starting with an ampersand
    and ending with a semicolon). 

    All entities here added from
    http://www.w3schools.com/tags/ref_entities.asp
    
    This module is part of the HarvestMan program.
    For licensing information see the file LICENSE.txt that
    is included in this distribution.

   Author: Anand B Pillai <abpillai at gmail dot com>
   
   Modification History
   --------------------
   
   Created - Anand B Pillai 28 Sep 06

   Copyright (C) 2006 Anand B Pillai.
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import unicodedata
import itertools

char_names = ['LESS-THAN SIGN',
              'GREATER-THAN SIGN',
              'AMPERSAND',
              'QUOTATION MARK',
              'SPACE',
              'LATIN CAPITAL LETTER C WITH CEDILLA',
              'LATIN SMALL LETTER C WITH CEDILLA',
              'LATIN CAPITAL LETTER N WITH TILDE',
              'LATIN SMALL LETTER N WITH TILDE',
              'LATIN CAPITAL LETTER THORN',
              'LATIN SMALL LETTER THORN',
              'LATIN CAPITAL LETTER Y WITH ACUTE',
              'LATIN SMALL LETTER Y WITH ACUTE',
              'LATIN SMALL LETTER Y WITH DIAERESIS',
              'LATIN SMALL LETTER SHARP S',
              'LATIN CAPITAL LETTER AE',
              'LATIN CAPITAL LETTER A WITH ACUTE',
              'LATIN CAPITAL LETTER A WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER A WITH GRAVE',
              'LATIN CAPITAL LETTER A WITH RING ABOVE',
              'LATIN CAPITAL LETTER A WITH TILDE',
              'LATIN CAPITAL LETTER A WITH DIAERESIS',
              'LATIN SMALL LETTER AE',
              'LATIN SMALL LETTER A WITH ACUTE',
              'LATIN SMALL LETTER A WITH CIRCUMFLEX',
              'LATIN SMALL LETTER A WITH GRAVE',
              'LATIN SMALL LETTER A WITH RING ABOVE',
              'LATIN SMALL LETTER A WITH TILDE',
              'LATIN SMALL LETTER A WITH DIAERESIS',
              'LATIN CAPITAL LETTER ETH',
              'LATIN CAPITAL LETTER E WITH ACUTE',
              'LATIN CAPITAL LETTER E WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER E WITH GRAVE',
              'LATIN CAPITAL LETTER E WITH DIAERESIS',
              'LATIN SMALL LETTER ETH',
              'LATIN SMALL LETTER E WITH ACUTE',
              'LATIN SMALL LETTER E WITH CIRCUMFLEX',
              'LATIN SMALL LETTER E WITH GRAVE',
              'LATIN SMALL LETTER E WITH DIAERESIS',
              'LATIN CAPITAL LETTER I WITH ACUTE',
              'LATIN CAPITAL LETTER I WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER I WITH GRAVE',
              'LATIN CAPITAL LETTER I WITH DIAERESIS',
              'LATIN SMALL LETTER I WITH ACUTE',
              'LATIN SMALL LETTER I WITH CIRCUMFLEX',
              'LATIN SMALL LETTER I WITH GRAVE',
              'LATIN SMALL LETTER I WITH DIAERESIS',
              'LATIN CAPITAL LETTER O WITH ACUTE',
              'LATIN CAPITAL LETTER O WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER O WITH GRAVE',
              'LATIN CAPITAL LETTER O WITH STROKE',
              'LATIN CAPITAL LETTER O WITH TILDE',
              'LATIN CAPITAL LETTER O WITH DIAERESIS',
              'LATIN SMALL LETTER O WITH ACUTE',
              'LATIN SMALL LETTER O WITH CIRCUMFLEX',
              'LATIN SMALL LETTER O WITH GRAVE',
              'LATIN SMALL LETTER O WITH STROKE',
              'LATIN SMALL LETTER O WITH TILDE',
              'LATIN SMALL LETTER O WITH DIAERESIS',
              'LATIN CAPITAL LETTER U WITH ACUTE',
              'LATIN CAPITAL LETTER U WITH CIRCUMFLEX',
              'LATIN CAPITAL LETTER U WITH GRAVE',
              'LATIN CAPITAL LETTER U WITH DIAERESIS',
              'LATIN SMALL LETTER U WITH ACUTE',
              'LATIN SMALL LETTER U WITH CIRCUMFLEX',
              'LATIN SMALL LETTER U WITH GRAVE',
              'LATIN SMALL LETTER U WITH DIAERESIS',
              'REGISTERED SIGN',
              'PLUS-MINUS SIGN',
              'MICRO SIGN',
              'PILCROW SIGN',
              'MIDDLE DOT',
              'CENT SIGN',
              'POUND SIGN',
              'YEN SIGN',
              'VULGAR FRACTION ONE QUARTER',
              'VULGAR FRACTION ONE HALF',
              'VULGAR FRACTION THREE QUARTERS',
              'SUPERSCRIPT ONE',
              'SUPERSCRIPT TWO',
              'SUPERSCRIPT THREE',
              'INVERTED QUESTION MARK',
              'DEGREE SIGN',
              'BROKEN BAR',
              'SECTION SIGN',
              'LEFT-POINTING DOUBLE ANGLE QUOTATION MARK',
              'RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK',
              'EURO SIGN',
              'SINGLE RIGHT-POINTING ANGLE QUOTATION MARK',
              'SINGLE LEFT-POINTING ANGLE QUOTATION MARK',              
              'PER MILLE SIGN',
              'HORIZONTAL ELLIPSIS',
              'DOUBLE DAGGER',
              'DAGGER',
              'DOUBLE LOW-9 QUOTATION MARK',
              'RIGHT DOUBLE QUOTATION MARK',
              'LEFT DOUBLE QUOTATION MARK',
              'SINGLE LOW-9 QUOTATION MARK',
              'RIGHT SINGLE QUOTATION MARK',
              'LEFT SINGLE QUOTATION MARK',
              'EM DASH',
              'EN DASH',
              'LATIN SMALL LETTER S WITH CARON',
              'LATIN CAPITAL LETTER S WITH CARON',
              'LATIN SMALL LIGATURE OE',
              'LATIN CAPITAL LIGATURE OE',
              'INVERTED EXCLAMATION MARK',
              'CURRENCY SIGN',
              'DIAERESIS',
              'FEMININE ORDINAL INDICATOR',
              'NOT SIGN',
              'TRADE MARK SIGN',
              'MACRON',
              'ACUTE ACCENT',
              'CEDILLA',
              'MASCULINE ORDINAL INDICATOR',
              'MULTIPLICATION SIGN',
              'DIVISION SIGN'
              ]

# Entity characters
ampersand_strings = ('&lt;','&gt;','&amp;','&quot;',
                     '&nbsp;','&Ccedil;','&ccdil;','&Ntilde;',
                     '&ntilde;','&THORN;','&thorn;','&Yacute;',
                     '&yacute;','&yuml;','&szlig;','&AElig;',
                     '&Aacute;','&Acirc;','&Agrave;','&Aring;',
                     '&Atilde;','&Auml;','&aelig;','&acirc;',
                     '&aacute;','&agrave;','&aring;','&atilde;',
                     '&auml;', '&ETH;','&Eacute;','&Ecirc;',
                     '&Egrave;','&Euml;','&eth;','&eacute;',
                     '&ecirc;','&egrave;','&euml;','&Iacute;',
                     '&Icirc;','&Igrave;','&Iuml;','&iacute;',
                     '&icirc;','&igrave;','&iuml;','&Oacute;',
                     '&Ocirc;','&Ograve;','&Oslash;','&Otilde;',
                     '&Ouml;','&oacute;','&ocirc;','&ograve;',
                     '&oslash;','&otilde;','&ouml;','&Uacute;',
                     '&Ucirc;','&Ugrave;','&Uuml;','&uacute;',
                     '&ucirc;','&ugrave;','&uuml;','&reg;',
                     '&plusmn;','&micro;','&para;','&middot;',
                     '&cent;','&pound;','&yen;','&frac14;',
                     '&frac12;','&frac34;','&sup1;','&sup2;',
                     '&sup3;','&iquest;','&deg;','&brvbar;',
                     '&sect;','&laquo;','&raquo;','&euro;',
                     '&rsaquo;','&lsaquo;','&permil;','&hellip;',
                     '&Dagger;','&dagger;','&bdquo;','&rdquo;',
                     '&ldquo;','&sbquo;','&rsquo;','&lsquo;',
                     '&mdash;','&ndash;','&scaron;','&Scaron;',
                     '&oelig;','&OElig;','&iexcl;','&curren;',
                     '&uml;','&ordf;','&not;','&trade;',
                     '&macr;','&acute;','&cedil;','&ordm;','&times;',
                     '&divide;')
                         
                         
def modify_url(url):
    """ Replace entity characters in URLs with the original
    string representations """
    
    for ampersand_string, ucode_name in itertools.izip(ampersand_strings, char_names):
        if url.find(ampersand_string) != -1:
            ucode_char = unicodedata.lookup(ucode_name)            
            try:
                url = url.replace(ampersand_string, ucode_char)
            except UnicodeDecodeError:
                pass
            
    return url

def main():
    # Test code
    url = 'http://www.nbb.be/pub/Home.htm?l=nl&amp;t=ho'
    print modify_url(url)

if __name__ == "__main__":
    main()
