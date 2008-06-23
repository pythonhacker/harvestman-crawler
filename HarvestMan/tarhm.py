import sys, os
import shutil
import time
import ftplib
import getpass

srcdir = sys.argv[1]
# Copy to /tmp
#os.system('cp -r %s /tmp/HarvestMan-2.0' % srcdir)
#curdir = os.path.abspath('.')
# Change to /tmp
#os.chdir('/tmp')
#srcdir = 'HarvestMan-2.0'
# Remove .pyc files
os.system('rm -rf `find %s -name \*.pyc`' % srcdir)
# Remove files starting with #
os.system('rm -rf `find %s -name \#*`' % srcdir)
# Remove files ending with ~
os.system('rm -rf `find %s -name \*~`' % srcdir)
# Remove .svn directories
os.system('rm -rf `find %s -name \.svn`' % srcdir)
# Remove any saved www* entries
os.system('rm -rf `find %s -name www*`' % srcdir)
# Remove any other saved files...
# Remove any .hpf files
os.system('rm -rf `find %s -name \*.hpf`' % srcdir)
# Remove any other .com/.org sites
os.system('rm -rf `find %s -regex ".*\.org"`' % srcdir)
os.system('rm -rf `find %s -regex ".*\.com"`' % srcdir)
# Remove any other stray html
os.system('rm -rf `find %s -name \*.htm\* | grep -v samples | grep -v bugs | grep -v templates`' % srcdir)
# Remove any .bidx files
os.system('rm -rf `find %s -name \.bidx*`' % srcdir)
# Now tar it up...
tarfile = time.strftime('HarvestMan-2.0alpha%d%m%Y.tar.gz', time.localtime())
ret = os.system('tar -czvf %s %s' % (tarfile, srcdir))
# Clean up the folder
os.system('rm -rf ' + srcdir)
ret = raw_input('Go ahead with upload [y/n] ? ')
if ret.strip().lower() != 'y':
    sys.exit('Done.')
    
# Upload it to harvestmanontheweb.com
user=raw_input('Enter FTP username: ').strip()
passw=getpass.getpass('Enter FTP password: ').strip()
print 'Logging into harvestmanontheweb.com...',
ftp = ftplib.FTP('www.harvestmanontheweb.com')
ftp.login(user, passw)
print 'done.'
print 'Changing directory to www/packages/2.0...',
ftp.cwd('www/packages/2.0')
print 'done.'
t1 = time.time()
print 'Transferring file %s...' % tarfile
ftp.storbinary('STOR %s' % tarfile, open(tarfile,'rb'))
ftp.close()
print 'Uploaded file %s in %.1f seconds' % (tarfile , time.time()-t1)
# Remove the tarfile
os.system('rm -rf ' + tarfile)
os.chdir(curdir)


