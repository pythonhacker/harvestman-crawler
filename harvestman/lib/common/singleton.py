# -- coding: utf-8
""" singleton.py - Singleton design-pattern implemented using
    meta-classes. 

    This module is part of the HarvestMan program.
    For licensing information see the file LICENSE.txt that
    is included in this distribution.

    Author: Anand B Pillai <anand at harvestmanontheweb.com>

    Created Anand B Pillai Feb 2 2007
    

    Copyright(C) 2007, Anand B Pillai.
    
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

class SingletonMeta(type):
    """ A type for Singleton classes """

    def my_new(cls,name,bases=(),dct={}):
        if not cls.instance:
            cls.instance = object.__new__(cls)
                
        return cls.instance
    
    def __init__(cls, name, bases, dct):
        super(SingletonMeta, cls).__init__(name, bases, dct)
        cls.instance = None
        cls.__new__ = cls.my_new

class SingletonMeta2(type):
    """ A type for Singleton classes """    

    def __init__(cls, *args):
        type.__init__(cls, *args)
        cls.instance = None

    def __call__(cls, *args):
        if not cls.instance:
            cls.instance = type.__call__(cls, *args)
        return cls.instance
    
class Singleton(object):
    """ The default implementation for a Python Singleton class """

    __metaclass__ = SingletonMeta2

    def getInstance(cls, *args):
        return cls(*args)
    
    getInstance = classmethod(getInstance)
    makeInstance = getInstance

