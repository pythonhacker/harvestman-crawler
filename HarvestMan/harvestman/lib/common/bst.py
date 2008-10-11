"""
bst.py - Basic binary search tree in Python with automated disk caching at
the nodes. This is not a full-fledged implementation since it does not
implement node deletion, tree balancing etc.

Created Anand B Pillai <abpillai at gmail dot com> Feb 13 2008

Copyright (C) 2008, Anand B Pillai.

"""

import cPickle
import math
import sys
import os
import shutil
import weakref

from dictcache import DictCache

class BSTNode(dict):
    """ Node class for a BST """
    
    def __init__(self, key, val, left=None, right=None, tree=None):
        self.key = key
        self[key] = val
        self['left'] = left
        self['right'] = right
        # Mode flag
        # 0 => mem
        # 1 => disk
        self.mode = 0
        # Number of gets
        self.cgets = 0
        # Number of loads
        self.cloads = 0
        # Link back to the tree
        self.tree = weakref.proxy(tree)
        
    def __getitem__(self, key):

        try:
            return super(BSTNode, self).__getitem__(key)
        except KeyError:
            return None
        
    def set(self, value):
        self[self.key] = value
        if self.mode == 1:
            # Already dumped
            self.mode = 0
            self.dump()
            
    def get(self):
        
        if self.mode==0:
            self.cgets += 1
            return self[self.key]
        else:
            self.cloads += 1            
            self.load()
            return self[self.key]

    def is_balanced(self, level=1):

        # Return if this node is balanced
        # The node balance check is done per
        # level. Default is 1 which means we
        # check whether this node has both left
        # and right children. If level is 2, this
        # is done at one more level, i.e for the
        # child nodes also...

        # Leaf node is not balanced...
        if self['left']==None and self['right']==None:
            return False

        while level>0:
            level -= 1
            
            if self['left'] !=None and self['right'] != None:
                if level:
                    return self['left'].is_balanced(level) and \
                           self['right'].is_balanced(level)
                else:
                    return True
            else:
                return False

        return False
        
    def load(self, recursive=False):

        # Load values from disk
        try:
            # Don't load if mode is 0 and value is not None
            if self.mode==1 and self[self.key] == None:
                self[self.key] = self.tree.from_cache(self.key)
                self.mode = 0
            
            if recursive:
                left = self['left']
                if left: left.load(True)
                right = self['right']
                if right: right.load(True)
                
        except Exception, e:
            raise
        
    def dump(self, recursive=False):

        try:
            if self.mode==0 and self[self.key] != None:
                self.tree.to_cache(self.key, self[self.key])
                self[self.key]=None
                self.mode = 1
            else:
                # Dont do anything
                pass
            
            if recursive:
                left = self['left']
                if left: left.dump(True)
                right = self['right']
                if right: right.dump(True)
                
        except Exception, e:
            raise

    def clear(self):

        # Clear removes the data from memory as well as from disk
        try:
            del self[self.key]
        except KeyError:
            pass

        left = self['left']
        right = self['right']
                
        if left:
            left.clear()
        if right:
            right.clear()

        super(BSTNode, self).clear()

