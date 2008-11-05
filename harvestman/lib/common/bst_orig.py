"""
bst.py - Basic binary search tree in Python with automated disk caching at
the nodes. This is not a full-fledged implementation since it does not
implement node deletion, tree balancing etc.

Created Anand B Pillai <abpillai at gmail dot com> Feb 13 2008

Copyright (C) 2008, Anand B Pillai.

"""



import cPickle
import math
import os
import shutil

class BSTNode(dict):
    """ Node class for a BST """
    
    def __init__(self, key, val, left=None, right=None):
        self.key = key
        self[key] = val
        self[0] = left
        self[1] = right
        # Mode flag
        # 0 => mem
        # 1 => disk
        self.mode = 0
        # Cached idx filename
        self.fname = ''
        # Number of gets
        self.cgets = 0
        # Number of loads
        self.cloads = 0

    def __getitem__(self, key):

        try:
            return super(BSTNode, self).__getitem__(key)
        except KeyError:
            return None
        
    def set(self, value):
        self.val = value

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
        if self[0]==None and self[1]==None:
            return False

        while level>0:
            level -= 1
            
            if self[0] !=None and self[1] != None:
                if level:
                    return self[0].is_balanced(level) and \
                           self[1].is_balanced(level)
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
                self[self.key] = cPickle.load(open(self.fname, 'rb'))
                self.mode = 0
            
            if recursive:
                left = self[0]
                if left: left.load(True)
                right = self[1]
                if right: right.load(True)
                
        except cPickle.UnpicklingError, e:
            raise
        except Exception, e:
            raise
        
    def dump(self, bdir, recursive=False):

        try:
            if self.mode==0:
                self.fname = os.path.join(bdir, str(self.key))
                cPickle.dump(self[self.key], open(self.fname, 'wb'))
                # If dumping was done, set val to None to
                # reclaim memory...
                del self[self.key]
                self.mode = 1
            else:
                # Dont do anything
                pass
            
            if recursive:
                left = self[0]
                if left: left.dump(bdir, True)
                right = self[1]
                if right: right.dump(bdir, True)
                
        except cPickle.PicklingError, e:
            raise
        except Exception, e:
            raise

    def clear(self):

        # Clear removes the data from memory as well as from disk
        self.val = None
        if self.fname and os.path.isfile(self.fname):
            try:
                os.remove(self.fname)
            except Exception, e:
                print e

        left = self[0]
        right = self[1]
                
        if left:
            left.clear()
        if right:
            right.clear()

        super(BSTNode, self).clear()

        
class BST(object):
    """ BST class with automated disk caching of node values """
    
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
        # Directory for file representation
        self.bdir = '.bidx' + str(hash(self))        
        if not os.path.isdir(self.bdir):
            try:
                os.makedirs(self.bdir)
            except Exception, e:
                raise

        self.root = None
        if key:
            self.root = self.insert(key, val)

    def addNode(self, key, val):
        self.size += 1
        self.height = int(math.ceil(math.log(self.size+1, 2)))
        node = BSTNode(key, val)

        if self.auto and self.autolevel and self.size>1:
            # Check if the node has become balanced at the
            # requested level...

            if self.auto and self.autolevel:
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
                root[0] = self.__insert(root[0], key, val)
            else:
                # Goes to right subtree
                # print 'Inserting on right subtree...', key
                root[1] = self.__insert(root[1], key, val)

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
                    return self.__lookup(root[0], key)
                else:
                    return self.__lookup(root[1], key)
                
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

    def __inorder(self, root):

        if root != None:
            for node in self.__inorder(root[0]):
                yield node
            yield root
            for node in self.__inorder(root[1]):
                yield node
            
    def inorder(self):
        # Inorder traversal, yielding the nodes
        
        return self.__inorder(self.root)

    def __preorder(self, root):

        if root != None:
            yield root
            for node in self.__preorder(root[0]):
                yield node
            for node in self.__preorder(root[1]):
                yield node            
            
    def preorder(self):
        # Inorder traversal, yielding the nodes
        return self.__preorder(self.root)

    def __postorder(self, root):

        if root != None:
            for node in self.__postorder(root[0]):
                yield node
            for node in self.__postorder(root[1]):
                yield node            
            yield root
            
    def postorder(self):
        # Inorder traversal, yielding the nodes
        return self.__postorder(self.root)        
        
    def minnode(self):
        # Node with the minimum key value

        root = self.root

        while (root[0] != None):
            root = root[0]

        return root
    
    def minkey(self):

        node = self.minnode()
        return node.key

    def maxnode(self):
        # Node with the maximum key value

        root = self.root

        while (root[1] != None):
            root = root[1]

        return root
    
    def maxkey(self):

        node = self.maxnode()
        return node.key

    def size_lhs(self):

        # Return the node size on the LHS (excluding root)
        root = self.root
        count = 0
        
        while root[0] != None:
            root = root[0]
            count += 1

        return count

    def size_rhs(self):

        # Return the node size on the LHS (excluding root)
        root = self.root
        count = 0
        
        while root[1] != None:
            root = root[1]
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
            self.__stats(root[0], d)
            self.__stats(root[1], d)
            
    def dump(self, startnode=None):

        if startnode==None:
            startnode = self.root
            
        if startnode==None:
            return None
        else:
            startnode.dump(self.bdir, True)

        self.hard = True

    def load(self):
        if self.root==None:
            return None

        if self.hard:
            self.root.load(True)
            self.hard = False

    def clear(self):

        if self.root:
            self.root.clear()
        # Remvoe the directory
        if self.bdir and os.path.isdir(self.bdir):
            try:
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
    #b.dump()
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

    print b.size_lhs()
    print b.size_rhs()    
    
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
