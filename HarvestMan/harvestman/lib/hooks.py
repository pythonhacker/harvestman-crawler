# -- coding: utf-8
""" hooks.py - Module allowing developer extensions(plugins/callbacks)
    to HarvestMan. This module makes it possible to hook into/modify the
    execution flow of HarvestMan, making it easy to extend and customize
    it. 

    This module is part of the HarvestMan program. For licensing information
    see the file LICENSE.txt that is included in this distribution.

    Author: Anand B Pillai <abpillai at gmail dot com>
    
    Created by Anand B Pillai Feb 1 07.

    Modified by Anand B Pillai Feb 17 2007 Completed callback implementation
                                           using metaclass methodwrappers.
    Modified by Anand B Pillai Feb 26 2007 Replaced all 'hook' strings with
                                           'plugin'.

   Copyright (C) 2007 Anand B Pillai.    
"""

__version__ = '2.0 b1'
__author__ = 'Anand B Pillai'

import sys, os
import __init__

from common.common import *
from methodwrapper import MethodWrapperMetaClass, set_wrapper_method

class HarvestManHooksException(Exception):
    """ Exception class for HarvestManHooks class """
    pass

class HarvestManHooks:
    """ Class which manages pluggable hooks and callbacks for HarvestMan """
    
    supported_modules = ('crawler','harvestman', 'urlqueue', 'datamgr', 'connector', 'rules')
    module_plugins = {}
    module_callbacks = {}
    run_plugins = {}
    run_callbacks = {}

    def __init__(self):
        pass
    
    @classmethod
    def add_all_plugins(cls):

        dirname = os.path.dirname(os.path.dirname(os.path.abspath(__init__.__file__)))
        # Append app path
        appath = os.path.join(dirname, 'apps')
        sys.path.append(appath)
        
        for module in cls.supported_modules:
            # Get __plugins__ attribute from the module
            M = __import__(module)
            plugins = getattr(M, '__plugins__',{})
            for plugin in plugins.keys():
                cls.add_plugin(module, plugin)

    @classmethod
    def add_all_callbacks(cls):

        dirname = os.path.dirname(os.path.dirname(os.path.abspath(__init__.__file__)))
        # Append app path
        appath = os.path.join(dirname, 'apps')
        sys.path.append(appath)
        
        for module in cls.supported_modules:
            # Get __plugins__ attribute from the module
            M = __import__(module)
            callbacks = getattr(M, '__callbacks__',{})

            for cb in callbacks.keys():
                cls.add_callback(module, cb)

    @classmethod                
    def add_plugin(cls, module, plugin):
        """ Add a plugin named 'plugin' for module 'module' """

        l = cls.module_plugins.get(module)
        if l is None:
            cls.module_plugins[module] = [plugin]
        else:
            l.append(plugin)

    @classmethod
    def add_callback(cls, module, callback):
        """ Add a callback named 'callback' for module 'module' """

        l = cls.module_callbacks.get(module)
        if l is None:
            cls.module_callbacks[module] = [callback]
        else:
            l.append(callback)            

    @classmethod
    def get_plugins(cls, module):
        """ Return all plugins for module 'module' """

        return cls.module_plugins.get(module)

    @classmethod
    def get_callbacks(cls, module):
        """ Return all callbacks for module 'module' """

        return cls.module_callbacks.get(module)    

    @classmethod
    def get_all_plugins(cls):
        """ Return the plugins data structure """

        # Note this is a copy of the dictionary,
        # so modifying it will not have any impact
        # locally.
        return cls.module_plugins.copy()

    @classmethod
    def get_all_callbacks(cls):
        """ Return the callbacks data structure """

        # Note this is a copy of the dictionary,
        # so modifying it will not have any impact
        # locally.
        return cls.module_callbacks.copy()    

    @classmethod
    def set_plugin_func(self, context, func):
        """ Set plugin function 'func' for context 'context' """

        self.run_plugins[context] = func
        # Inject the given function in place of the original
        module, plugin = context.split(':')
        # Load module and get the entry point
        M = __import__(module)
        orig_func = getattr(M, '__plugins__').get(plugin)
        # Orig func is in the form class:function
        klassname, function = orig_func.split(':')
        if klassname:
            klass = getattr(M, klassname)
            # print klass
            # Replace function with the new one
            # print 'Klassid=>',id(klass), func, id(func)
            objects.config.set_klass_plugin_func(klassname, function, func)

    @classmethod        
    def set_callback_method(self, context, method, order='post'):
        """ Set callback method at context as the given
        method 'method'. The callback will be inserted after
        the original function call if order is 'post' and
        inserted before the original function call if order
        is 'pre' """

        self.run_callbacks[order + ':' + context] = method
        module, callback = context.split(':')
        # Load module and get the entry point
        M = __import__(module)
        orig_meth = getattr(M, '__callbacks__').get(callback)
        
        # Orig func is in the form class:function
        klassname, origmethod = orig_meth.split(':')
        if klassname:
            klass = getattr(M, klassname)
            # print klass
            # If klass does not define its __metaclass__ attribute
            # as MethodWrapperMetaClass, then we cannot do anything.
            cls = getattr(klass, '__metaclass__', None)
            if (cls==None) or (cls.__name__ != 'MethodWrapperMetaClass'):
                raise HarvestManHooksException, 'Error: Cannot set callback on klass %s, __metaclass__ attribute is not set correctly!' % klassname
            
            # Insert new function which basicaly calls
            # new function before or after the original
            methobj = getattr(klass, origmethod)
            # Post call back function should take one extra argument
            # than the function itself.
            argcnt1 = methobj.im_func.func_code.co_argcount
            argcnt2 = method.func_code.co_argcount
            if order=='post' and ((argcnt1 + 1)!= argcnt2) or \
               order=='pre' and (argcnt1 != argcnt2):
                raise HarvestManHooksException,'Error: invalid callback method, signature does not match!'
            # Set wrapper method
            # print 'Klassid=>',id(klass), origmethod, id(method)
            objects.config.set_klass_callback_func(klassname, origmethod, method, order)            
        else:
            pass

    @classmethod                          
    def get_plugin_func(self, context):

        return self.run_plugins.get(context)

    @classmethod
    def get_all_plugin_funcs(self):

        return self.run_plugins.copy()