class BST(object):
    """ BST class with automated disk caching of node values """

    # Increase the recursion limit for large trees
    sys.setrecursionlimit(20000)
        
    def __init__(self, key=None, val=None):
        # Size of tree
        self.size = 0
        # Height of tree
        self.height = 0
        # 'Hardened' flag - if the data structure
        # is dumped to disk fully, the flag hard
        # is set to True
        self.hard = False
        # Autocommit mode
        self.auto = False
        # Autocommit mode level
        self.autolevel = 0
        # Current auto left node for autocommit
        self.autocurr_l = None
        # Current auto right node for autocommit
        self.autocurr_r = None        
        # For stats
        # Total number of lookups
        self.nlookups = 0
        # Total number of in-mem lookups
        self.ngets = 0
        # Total number of disk loads
        self.nloads = 0
        self.root = None
        if key:
            self.root = self.insert(key, val)
        self.bdir = ''
        self.diskcache = None

    def __del__(self):
        self.clear()

    def to_cache(self, key, val):
        self.diskcache[key] = val

    def from_cache(self, key):
        return self.diskcache[key]
    
    def addNode(self, key, val):
        self.size += 1
        self.height = int(math.ceil(math.log(self.size+1, 2)))
        node = BSTNode(key, val, tree=self)

        if self.auto and self.autolevel and self.size>1:
            # print 'Auto-dumping...', self.size
            if self.size % self.autolevel==0:
                self.dump(self.autocurr_l)
                # Set autocurr to this node
                self.autocurr_l = node
            
            #if self.autocurr_l and self.autocurr_l.is_balanced(self.autolevel):
            #    print 'Auto-dumping...', self.autocurr_l.key
            #    self.dump(self.autocurr_l)
            #    curr = self.autocurr_l
            #    # Set autocurr to the children of this node
            #    self.autocurr_l = curr.left
            #    self.autocurr_r = curr.right
            #    print 'Left=>',self.autocurr_l
            #    print 'Right=>',self.autocurr_r                
            #    print 'Root=>',self.root.key
                
            #if self.autocurr_r == self.autocurr_l:
            #    return node
            
            #if self.autocurr_r and self.autocurr_r.is_balanced(self.autolevel):
            #    print 'Auto-dumping...', self.autocurr_r.key
            #    self.dump(self.autocurr_r)
            #    curr = autocurr_r
            #    # Set autocurr to the children of this node
            #    self.autocurr_l = curr.left
            #    self.autocurr_r = curr.right                
                
                
        return node
    
    def __insert(self, root, key, val):
        
        if root==None:
            return self.addNode(key, val)

        else:
            if key<=root.key:
                # Goes to left subtree
                # print 'Inserting on left subtree...', key
                root['left'] = self.__insert(root['left'], key, val)
            else:
                # Goes to right subtree
                # print 'Inserting on right subtree...', key
                root['right'] = self.__insert(root['right'], key, val)

            return root
        
    def __lookup(self, root, key):

        if root == None:
            return None
        else:
            if key==root.key:
                # Note we are returning the value
                return root.get()
            else:
                if key < root.key:
                    return self.__lookup(root['left'], key)
                else:
                    return self.__lookup(root['right'], key)

    def __update(self, root, key, newval):

        if root == None:
            return None
        else:
            if key==root.key:
                root.set(newval)
            else:
                if key < root.key:
                    return self.__update(root['left'], key, newval)
                else:
                    return self.__update(root['right'], key, newval)                
                
    def insert(self, key, val):
        node = self.__insert(self.root, key, val)

        if self.root == None:
            self.root = node
            # Set auto node
            self.autocurr_l = self.autocurr_r = self.root

        # If node is added to left of current autocurrent node..
        
        return node

    def lookup(self, key):
        return self.__lookup(self.root, key)

    def update(self, key, newval):
        self.__update(self.root, key, newval)
        
    def __inorder(self, root):

        if root != None:
            for node in self.__inorder(root['left']):
                yield node
            yield root
            for node in self.__inorder(root['right']):
                yield node
            
    def inorder(self):
        # Inorder traversal, yielding the nodes
        
        return self.__inorder(self.root)

    def __preorder(self, root):

        if root != None:
            yield root
            for node in self.__preorder(root['left']):
                yield node
            for node in self.__preorder(root['right']):
                yield node            
            
    def preorder(self):
        # Inorder traversal, yielding the nodes
        return self.__preorder(self.root)

    def __postorder(self, root):

        if root != None:
            for node in self.__postorder(root['left']):
                yield node
            for node in self.__postorder(root['right']):
                yield node            
            yield root
            
    def postorder(self):
        # Inorder traversal, yielding the nodes
        return self.__postorder(self.root)        
        
    def minnode(self):
        # Node with the minimum key value

        root = self.root

        while (root['left'] != None):
            root = root['left']

        return root
    
    def minkey(self):

        node = self.minnode()
        return node.key

    def maxnode(self):
        # Node with the maximum key value

        root = self.root

        while (root['right'] != None):
            root = root['right']

        return root
    
    def maxkey(self):

        node = self.maxnode()
        return node.key

    def size_lhs(self):

        # Traverse pre-order and increment counts
        if self.root == None:
            return 0
        
        root_left = self.root['left']
        count = 0

        for node in self.__preorder(root_left):
            count += 1

        return count

    
    def size_rhs(self):

        if self.root == None:
            return 0

        # Traverse pre-order and increment counts
        root_right = self.root['right']
        count = 0

        for node in self.__preorder(root_right):
            count += 1

        return count
    
    def size(self):
        return self.count

    def stats(self):

        d = {'gets': 0, 'loads': 0}
        self.__stats(self.root, d)
        return d

    def __stats(self, root, d):

        if root != None:
            d['gets'] += root.cgets
            d['loads'] += root.cloads
            self.__stats(root['left'], d)
            self.__stats(root['right'], d)
            
    def dump(self, startnode=None):

        if startnode==None:
            startnode = self.root
            
        if startnode==None:
            return None
        else:
            startnode.dump(True)

        self.hard = True

    def load(self):
        if self.root==None:
            return None

        if self.hard:
            self.root.load(True)
            self.hard = False

    def reset(self):
        self.size = 0
        self.height = 0
        self.hard = False
        # Autocommit mode
        self.auto = False
        self.autolevel = 0
        self.autocurr_l = None
        self.autocurr_r = None        
        self.nlookups = 0
        self.ngets = 0
        self.nloads = 0
        self.root = None
        
    def clear(self):

        if self.root:
            self.root.clear()

        self.reset()
        if self.diskcache:
            self.diskcache.clear()

        # Remvoe the directory
        if self.bdir and os.path.isdir(self.bdir):
            try:
                print 'Removing folder',self.bdir
                shutil.rmtree(self.bdir)
            except Exception, e:
                print e

    def set_auto(self, level):
        # Enable auto commit and set level
        # If auto commit is set to true, the tree
        # is flushed to disk after the existing
        # autocommit node is balanced at the
        # level 'level'. The starting autocommit
        # node is root by default.
        self.auto = True
        self.autolevel = level
        # Directory for file representation
        self.bdir = '.bidx' + str(hash(self))        
        if not os.path.isdir(self.bdir):
            try:
                print 'Making folder',self.bdir
                os.makedirs(self.bdir)
            except Exception, e:
                raise

        self.diskcache = DictCache(10, self.bdir)
        self.diskcache.freq = self.autolevel
        
