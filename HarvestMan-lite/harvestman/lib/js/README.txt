This folder contains a pure Python port of Rbnarcissus
{http://idontsmoke.co.uk/2005/rbnarcissus/}. The narcissus.py
module contains the main parser code. The jsparse.py module
prints out a dictionary of functions in a javascript source
file passed as argument to it.

For testing the code, use jsparse.py as follows.

$ python testnarcissus.py

Please note that this is an alpha port and it has been tested
for only select javascript samples. However it should work for 
arbitrary javascript code once the bugs are fixed. 

Now the parser closely approximates the original ruby parser.
The parser passes for all sample files directly inside the "js"
folder. It fails for files inside "js/fail" folder. The ruby
parser also exhibits the same behavior.

Note: This folder also contains a working Javascript DOM parser
which is based on regular expressions and a previous HTML
Javascript parser written by me. It does not use the narcissus
code. This parser code resides in jsparser.py and it uses 
the DOM definitions in jsdom.py . 