HarvestManHooks.add_all_plugins()
HarvestManHooks.add_all_callbacks()
              
def register_plugin_function(context, func):
    """ Register function 'func' as
    a plugin at context 'context' """
    
    # The context is a string of the form module:hook
    # Example => crawler:fetcher_process_url_hook

    # Hooks are defined in modules using the global dictionary
    # __hooks__. This module will load all hooks from modules
    # supporting hookable(pluggable) function definitions, when
    # this module is imported and add the hook definitions to
    # the class HarvestManHooks.
    
    # The function is a hook function/method object which is defined
    # at the time of calling this function. This function
    # will not attempt to validate whether the hook function exists
    # and whether it accepts the right parameters (if any). Any
    # such validation is done by the Python run-time. The function
    # can be a module-level, class-level or instance-level function.
    
    module, plugin = context.split(':')

    # Validity checks...
    if module not in HarvestManHooks.get_all_plugins().keys():
        raise HarvestManHooksException,'Error: %s has no plugins defined!' % module

    if plugin not in HarvestManHooks.get_plugins(module):
        raise HarvestManHooksException,'Error: Plugin %s is not defined for module %s!' % (plugin, module)

    # Finally add hook..
    HarvestManHooks.set_plugin_func(context, func)

def register_callback_method(context, method, order):
    """ Register class method 'method' as
    a callback at context 'context' according
    to given order """

    # Don't call this function directly, instead
    # use one of the function below which wraps up
    # this function.
    
    if order not in ('post','pre'):
        raise HarvestManHooksException,'Error: order argument %s is not valid!' % order
    
    # The context is a string of the form module:hook
    # Example => crawler:fetcher_process_url_hook

    # Callbackss are defined in modules using the global dictionary
    # __callbacks__. This module will load all callbacks from modules
    # having function definitions which support callbacks, when
    # this module is imported. The callback definitions are added to
    # the class HarvestManHooks.
    
    # The method 'method' is a callback instance method object which is defined
    # at the time of calling this function. The method has to be declared
    # as a class-level method with the same arguments as the original.
    # Callbacks are not supported for module level functions, i.e functions
    # not associated to classes.
    
    module, hook = context.split(':')

    # Validity checks...can be a module-level, class-level or instance-level function.
    if module not in HarvestManHooks.get_all_callbacks().keys():
        raise HarvestManHooksException,'Error: %s has no callbacks defined!' % module

    if hook not in HarvestManHooks.get_callbacks(module):
        raise HarvestManHooksException,'Error: Callback %s is not defined for module %s!' % (hook, module)

    # Finally add callback..
    HarvestManHooks.set_callback_method(context, method, order)    
    
def register_pre_callback_method(context, method):
    """ Register callback method as a pre callback """

    return register_callback_method(context, method,'pre')

def register_post_callback_method(context, method):
    """ Register callback method as a post callback """

    return register_callback_method(context, method,'post')
    
def myfunc(self):
    pass

if __name__ == "__main__":
    register_plugin_function('datamgr:download_url_plugin', myfunc)
    register_post_callback_method('crawler:fetcher_process_url_callback', myfunc)
    print HarvestManHooks.getInstance().get_all_hook_funcs()
