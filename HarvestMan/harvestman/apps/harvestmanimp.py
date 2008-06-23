"""
harvestmanimp.py - HarvestMan import wrapper.

This is just a wrapper which imports all names defined in harvestman.py module.
This is required since we install all source code under site-packages/harvestman
folder. So a plain 'import harvestman' might cause a name conflict, since it
might import from site-packages/harvestman/__init__.py, instead of
from harvestman/apps/harvestman.py .

If you want to make sure you are importing from harvestman/apps/harvestman.py
use this module wrapper.
"""

from harvestman import *
