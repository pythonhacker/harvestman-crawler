#!/usr/bin/env python

from distutils.core import setup
from distutils.ccompiler import CCompiler, new_compiler

import os, sys
import zipfile
import shutil
import stat
import urllib
import tarfile

BUILD_SGMLOP=False

if os.name == 'posix':
    BUILD_SGMLOP = True
    
pyparsing_surl = 'http://cheeseshop.python.org/packages/source/p/pyparsing/pyparsing-1.4.8.tar.gz'
webpy_surl = 'http://webpy.org/static/web.py-0.23.tar.gz'

# Python 2.4 and lesser do not have this function in the tarfile module...
def extractall(self, path=".", members=None):
    """Extract all members from the archive to the current working
       directory and set owner, modification time and permissions on
       directories afterwards. `path' specifies a different directory
       to extract to. `members' is optional and must be a subset of the
       list returned by getmembers().
    """
    directories = []

    if members is None:
        members = self

    for tarinfo in members:
        if tarinfo.isdir():
            # Extract directory with a safe mode, so that
            # all files below can be extracted as well.
            try:
                os.makedirs(os.path.join(path, tarinfo.name), 0777)
            except EnvironmentError:
                pass
            directories.append(tarinfo)
        else:
            self.extract(tarinfo, path)

    # Reverse sort directories.
    directories.sort(lambda a, b: cmp(a.name, b.name))
    directories.reverse()

    # Set correct owner, mtime and filemode on directories.
    #for tarinfo in directories:
    #    path = os.path.join(path, tarinfo.name)
    #    try:
    #        self.chown(tarinfo, path)
    #        self.utime(tarinfo, path)
    #        self.chmod(tarinfo, path)
    #    except ExtractError, e:
    #        #if self.errorlevel > 1:
    #        #    raise
    #        #else:
    #        self._dbg(1, "tarfile: %s" % e)

# Dynamically add the 'extractall' function and related error class...
if not hasattr(tarfile.TarFile, 'extractall'):
    setattr(tarfile.TarFile, 'extractall', extractall)
    class ExtractError(tarfile.TarError): pass
    setattr(tarfile.ExtractError, 'ExtractError', ExtractError)
    
def site_packages_dir():

    import site
    
    modpath = site.os.__file__
    moddir = os.path.dirname(modpath)
    sitedir = os.path.join(moddir, 'site-packages')
    
    # On 64 bit this returns <prefix>/lib64, but distutils copies to
    # <prefix>/lib, so we also do the same thing here.
    paths = sitedir.split(os.sep)
    for x in range(len(paths)):
        if paths[x] == 'lib64':
            paths[x] = 'lib'
    sitedir = os.sep.join(paths)
            
    return sitedir
    
def locate_executable(name):

    path = os.environ.get('PATH')
    if os.name == 'posix':
        paths = path.split(':')
    elif os.name == 'nt':
        paths = path.split(';')
        
    for p in paths:
        exepath = os.path.join(p, name)
        if os.path.isfile(exepath):
            return exepath

    return ''
    
def install_pyparsing():
    print 'Installing pyparsing...'
    return install_package_from_source(name='pyparsing',url=pyparsing_surl, try_easy_install=False)

def install_webpy():
    print 'Installing web.py...'
    return install_package_from_source(name='webpy',url=webpy_surl, try_easy_install=False)
    
def install_package_from_source(name, url, try_easy_install=True):
    
    # Can't rely on easy_install being there ...
    easy_install, flag = False, True
    if try_easy_install:
        easy_install = locate_executable('easy_install')
        
    if easy_install:
        try:
            import pkg_resources
            
            print 'Installing % using easy_install...' % name
            return os.system(' '.join((easy_install, url)))
        except ImportError:
            print 'easy_install is not setup correctly'
            
    if flag:
        print 'Installing directly from source...'
        temp_dir = os.path.join('deps','build_%s' % name)
        
        if not os.path.isdir(temp_dir):
            try:
                os.makedirs(temp_dir)
            except OSError, e:
                print e
                return -1

        fname = os.path.join(temp_dir, '%s.tar.gz' % name )

        try:
            print 'Retrieving %s...' % url
            urllib.urlretrieve(url, fname)
        except Exception, e:
            print e
            return -1

        child_dir = ''
        
        if os.path.isfile(fname):
            print 'Extracting %s...' % fname
            try:
                f = tarfile.open(fname, 'r:gz')
                f.extractall(temp_dir)
                l = os.listdir(temp_dir)
                l.remove('%s.tar.gz' % name)
                child_dir = os.path.join(temp_dir, l[0])
            except tarfile.TarError, e:
                print e
                return -1
        else:
            print 'Error retrieving %s.' % url
            return -1

        curdir = os.path.abspath(os.curdir)
        if child_dir:
            os.chdir(child_dir)
            ret = os.system('python setup.py install')
        else:
            print 'Error in extracting %s.' % fname
            return -1

        os.chdir(curdir)
        
        try:
            shutil.rmtree(temp_dir)
        except (IOError, OSError), e:
            print e

        return ret

    return -1

