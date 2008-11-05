# -- coding: utf-8
import sys
from narcissus import *

def get_children(n):
    children = []
    attrs = [n.type, n.value, n.lineno, n.start, n.end, n.tokenizer, n.initializer,
             n.name, n.params, n.funDecls, n.varDecls, n.body, n.functionForm,
             n.assignOp, n.expression, n.condition, n.thenPart, n.elsePart,
             n.readOnly, n.isLoop, n.setup, n.postfix, n.update, n.exception,
             n.object, n.iterator, n.varDecl, n.label, n.target, n.tryBlock,
             n.catchClauses, n.varName, n.guard, n.block, n.discriminant, n.cases,
             n.defaultIndex, n.caseLabel, n.statements, n.statement]

    # print 'Node length =>', len(n)
    for x in range(len(n)):
        if n[x] != n and n[x].__class__ == Node:
            children.append(n[x])

    for x in range(len(attrs)):
        if isinstance(attrs[x], Node) and attrs[x] != n:
            children.append(attrs[x])

    return children

def resolve_name(n):
    name = ''

    if n.type == consts["DOT"]:
        name = resolve_name(n[0]) + "." + resolve_name(n[1])
    else: # INDENTIFIER
        name = n.value
        
    return name

def get_functions (n, functions = None):

    # print "FUNCS=>",functions
    if not functions: functions = {}

    function = None
    name = None

    # print n.type, consts["FUNCTION"]
    if n.type == consts["FUNCTION"] and n.name:
            print 'Function=>',n
            functions[n.name] = n
    elif  (n.type == consts["ASSIGN"]) and (n[1].type == consts["FUNCTION"]) and (not n[1].name):
            function = n[1]
            name = resolve_name(n[0])
            functions[name] = function
            

    children = get_children(n)
    for x in range(len(children)):
        functions = get_functions(children[x], functions)

    return functions


def print_functions(filename):

    jsdata = open(filename).read()
    jstree = parse(jsdata, filename)
    print type(jstree)
    
    functions = get_functions(jstree)
    print functions

    for f, funcobj in functions.iteritems():
        print 'Function',f
        print funcobj.varDecls

if __name__ == "__main__":
    print_functions(sys.argv[1])
            
