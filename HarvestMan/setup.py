from setuptools import setup, find_packages
import sys, os

version = '2.0.3'

setup(name='HarvestMan',
      version=version,
      description="HarvestMan is a web crawler application and framework.",
      long_description="""\
HarvestMan is a modular, extensible and flexible web crawler program cum framework written in pure Python. HarvestMan? can be used to download files from websites according to a number of customized rules and constraints. It can be used to find information from websites matching keywords or regular expressions.
""",
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
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
      keywords='crawler spider web-crawler web-bot robot data-mining python',
      author='Anand B Pillai',
      author_email='abpillai at gmail dot com',
      url='http://code.google.com/p/harvestman-crawler/',
      license='GPLv2',
      #find_packages replaces package_dir and packages
      #packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      #package_dir = {'harvestman': 'harvestman'}, #Instalation package:path
      packages=find_packages(exclude=['ez_setup', 'examples']),
      include_package_data = True,    # include everything in source control
      package_dir = {'harvestman': 'harvestman'}, #Instalation package:path
      #packages = ['harvestman',
      #           'harvestman.apps',
      #           'harvestman.lib',
      #           'harvestman.lib.common',
      #           'harvestman.lib.js',
      #           'harvestman.ext',
      #           'harvestman.test',
      #           'harvestman.dev',
      #           'harvestman.tools'
      #           ],
      #Package_data is for none-py files
      package_data = {'harvestman' : ['ui/templates/*.html', 'ui/templates/content/*']},
      zip_safe=False,
      install_requires=[
      "sgmlop >= 1.1.1",
      "pyparsing >= 1.4.8",
      "web.py >= 0.23",
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [console_scripts]
        harvestman = harvestman.apps.spider:main
        hget = harvestman.apps.hget:main
      """,
      )

#Create config.xml
#print sys.prefix
#if sys.prefix!='/usr':
#    pass

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

