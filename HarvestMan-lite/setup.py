#Gets setuptools
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

#Normal setup.py starts here
import sys, os

version = '2.0.4beta'

setup(name='HarvestMan',
      version=version,
      description="HarvestMan is a web crawler application and framework.",
      long_description="""\
HarvestMan is a modular, extensible and flexible web crawler program cum framework written in pure Python. HarvestMan? can be used to download files from websites according to a number of customized rules and constraints. It can be used to find information from websites matching keywords or regular expressions.
""",
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Testing :: Traffic Generation',
          'Topic :: Text Processing :: Indexing',
          ],
      keywords='crawler spider web-crawler web-bot robot data-mining python',
      author='Anand B Pillai',
      author_email='abpillai at gmail dot com',
      maintainer='Lukasz Szybalski',
      maintainer_email='szybalski@gmail.com',
      url='http://code.google.com/p/harvestman-crawler/',
      license='GPLv2',
      #find_packages replaces package_dir and packages
      #packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      #package_dir = {'harvestman': 'harvestman'}, #Instalation package:path
      packages=find_packages(exclude=['ez_setup', 'examples']),
      include_package_data = True,    # include everything in source control
      package_dir = {'harvestman': 'harvestman'}, #Instalation package:path
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
      """,
      )