if __name__ == "__main__":
    b = BST()
    b.set_auto(3)
    print b.root
    b.insert(4,[4])
    b.insert(3,[2])
    b.insert(2,[6])
    b.insert(1, [3])
    b.insert(5,[5])
    b.insert(6,[7])
    b.insert(0,[8])        
    print b.size
    print b.height
    print b.lookup(4)
    b.dump()
    # Now try to lookup item 3
    print b.lookup(3)
    print b.lookup(3)
    print b.lookup(3)    
    # Load all
    b.load()
    print b.size, b.height
    
    # Do inorder
    print 'Inorder...'
    for node in b.inorder():
        print node.key,'=>',node[node.key]
    # Do preorder
    print 'Preorder...'    
    for node in b.preorder():
        print node.key,'=>',node[node.key]
    # Do postorder
    print 'Postorder...'        
    for node in b.postorder():
        print node.key,'=>',node[node.key]

    print 'LHS=>',b.size_lhs()
    print 'RHS=>',b.size_rhs()    
    
    # b.clear()
    print b.stats()
    root = b.root
    print root.is_balanced()    
    print root.is_balanced(2)
    
    del b

    b= BST()
    b.insert(10,[4])
    b.insert(5,[2])
    b.insert(2,[6])
    b.insert(7, [3])
    b.insert(14,[5])
    b.insert(12,[7])
    b.insert(15,[8])

    root = b.root    
    print root.is_balanced(1)
    print root.is_balanced(2)
    print root.is_balanced(3)

    print 'LHS=>',b.size_lhs()
    print 'RHS=>',b.size_rhs()    
    
