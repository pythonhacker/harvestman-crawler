## Standards ##
  * When adding modifying code make sure you use the base imports
```
[good]from harvestman.lib import *
[good]from harvestman.lib import xyz
[good]from hasvestman.lib.common import *
[bad]import xyz
[bad]import *
```
## branches ##
  * Here is a short intro on how do do merging and branching.
  * http://kenkinder.com/svnmerge/
# Packages #
## python eggs ##
  * To make a python egg you can do the following:
  * In a folder that has setup.py:
```
python setup.py bdist_egg
```
  * The file should be in a dist folder
```
dist/HarvestMan-2.0.2dev_r107-py2.4.egg
```
  * You can send the egg to somebody and they can install it using easy\_install command:
```
easy_install HarvestMan-2.0.2dev_r107-py2.4.egg
```

## Making win32 package ##
  * Environment:Windows XP SP2 running Python 2.5.2, py2exe 0.6.8