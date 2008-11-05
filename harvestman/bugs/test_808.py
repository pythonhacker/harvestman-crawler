# Demoing fix for #808.
# 808: Crawler should try and parse links in "select" options in HTML
# forms.
# Bug: http://trac.eiao.net/cgi-bin/trac.cgi/ticket/808
import sys
sys.path.append('..')
from lib import pageparser
from lib import config
from lib import logger
from lib.common.common import *


SetAlias(config.HarvestManStateObject())
SetAlias(logger.HarvestManLogger())

# First parse with sgmlop parser with option parsing disabled...
print 'Testing with sgmlop parser...'
p = pageparser.HarvestManSGMLOpParser()
p.feed(open('s_municipaux.htm').read())
print 'Asserting link count with option tag disabled...'
assert(len(p.links)==18)

# Now turn on option tag parsing
p.enable_feature('option')
p.feed(open('s_municipaux.htm').read())
print 'Asserting link count with option tag enabled...'
assert(len(p.links)==31)

print 'Testing with pure Python parser...'
p = pageparser.HarvestManSimpleParser()
p.disable_feature('option')
p.feed(open('s_municipaux.htm').read())
print 'Asserting link count with option tag disabled...'
assert(len(p.links)==18)

# Now turn on option tag parsing
p.enable_feature('option')
p.feed(open('s_municipaux.htm').read())
print 'Asserting link count with option tag enabled...'
assert(len(p.links)==31)
