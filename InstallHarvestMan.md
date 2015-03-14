**You have few options when installing harvestman**

Currently the best way is to download the source code from the trunk of our repository.

# Check out code from svn #
  * First you need to checkout version of harvestman from repository.You will need '''subversion''' program to do that. When subversion is installed run this command:
```
svn checkout http://harvestman-crawler.googlecode.com/svn/trunk/HarvestMan-lite harvestman-crawler
```

# Install harvestman #

## Requirements ##
  * Harvestman requires:

  1. python2.4 or higher. (python2.3 untested)
  1. python-dev package
  1. sgmlop,pyparsing,web.py which will get installed automatically as part of the installation.

## Installation of harvestman ##
  * You have two options of installing harvestman. You can install it in a system base folder or you can use virtualenv to install it in your defined folder.

### Vritualenv ###
  * If you want to use virtualenv
  * Setup virtualenv folder. If you don't have virtualenv install it using **easy\_install virtualenv**
```
virtualenv --no-site-packages harvestmanENV

You should see:
New python executable in harvestmanENV/bin/python
Installing setuptools............done.
```
  * Activate your virtual setup.
```
source harvestmanENV/bin/activate
```
  * You should see (harvestmanENV) on your command line:
```
(harvestmanENV)lucas@delldebian:~/tmp$ 
```
  * Now go into the harvestman folder and install it
```
cd harvestman-crawler/HarvestMan/
python setup.py install
```
  * Test the installation by running:
```
harvestman --selftest
```
  * When done you can deactivate your virtualenv
```
deactivate
```
  * See UsingHarvestman

### system wide installation ###
  * If you want to do a system wide installation:
  * Go into the harvestman folder, and run setup file.
```
cd harvestman-crawler/HarvestMan/
python setup.py install
```