def create_shortcut(app):

    print 'Creating application link for %s...' % app
    
    sitedir = site_packages_dir()
    print 'Sitedir=>',sitedir
    prefix = sys.prefix
    exe_prefix = os.path.join(prefix, 'bin')
    
    app_path = os.path.join(exe_prefix, app)
    try:
        envp = "env" # os.path.join(exe_prefix, 'env')
        modpath = os.path.join(sitedir, 'harvestman', 'apps', app + '.py')
        string = '#!/bin/sh\n%s python %s $*' % (envp, modpath)
        open(app_path, 'w').write(string)
        # Make it executable...
        os.chmod(app_path, stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
        return 0
    except IOError, e:
        print e
        return -1

def check_webpy():

    try:
        import web
        from web import form
        from web import template
        return float(web.__version__)>=0.2
    except ImportError, AttributeError:
        return False
    
def check_sgmlop():

    html="""\
    <html><
    title>Test sgmlop</title>
    <body>
    <p>This is a pargraph</p>
    <img src="img.jpg"/>
    <a href="http://www.python.org'>Python</a>
    </body>
    </html>
    """
    
    try:
        import sgmlop
        print 'Found sgmlop...'
        
        class DummyHandler(object):
            links = []
            def finish_starttag(self, tag, attrs):
                self.links.append(tag)
                pass

        print 'Testing sgmlop...'
        parser = sgmlop.SGMLParser()
        parser.register(DummyHandler())
        parser.feed(html)
        # Check if we got all the links...
        if len(DummyHandler.links)==4:
            print 'tested sgmlop ok'
            return 0
        else:
            print 'sgmlop test failed, disabling sgmlop...'
            return -1
    except ImportError:
        return -1

def check_ccompiler():
    # Check if we can compile C programs, currently just instantiates
    # a compiler object... need to see if we should do further than
    # this...
    try:
        ccomp = new_compiler()
        return ccomp
    except Exception, e:
        print e
        sys.exit(1)
        
def build_sgmlop():

    print 'Building sgmlop C extension...'
    print '(Set the variable BUILD_SGMLOP to False and re-run the script if you want to disable sgmlop build)'
    fnames = os.listdir("deps")
    fname = [item for item in fnames if item.startswith('sgmlop')][0]
    if fname:
        fpath = os.path.join('deps', fname)
        # Should be a zipfile
        z = zipfile.ZipFile(fpath, 'r')
        print 'Extracting...'
        # Create directory...
        tempdir = os.path.join('deps', 'build_sgmlop')
        if not os.path.isdir(tempdir):
            try:
                os.makedirs(tempdir)
            except OSError, e:
                print e
                return -1
            
        for zinfo in z.infolist():
            arfile = zinfo.filename
            data = z.read(arfile)
            # Write with only filename
            arpath = os.path.join(tempdir, os.path.split(arfile)[-1])
            open(arpath, 'w').write(data)
            
        # Build sgmlop
        curdir = os.path.abspath(os.curdir)
        
        os.chdir(tempdir)
        ret = os.system("python setup.py install")

        os.chdir(curdir)
        
        try:
            shutil.rmtree(tempdir)
        except (IOError, OSError), e:
            print e
            
        return ret

    return -1
            
        
def version():
    vinfo = sys.version_info    
    return (vinfo, '.'.join((str(vinfo[0]), str(vinfo[1]), str(vinfo[2]))))

def main():
    vinfo, ver = version()
    print "Python version %s detected..." % ver
        
    if vinfo < (2,4):
        print 'Error: You need Python 2.4 or greater for HarvestMan'
        sys.exit(1)

    use_sgmlop = False
    
    if check_sgmlop()==-1:
        if BUILD_SGMLOP:
            print 'sgmlop not installed, checking for c compiler...'
            comp = check_ccompiler()
            if comp:
                print 'C compiler found...'
                # Build sgmlop...
                if build_sgmlop()==0 and check_sgmlop() != -1:
                    use_sgmlop = True
        else:
            print 'BUILD_SGMLOP flag set to False, not trying to build sgmlop...'
    else:
        use_sgmlop = True
            
    if use_sgmlop:
        print 'sgmlop found, will be used as fall-back HTML parser...'

    try:
        print 'Checking for pyparsing...'
        import pyparsing
        print 'found pyparsing.'
    except ImportError:
        print 'pyparsing not found.'
        if install_pyparsing() == -1:
            print 'Could not install pyparsing.'
        else:
            print 'Installed pyparsing successfully.'

    print 'Checking for web.py version >=0.2...'
    if check_webpy():
        print 'Found web.py...'
    else:
        print 'Web.py either missing or older version...'
        if install_webpy() == -1:
            print 'Could not install web.py!'
        else:
            print 'Installed web.py successfully.'
            
        
    setup(name="HarvestMan",
          version="2.0alpha",
          description="A modular, extensible, flexible, multithreaded webcrawler application and framework",
          author="Anand B Pillai",
          author_email="abpillai_at_gmail_dot_com",
          maintainer="Anand B Pillai",
          maintainer_email="abpillai_at_gmail_dot_com",
          url="http://www.harvestmanontheweb.com",
          license="GNU General Public License v 2.0",
          # requires=["Python (>=2.4)"],
          download_url="http://www.harvestmanontheweb.com/packages/2.0/HarvestMan-2.0alpha13062008.tar.gz",
          classifiers=[
          'Development Status :: 5 - Stable',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Offline browsing, Indexing, Search',
          ],

          package_dir = {'harvestman': 'harvestman'},
          packages = ['harvestman',
                      'harvestman.apps',
                      'harvestman.lib',
                      'harvestman.lib.common',
                      'harvestman.lib.js',
                      'harvestman.ext',
                      'harvestman.test',
                      'harvestman.dev',
                      'harvestman.tools'],
          package_data = {'harvestman' : ['ui/templates/*.html', 'ui/templates/content/*','test/*.html','test/*.css']}
          )

    from harvestman.lib.config import HarvestManStateObject
    cfg = HarvestManStateObject()

    etcdir = cfg.etcdir
    print 'Creating basic configuration in %s...' % etcdir

    # If using sgmlop parser set htmlparser option to 1...
    conf_data = cfg.generate_system_configuration()

    if not os.path.isdir(etcdir):
        try:
            os.makedirs(etcdir)
        except OSError, e:
            print e
            sys.exit(1)

    if os.path.isdir(etcdir):
        etcfile = os.path.join(etcdir, 'config.xml')
        open(etcfile, 'w').write(conf_data)
        print 'done.'
    else:
        print 'Could not create system configuration!'

    # Run unit tests
    try:
        # See if this is a fresh install, then run all tests
        # else skip running of tests...
        test_log = os.path.join(site_packages_dir(), 'harvestman', 'unittest.log')

        res=0
        if os.path.isfile(test_log):
            # Check the result
            res = int(open(test_log).read())
            
        if res != 1:
            print 'Fresh installation, running unit tests...'
            from harvestman.test import run_tests
            # result = run_tests.run_test_urlparser()

            result = run_tests.run_all_tests()
            print 'Ran %d tests, %d passes, %d failures' % (result.testsRun,
                                                            result.testsRun - len(result.errors),
                                                            len(result.errors))
            try:
                if result.wasSuccessful():
                    open(test_log, 'w').write('1')
                else:
                    open(test_log, 'w').write('0')
            except (IOError, OSError), e:
                print e
        else:
            print 'Not a fresh installation, skipping unit tests...'
                
    except ImportError, e:
        print 'Could not import unit test run module, please re-run this script/report the failure'

    if os.name == 'posix':
        # Create short-cuts
        print 'Creating application links...'
        create_shortcut("harvestman")
        create_shortcut("hget")

        
if __name__ == "__main__":
    main()

