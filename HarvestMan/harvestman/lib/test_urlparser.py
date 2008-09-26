import urlparser

# h = urlparser.HarvestManUrl('http://razor.occams.info/') #code/repo/?/govtrack/sec')
h = urlparser.HarvestManUrl('http://razor.occams.info/code/repo/?/govtrack/sex/')
# h = urlparser.HarvestManUrl('http://razor.occams.info/code/repo/govtrack/sec')
print h
## h2 = urlparser.HarvestManUrl('coderef2.c', baseurl=h)
## print h2
## h2 = urlparser.HarvestManUrl('?/govtrack/sec/coderef2.c', baseurl=h)
## print h2
## h2 = urlparser.HarvestManUrl('?/sec/coderef2.c', baseurl=h)
## print h2
## h2 = urlparser.HarvestManUrl('?sec/coderef2.c', baseurl=h)
## print h2
## h2 = urlparser.HarvestManUrl('sec/coderef2.c', baseurl=h)
## print h2
## h2 = urlparser.HarvestManUrl('/sec/coderef2.c', baseurl=h)
## print h2
## h2 = urlparser.HarvestManUrl('govtrack/sec/coderef2.c', baseurl=h)
## print h2
h2 = urlparser.HarvestManUrl('?/govtrack/sec/../coderef2.c', baseurl=h)
print h2
