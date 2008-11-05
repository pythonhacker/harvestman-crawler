"""
Simple test script which tests narcissus against all sample
javascript files """

from jsparse import print_functions
import sys, os

fcount, passcount = 0, 0

oldstdout = sys.stdout
# Redirect all output to /dev/null
if os.name == 'posix':
    sys.stdout = open('/dev/null','w')
else: 
    sys.stdout = open('.js.tmp','w')

skip = ['editor_main.js','bportugal.js']

for filename in os.listdir("samples"):
    if filename.endswith('.js') and filename not in skip:
        print >> sys.stderr, "Filename => " + filename
        fcount += 1
        try:
            print_functions(os.path.join('samples',filename))
            passcount += 1
        except Exception, e:
            print >> sys.stderr, "Error: " + str(e)

sys.stdout = oldstdout

if fcount:
    print 'Tested with %d samples.' % fcount
    if fcount == passcount:
        print 'All tests passed'
    else:
        print '%d tests passed, %d failed' % (passcount, fcount-passcount)
        
    
