import urlparser

# Test 1
h = urlparser.HarvestManUrl('http://razor.occams.info/code/repo/?/govtrack/sec')
print h
assert(h.get_full_url()=='http://razor.occams.info/code/repo/?/govtrack/sec')
h2 = urlparser.HarvestManUrl('coderef.c', baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/coderef.c')
h2 = urlparser.HarvestManUrl('?/govtrack/sec/coderef2.c',baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/?/govtrack/sec/coderef2.c')
h2 = urlparser.HarvestManUrl("?/sec/coderef3.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/?/sec/coderef3.c')
h2 = urlparser.HarvestManUrl("?sec/coderef4.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/?sec/coderef4.c')
h2 = urlparser.HarvestManUrl("sec/coderef5.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/sec/coderef5.c')
h2 = urlparser.HarvestManUrl("/sec/coderef6.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/sec/coderef6.c')
h2 = urlparser.HarvestManUrl("govtrack/sec/coderef7.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/govtrack/sec/coderef7.c')
h2 = urlparser.HarvestManUrl("govtrack/?/sec/../coderef8.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/govtrack/?/sec/../coderef8.c')
h2 = urlparser.HarvestManUrl("http://www.foo.com/govtrack/./sec/?/id/../coderef8.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://www.foo.com/govtrack/sec/?/id/../coderef8.c')
h2 = urlparser.HarvestManUrl("../repo2/govtrack/./sec/?/id/../coderef8.c", baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo2/govtrack/sec/?/id/../coderef8.c')

# Test 2
h = urlparser.HarvestManUrl('http://razor.occams.info/code/repo/?/govtrack/sec')
print h
h2 = urlparser.HarvestManUrl('../coderef.c', baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/coderef.c')
h2 = urlparser.HarvestManUrl('govtrack/?/sec/coderef.c', baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/govtrack/?/sec/coderef.c')
h2 = urlparser.HarvestManUrl('../govtrack2/?/../sec/.././sec/coderef.c', baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/govtrack2/?/../sec/.././sec/coderef.c')

print 'Test 3'
# Test 3
h = urlparser.HarvestManUrl('http://razor.occams.info/code/repo/?/govtrack/sec/?')
print h
h2 = urlparser.HarvestManUrl('?/govtrack/?/sec/coderef.c', baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/repo/?/govtrack/?/sec/coderef.c')
h2 = urlparser.HarvestManUrl('../gotrack2/../sec/?/../?/./sec/coderef.c', baseurl=h)
print h2
assert(h2.get_full_url()=='http://razor.occams.info/code/sec/?/../?/./sec/coderef.c')

