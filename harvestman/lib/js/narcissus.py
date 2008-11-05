# -- coding: utf-8
"""
Python port of Rbnarcissus, a pure Javascript parser written in Ruby.
This code has been ported from the free Rbnarcissus port available
at http://idontsmoke.co.uk/2005/rbnarcissus/Parser.rb.

For a status of the code and the test cases which pass, read
the README.

This code is licensed under GNU GPL version 2.0.

Author : Anand B Pillai <abpillai at gmail dot com>
Copyright (C) 2007 Anand B Pillai <abpillai at gmail dot com>
"""

__version__ = "0.1 (alpha)"
__author__  = "Anand B Pillai"

import re

def dump(d):
    for key in sorted(d):
        print key,'=>',d[key]

class NarcissusError(Exception):

    def __init__(self, msg, tokenizer):
        self.msg = msg
        self.t = tokenizer

    def __str__(self):
        return self.msg
    
tokens = [
        # End of source.
        "END",
        
        # Operators and punctuators.  Some pair-wise order matters, e.g. (+, -)
        # and (UNARY_PLUS, UNARY_MINUS).
        "\n", ";",
        ",",
        "=",
        "?", ":", "CONDITIONAL",
        "||",
        "&&",
        "|",
        "^",
        "&",
        "==", "!=", "===", "!==",
        "<", "<=", ">=", ">",
        "<<", ">>", ">>>",
        "+", "-",
        "*", "/", "%",
        "!", "~", "UNARY_PLUS", "UNARY_MINUS",
        "++", "--",
        ".",
        "[", "]",
        "{", "}",
        "(", ")",
        
        # Nonterminal tree node type codes.
        "SCRIPT", "BLOCK", "LABEL", "FOR_IN", "CALL", "NEW_WITH_ARGS", "INDEX",
        "ARRAY_INIT", "OBJECT_INIT", "PROPERTY_INIT", "GETTER", "SETTER",
        "GROUP", "LIST",
        
        # Terminals.
        "IDENTIFIER", "NUMBER", "STRING", "REGEXP",
        
        # Keywords.
        "break",
        "case", "catch", "const", "continue",
        "debugger", "default", "delete", "do",
        "else", "enum",
        "false", "finally", "for", "function",
        "if", "in", "instanceof",
        "new", "null",
        "return",
        "switch",
        "this", "throw", "true", "try", "typeof",
        "var", "void",
        "while", "with",
]

# Operator and punctuator mapping from token to tree node type name.
opTypeNames = {
    "\n"  : "NEWLINE",
    ';'   : "SEMICOLON",
    ','   : "COMMA",
    '?'   : "HOOK",
    ':'   : "COLON",
    '||'  : "OR",
    '&&'  : "AND",
    '|'   : "BITWISE_OR",
    '^'   : "BITWISE_XOR",
    '&'   : "BITWISE_AND",
    '===' : "STRICT_EQ",
    '=='  : "EQ",
    '='   : "ASSIGN",
    '!==' : "STRICT_NE",
    '!='  : "NE",
    '<<'  : "LSH",
    '<='  : "LE",
    '<'   : "LT",
    '>>>' : "URSH",
    '>>'  : "RSH",
    '>='  : "GE",
    '>'   : "GT",
    '++'  : "INCREMENT",
    '--'  : "DECREMENT",
    '+'   : "PLUS",
    '-'   : "MINUS",
    '*'   : "MUL",
    '/'   : "DIV",
    '%'   : "MOD",
    '!'   : "NOT",
    '~'   : "BITWISE_NOT",
    '.'   : "DOT",
    '['   : "LEFT_BRACKET",
    ']'   : "RIGHT_BRACKET",
    '{'   : "LEFT_CURLY",
    '}'   : "RIGHT_CURLY",
    '('   : "LEFT_PAREN",
    ')'   : "RIGHT_PAREN"
}

# Hash of keyword identifier to tokens index.
keywords = {}

# Define const END, etc., based on the token names.  Also map name to index.
consts = {}

r1 = re.compile(r'\A[a-z]')
r2 = re.compile(r'\A\W')

for i in range(len(tokens)):
    t = tokens[i]

    if r1.match(t):
#         # print t
        consts[t.upper()] = i
        keywords[t] = i
    elif r2.match(t):
        consts[opTypeNames[t]] = i
    else:
        consts[t] = i

#for key in sorted(keywords):
# #    print key,'=>',keywords[key]

# Map assignment operators to their indexes in the tokens array.
assignOps = ['|', '^', '&', '<<', '>>', '>>>', '+', '-', '*', '/', '%']
assignOpsHash = {}

for i in range(len(assignOps)):
    t = assignOps[i]
    assignOpsHash[t] = consts[opTypeNames[t]]

#for key in sorted(assignOpsHash):
# #    print key,'=>',assignOpsHash[key]
    
opPrecedence = {
    "SEMICOLON" : 0,
    "COMMA" : 1,
    "ASSIGN" : 2,
    "HOOK" : 3, "COLON" : 3, "CONDITIONAL" : 3,
    "OR" : 4,
    "AND" : 5,
    "BITWISE_OR" : 6,
    "BITWISE_XOR" : 7,
    "BITWISE_AND" : 8,
    "EQ" : 9, "NE" : 9, "STRICT_EQ" : 9, "STRICT_NE" : 9,
    "LT" : 10, "LE" : 10, "GE" : 10, "GT" : 10, "IN" : 10, "INSTANCEOF" : 10,
    "LSH" : 11, "RSH" : 11, "URSH" : 11,
    "PLUS" : 12, "MINUS" : 12,
    "MUL" : 13, "DIV" : 13, "MOD" : 13,
    "DELETE" : 14, "VOID" : 14, "TYPEOF" : 14, # PRE_INCREMENT: 14, PRE_DECREMENT: 14,
    "NOT" : 14, "BITWISE_NOT" : 14, "UNARY_PLUS" : 14, "UNARY_MINUS" : 14,
    "INCREMENT" : 15, "DECREMENT" : 15, # postfix
    "NEW" : 16,
    "DOT" : 17
}

# Map operator type code to precedence.
for key in opPrecedence.keys():
    opPrecedence[consts[key]] = opPrecedence[key]

#for key in sorted(opPrecedence):
# #    print key,'=>',opPrecedence[key]

opArity = {
        "COMMA" : -2,
        "ASSIGN" : 2,
        "CONDITIONAL" : 3,
        "OR" : 2,
        "AND" : 2,
        "BITWISE_OR" : 2,
        "BITWISE_XOR" : 2,
        "BITWISE_AND" : 2,
        "EQ" : 2, "NE" : 2, "STRICT_EQ" : 2, "STRICT_NE" : 2,
        "LT" : 2, "LE" : 2, "GE" : 2, "GT" : 2, "IN" : 2, "INSTANCEOF" : 2,
        "LSH" : 2, "RSH" : 2, "URSH" : 2,
        "PLUS" : 2, "MINUS" : 2,
        "MUL" : 2, "DIV" : 2, "MOD" : 2,
        "DELETE" : 1, "VOID" : 1, "TYPEOF" : 1, # PRE_INCREMENT: 1, PRE_DECREMENT: 1,
        "NOT" : 1, "BITWISE_NOT" : 1, "UNARY_PLUS" : 1, "UNARY_MINUS" : 1,
        "INCREMENT" : 1, "DECREMENT" : 1,   # postfix
        "NEW" : 1, "NEW_WITH_ARGS" : 2, "DOT" : 2, "INDEX" : 2, "CALL" : 2,
        "ARRAY_INIT" : 1, "OBJECT_INIT" : 1, "GROUP" : 1
}

# Map operator type code to arity.
for key in opArity.keys():
    opArity[consts[key]] = opArity[key]

# dump(opArity)

# NB: superstring tokens (e.g., ++) must come before their substring token
# counterparts (+ in the example), so that the opRegExp regular expression
# synthesized from this list makes the longest possible match.
ops = [';', ',', '?', ':', '||', '&&', '|', '^', '&', '===', '==', 
       '=', '!==', '!=', '<<', '<=', '<', '>>>', '>>', '>=', '>', '++', '--',
       '+', '-', '*', '/', '%', '!', '~', '.', '[', ']', '{', '}', '(', ')']


# Build a regexp that recognizes operators and punctuators (except newline).

opRegExpSrc = "\\A"
r3 = re.compile(r'([?|^&(){}\[\]+\-*\/\.])')

# $ops.length.times do |i|
for i in range(len(ops)):
    if opRegExpSrc != "\\A":
        opRegExpSrc += "|\\A"
        
    s = ops[i]
#     #print 'S=>',s
    for item in s:
        opRegExpSrc += r3.sub("\\" + item, item)
    
opRegExp = re.compile(opRegExpSrc, re.MULTILINE)

# A regexp to match floating point literals (but not integer literals).
fpRegExp = re.compile("\\A\\d+\\.\\d*(?:[eE][-+]?\\d+)?|\\A\\d+(?:\\.\\d*)?[eE][-+]?\\d+|\\A\\.\\d+(?:[eE][-+]?\\d+)?", re.MULTILINE)

# dump(consts)
# import sys
# sys.exit(0)

class List(list):
    def __setitem__(self, index, item):
        l = len(self)
        if l<=index:
          for x in range(index-l): self.append(None)
          self.append(item)
        else:
            super(List, self).__setitem__(index, item)

    def __getitem__(self, index):
        try:
            return super(List, self).__getitem__(index)
        except IndexError, e:
            return None

class List2(list):
    
    def last(self):
        try:
            return self[-1]
        except IndexError, e:
            return None

class Tokenizer(object):

    def __init__(self, source, filename='', line=1):
        self.cursor = 0
        self.source = str(source)
        self.tokens = List()
        self.tokenIndex = 0
        self.lookahead = 0
        self.scanNewlines = False
        self.scanOperand = True
        self.filename = filename
        self.lineno = line

    def input(self):
        return self.source[self.cursor:]

    def done(self):
        return (self.peek() == consts["END"])

    def token(self):
        return self.tokens[self.tokenIndex]

    def match(self, tt):
        print 'Calling match of',tt
        got = self.get()
        print 'GOOT',got,tt
        
        if got == tt:
            return True
        else:
            return self.unget()
    
    def mustMatch(self, tt):
        print 'Calling mustMatch',tt
        if not self.match(tt):
            raise NarcissusError("Missing " + self.tokens[tt].lower(), self)
        return self.token()
    
    def peek(self):
#         # print self.lookahead
        
        if self.lookahead > 0:
#             # print len(self.tokens)
#             # print self.tokenIndex,self.lookahead
#             # print (self.tokenIndex + self.lookahead) & 3
#             # print self.tokens
            token = self.tokens[(self.tokenIndex + self.lookahead) & 3]
#             # print token
            tt = token.type
        else:
            tt = self.get()
            self.unget()

        return tt

    def peekOnSameLine(self):
        self.scanNewlines = True
        tt = self.peek()
        self.scanNewlines = False
        return tt

    def get(self):

        pattern1 = re.compile(r'\A[ \t]+')
        pattern2 = re.compile(r'\s+')
        pattern3 = re.compile("\/(?:\*(?:.)*?\*\/|\/[^\n]*)", re.DOTALL)
        
        # pattern3 = re.compile(r'(\?\:\*(\?\:\.)*?\*\/|\/[^\n]*)', re.MULTILINE)
        pattern4 = re.compile(r'\A0[xX][\da-fA-F]+|0[0-7]*|\d+')
        pattern5 = re.compile(r'\A(\w|\$)+')
        pattern6 = re.compile(r"\A\"(?:\\.|[^\"])*\"|\A'(?:[^']|\\.)*'")
        pattern7 = re.compile(r'\A\/((?:\\.|[^\/])+)\/([gi]*)')
            
        while self.lookahead > 0:
            self.lookahead -= 1
            self.tokenIndex = (self.tokenIndex + 1) & 3
            token = self.tokens[self.tokenIndex]
            if token.type != consts["NEWLINE"] or self.scanNewlines:
                return token.type

        while True:

            input_s = self.input()
            print 'Input => ', input_s
            
            if self.scanNewlines:
                print 'Scannewlines is true'
                match = pattern1.match(input_s)
            else:
                match = pattern2.match(input_s)

            if match:
                print 'A MATCH FOUND!'
                spaces = match.group(0)
                print 'Spaces =>',len(spaces)
                self.cursor += len(spaces)
                print 'Newline count =>',spaces.count('\n')
                self.lineno += spaces.count('\n')
                input_s = self.input()

            print 'Input=>',input_s, len(input_s)
            match = pattern3.match(input_s)
            if not match:
                print 'BREAKING'
                break

            print 'Cursor',self.cursor
            comment = match.group(0)
            print 'Comment =>',comment
            self.cursor += len(comment)
            print 'Cursor',self.cursor            
            print 'Comment length, comment newline count=>',len(comment),comment.count('\n')
            self.lineno += comment.count('\n')

        self.tokenIndex = (self.tokenIndex + 1) & 3
#         # print self.tokenIndex
        token = self.tokens[self.tokenIndex]

        if token==None:
#             # print self.tokens, self.tokenIndex
            self.tokens[self.tokenIndex] = token = Token()

        if len(input_s)==0:
            token.type = consts["END"]
            return token.type
        
        matchflag = False
        cursor_advance = 0

        if fpRegExp.match(input_s):
            print "Matched here1"            
            match = fpRegExp.match(input_s)
            
            token.type = consts["NUMBER"]
            # Not sure if this works or if we need .findall()[0]
            token.value = float(match.group(0))
        elif pattern4.match(input_s):
            print "Matched here2"                        
            match = pattern4.match(input_s)
            token.type = consts["NUMBER"]
            token.value = int(match.group(0))
        elif pattern5.match(input_s):
            print "MATCH: Matched here3",input_s                        
            match = pattern5.match(input_s)
            id = match.group(0)
            token.type = keywords.get(id) or consts["IDENTIFIER"]
            token.value = id
        elif pattern6.match(input_s):
            print "Matched here4"                        
            match = pattern6.match(input_s)
            token.type = consts["STRING"]
            token.value = str(match.group(0))
        elif self.scanOperand and pattern7.match(input_s):
            print "Matched here5"                                    
            match = pattern7.match(input_s)
#             # print match.group(2)
            token.type = consts["REGEXP"]
            # print match.group(1), match.group(2)
            token.value = re.compile(match.group(1)) # , match.group(2))
        elif opRegExp.match(input_s):
            print "Matched here6",input_s                               
            match = opRegExp.match(input_s)

            op = match.group(0)
            if assignOpsHash.get(op) and (input_s[len(op):2] == '='):
                print 'Token type is ASSIGN'
                token.type = consts["ASSIGN"]
                token.assignOp = consts[opTypeNames[op]]
                cursor_advance = 1 # length of '='
            else:
                token.type = consts[opTypeNames[op]]
                print token.type, self.scanOperand, consts["MINUS"]
                print 'TOKEN TYPE NOT ASSIGN!'

                if self.scanOperand and (token.type==consts["PLUS"] or token.type==consts["MINUS"]):
                    print 'Adding to token type!'
                    token.type += consts["UNARY_PLUS"] - consts["PLUS"]

                token.assignOp = None
            token.value = op
        else:
            raise NarcissusError("Illegal token", self)

        token.start = self.cursor
#         # print token.start
        print 'Group0 =>',match.group(0)
        print 'Advancing cursor by',len(match.group(0)) + cursor_advance
        self.cursor += len(match.group(0)) + cursor_advance
#         # print self.cursor
        token.end = self.cursor
#         # print token.end
        token.lineno = self.lineno
#         # print token.lineno

        print 'Returning',token.type
        return token.type

    def unget(self):

        self.lookahead += 1
        if self.lookahead == 4:
            raise NarcissusError("PANIC: too much lookahead!", self)
        self.tokenIndex = (self.tokenIndex - 1) & 3
        return None

class NarcissusError(Exception):

    def __init__(self, msg, tokenizer):
        self.msg = msg
        self.line = str(tokenizer.lineno)

    def __str__(self):
        return '\n'.join((self.msg, "on line " + self.line))


class Token(object):

    __slots__ = ['type','value','start','end','assignOp','lineno']
    
    def __init__(self):
        self.type = None
        self.value = None
        self.start = None
        self.end = None
        self.assignOp = None
        self.lineno = None

    def lower(self):
        return self.value.lower()
    
class CompilerContext(object):

    __slots__ = ['inFunction', 'stmtStack','funDecls','varDecls',
                 'bracketLevel','curlyLevel','parenLevel','hookLevel',
                 'ecmaStrictMode','inForLoopInit']

    def __init__(self, inFunction):
        self.inFunction = inFunction
        self.stmtStack = []
        self.funDecls = []
        self.varDecls = []

        self.bracketLevel = self.curlyLevel = self.parenLevel = self.hookLevel = 0
        self.ecmaStrictMode = self.inForLoopInit = False


CURSOR = 0
IND = 0

# class Node => TODO
class Node(list):

    __slots__ =  ['type','value','lineno','start','end','tokenizer','initializer',
                  'name','params','funDecls','varDecls', 'body', 'functionForm',
                  'assignOp', 'expression', 'condition', 'thenPart', 'elsePart',
                  'readOnly', 'isLoop', 'setup', 'postfix', 'update', 'exception',
                  'object', 'iterator', 'varDecl', 'label', 'target', 'tryBlock',
                  'catchClauses', 'varName', 'guard', 'block', 'discriminant', 'cases',
                  'defaultIndex', 'caseLabel', 'statements', 'statement','children']
    
    def __init__(self, t, type=None):
        # Blanket initialize all params
        for var in self.__class__.__slots__:
            setattr(self, var, None)
            
        token = t.token()
#         # print 'token=>',token
        if token:
            if type:
                self.type = type
            else:
                self.type = token.type
            self.value = token.value
            self.lineno = token.lineno
            self.start = token.start
            self.end = token.end
        else:
            self.type = type
            self.lineno = t.lineno

        # T is the Tokenizer instance
        self.tokenizer = t

    # Always use push$ to add operands to an expression, to update start and end.
    def append(self, kid):
        # print "Pushing...", kid.__class__, kid.type
        if kid.start and self.start:
            if kid.start < self.start:
                self.start = kid.start

        if kid.end and self.end:
            if self.end < kid.end:
                self.end = kid.end

        return super(Node, self).append(kid)

    push = append
    def __str__(self):

        s = ''
        attrs = [self.value, self.lineno, self.start, self.end,
                 self.name, self.params, self.funDecls, self.varDecls,
                 self.body, self.functionForm, self.assignOp, self.expression,
                 self.condition, self.thenPart, self.elsePart ]

        global IND
        IND += 1

        for x in range(len(self)):
            item = self[x]
            if item != self and isinstance(item, Node):
                s = s + str(item)

        for x in range(len(attrs)):
            # Some commented out code here, not adding it
            item = attrs[x]
            if isinstance(item, Node):
                s = s + str(item)

        IND -= 1
        if IND == 0:
             print self.tokenizer.source[CURSOR:],

        return ""
            
    def getSource(self):
        return self.tokenizer.source[self.start:self.start+self.end]
    
    def filename(self):
        return self.tokenizer.filename
        

def Script(t, x):
    n = Statements(t, x)
    n.type = consts["SCRIPT"]
    n.funDecls = x.funDecls
    n.varDecls = x.varDecls

    return n

# Statement stack and nested statement handler.
# nb. Narcissus allowed a function reference, here we use Statement explicitly
def nest(t, x, node, end_ = None):
    x.stmtStack.append(node)
    n = Statement(t, x)
    x.stmtStack.pop()
    if end_:
        t.mustMatch(end_)
    return n

def Statements(t, x):

    n = Node(t, consts["BLOCK"])
    x.stmtStack.append(n)

    while (not t.done()) and (t.peek() != consts["RIGHT_CURLY"]):
        # print 'Loop'
#         # print 'Starting to push'
        s = Statement(t, x)
        # print 'Type =>',s.type
        n.push(s)
#         # print "Push ended"
        
    x.stmtStack.pop()
    return n

def Block(t, x):
    t.mustMatch(consts["LEFT_CURLY"])
    n = Statements(t, x)
    t.mustMatch(consts["RIGHT_CURLY"])
    return n

DECLARED_FORM = 0
EXPRESSED_FORM = 1
STATEMENT_FORM = 2

def Statement(t, x):
    # Cases for statements ending in a right curly return early, avoiding the
    # common semicolon insertion magic after this switch.

    # t is an instance of Tokenizer
    tt = t.get()
    print 'TT is',tt
    if tt == consts["FUNCTION"]:
        print 'TT is a function', consts["FUNCTION"]
        return FunctionDefinition(t, x, True, 
                                  (len(x.stmtStack) > 1) and STATEMENT_FORM or DECLARED_FORM)
    elif tt == consts["LEFT_CURLY"]:
        n = Statements(t, x)
        t.mustMatch(consts["RIGHT_CURLY"])
        return n
                
    elif tt == consts["IF"]:
        n = Node(t)
        n.condition = ParenExpression(t, x)
        x.stmtStack.append(n)
        n.thenPart = Statement(t, x)
        if t.match(consts["ELSE"]):
            n.elsePart = Statement(t, x)
        else:
            n.elsePart = None
            
        x.stmtStack.pop()
        return n

    elif tt == consts["SWITCH"]:
        n = Node(t)
        t.mustMatch(consts["LEFT_PAREN"])
        n.discriminant = Expression(t, x)
        t.mustMatch(consts["RIGHT_PAREN"])
        n.cases = []
        n.defaultIndex = -1
        x.stmtStack.append(n)
        t.mustMatch(consts["LEFT_CURLY"])
        
        while True:
            tt = t.get()
            print 'TT IS',tt
            if tt == consts["RIGHT_CURLY"]: break
            if tt == consts["DEFAULT"] or tt == consts["CASE"]:
                if tt == consts["DEFAULT"] and n.defaultIndex >= 0:
                    raise NarcissusError("More than one switch default", t)

                n2 = Node(t)
                if tt == consts["DEFAULT"]:
                    n.defaultIndex = len(n.cases)
                else:
                    n2.caseLabel = Expression(t, x, consts["COLON"])

                                        
            else:
                raise NarcissusError("Invalid switch case", t)

            t.mustMatch(consts["COLON"])
            n2.statements = Node(t, consts["BLOCK"])

            while True:
                tt = t.peek()
                if (tt == consts["CASE"]) or \
                    (tt==consts["DEFAULT"]) or \
                    (tt==consts["RIGHT_CURLY"]):
                    break

                print 'Yeah dude!'
                n2.statements.append(Statement(t, x))

            n.cases.append(n2)
            # End of while...
            
        x.stmtStack.pop()
        return n

    elif tt == consts["FOR"]:
        n = Node(t)
        n.isLoop = True

        n2 = None
        
        t.mustMatch(consts["LEFT_PAREN"])
        tt = t.peek()
        if tt != consts["SEMICOLON"]:
            x.inForLoopInit = True
            if tt == consts["VAR"] or tt == consts["CONST"]:
                print 'Got',t.get()
                n2 = Variables(t, x)
            else:
                n2 = Expression(t, x)

            x.inForLoopInit = False

        if n2 and t.match(consts["IN"]):
            n.type = consts["FOR_IN"]
            if n2.type == consts["VAR"]:
                if len(n2) != 1:
                    raise NarcissusError("Invalid for..in left-hand side", t)

                n.iterator = n2[0]
                n.varDecl = n2
            else:
                n.iterator = n2
                n.varDecl = None

            n.object = Expression(t, x)
        else:
            n.setup = n2 or None
            t.mustMatch(consts["SEMICOLON"])
            if (t.peek() == consts["SEMICOLON"]):
                n.condition = None
            else:
                n.condition = Expression(t, x)
            t.mustMatch(consts["SEMICOLON"])
            if (t.peek() == consts["RIGHT_PAREN"]):
                n.update = None
            else:
                n.update = Expression(t, x)

        t.mustMatch(consts["RIGHT_PAREN"])
        n.body = nest(t, x, n)
        return n

    elif tt == consts["WHILE"]:
        n = Node(t)
        n.isLoop = True
        n.condition = ParenExpression(t, x)
        n.body = nest(t, x, n)
        return n

    elif tt == consts["DO"]:
        n = Node(t)
        n.isLoop = True
        n.body = nest(t, x, n, consts["WHILE"])
        n.condition = ParenExpression(t, x)
        if not x.ecmaStrictMode:
            # <script language="JavaScript"> (without version hints) may need
            # automatic semicolon insertion without a newline after do-while.
            # See http://bugzilla.mozilla.org/show_bug.cgi?id=238945.
            t.match(consts["SEMICOLON"])
            return n
        
    elif (tt == consts["BREAK"]) or (tt == consts["CONTINUE"]):
        n = Node(t)
        if t.peekOnSameLine() == consts["IDENTIFIER"]:
            print 'Gewt',t.get()
            n.label = t.token().value

        ss = x.stmtStack
        i = len(ss)

        label = n.label
        if label:
            while True:
                i -= 1
                if i < 0:
                    raise NarcissusError("Label not found", t)
                if (ss[i].label != label): break
                
        else:
            while True:
                i -= 1

                if i<0:
                    if tt == consts["BREAK"]:
                        raise NarcissusError("Invalid break", t)
                    else:
                        raise NarcissusError("Invalid continue", t)

                if ss[i].isLoop or (tt==consts["BREAK"] and ss[i].type == consts["SWITCH"]):
                    break

        n.target = ss[i]        

    elif tt == consts["TRY"]:
        n = Node(t)
        n.tryBlock = Block(t, x)
        n.catchClauses = List2()

        while t.match(consts["CATCH"]):
            n2 = Node(t)
            t.mustMatch(consts["LEFT_PAREN"])
            n2.varName = t.mustMatch(consts["IDENTIFIER"]).value
            if t.match(consts["IF"]):
                if x.ecmaStrictMode:                
                    raise NarcissusError("Illegal catch guard", t)
                if len(n.catchClauses) and (not n.catchClauses.last().guard):
                    raise NarcissusError("Guarded catch after unguarded", t)
                n2.guard = Expression(t, x)
            else:
                n2.guard = None

            t.mustMatch(consts["RIGHT_PAREN"])
            n2.block = Block(t, x)
            n.catchClauses.append(n2)

        if t.match(consts["FINALLY"]):
            n.finallyBlock = Block(t, x) 
        if (not len(n.catchClauses)) and (not n.finallyBlock):
            raise NarcissusError("Invalid try statement", t)
        
        return n

    elif tt == consts["CATCH"]:
        pass
    elif tt == consts["FINALLY"]:
        raise NarcissusError(str(tokens[tt]) + " without preceding try", t)
    elif tt == consts["THROW"]:
        n = Node(t)
        n.exception = Expression(t, x)
    elif tt == consts["RETURN"]:
        print 'In Return'
        if not x.inFunction:
            raise NarcissusError("Invalid return", t)
        n = Node(t)
        tt = t.peekOnSameLine()
        if (tt != consts["END"]) and \
           (tt != consts["NEWLINE"]) and \
           (tt != consts["SEMICOLON"]) and \
           (tt != consts["RIGHT_CURLY"]):
            print 'Okay!'
            n.value = Expression(t, x)
            print "Val => " + str(n.value)

    elif tt == consts["WITH"]:
        n = Node(t)
        n.object = ParenExpression(t, x)
        n.body = nest(t, x, n)
        return n
            
    elif (tt == consts["VAR"]) or (tt==consts["CONST"]):
        n = Variables(t, x)

    elif tt == consts["DEBUGGER"]:
        n = Node(t)

    elif (tt==consts["NEWLINE"]) or (tt==consts["SEMICOLON"]):
        print 'out here'
        n = Node(t, consts["SEMICOLON"])
        n.expression = None
        return n

    else:
#         # print 'out there'
        if (tt==consts["IDENTIFIER"]) and (t.peek() == consts["COLON"]):
            label = t.token().value
            ss = x.stmtStack
            for x in range(len(ss)-1):
                if ss[i].label == label:
                    raise NarcissusError("Duplicate label", t)

            print 'GAWT',t.get()
            n = Node(t, consts["LABEL"])
            n.label = label
            n.statement = nest(t, x, n)
            return n

        t.unget()
        n = Node(t, consts["SEMICOLON"])
        n.expression = Expression(t, x)
        n.end = n.expression.end


    if t.lineno == t.token().lineno:
        tt = t.peekOnSameLine()
        print 'TT*=>',tt
        if tt != consts["END"] and \
           tt != consts["NEWLINE"] and \
           tt != consts["SEMICOLON"] and \
           tt != consts["RIGHT_CURLY"]:
            raise NarcissusError("Missing ; before statement", t)

    t.match(consts["SEMICOLON"])
    return n
              
            
    
def FunctionDefinition(t, x, requireName, functionForm):

    # t => an instance of Tokenizer
    f = Node(t)
    if f.type != consts["FUNCTION"]:
        f.type = (f.value == "get") and consts["GETTER"] or consts["SETTER"]
#     print f.type
    if t.match(consts["IDENTIFIER"]):
        f.name = t.token().value
    t.mustMatch(consts["LEFT_PAREN"])
    f.params = []

    while True:
        tt = t.get()
        print 'TT IZ',tt
        if tt==consts["RIGHT_PAREN"]: break
        if tt != consts["IDENTIFIER"]:
            raise NarcissusError("Missing formal parameters", t)
        f.params.append(t.token().value)
        if t.peek() != consts["RIGHT_PAREN"]:
            t.mustMatch(consts["COMMA"])

    t.mustMatch(consts["LEFT_CURLY"])
    x2 = CompilerContext(True)
    f.body = Script(t, x2)
    t.mustMatch(consts["RIGHT_CURLY"])
    f.end = t.token().end
    f.functionForm = functionForm
    if functionForm == consts.get("DECLARED_FORM"):
#         print 'okay'
        x.funDecls.append(f)

    return f

def Variables(t, x):

    n = Node(t)

    while True:
        t.mustMatch(consts["IDENTIFIER"])
        n2 = Node(t)
        n2.name = n2.value
        if t.match(consts["ASSIGN"]):
            if t.token().assignOp:
                raise NarcissusError("Invalid variable initialization", t)
#             print 'Initializing var...'
            n2.initializer = Expression(t, x, consts["COMMA"])

        n2.readOnly = ( n.type == consts["CONST"])
        # print 'vars=>',n2.type
#         print 'Starting to push'
        n.push(n2)
#         print "Push ended"        
        x.varDecls.append(n2)
        if not t.match(consts["COMMA"]): break
        
    return n

def ParenExpression(t, x):
    t.mustMatch(consts["LEFT_PAREN"])
    n = Expression(t, x)
    t.mustMatch(consts["RIGHT_PAREN"])
    return n

def Expression(t, x, stop = None):
    operators = List2()
    operands = List2()

    print 'In Expression',len(operands)

    bl = x.bracketLevel
    cl = x.curlyLevel
    pl = x.parenLevel
    hl = x.hookLevel

    def Reduce(operators, operands, t):
        # print 'Reduce called!'
        #for item in operators:
        #    print 'operator=>',item
            
        n = operators.pop()
        print 'N=>',n.type
        op = n.type
        arity = opArity[op]
        print 'Arity=>',arity
        if arity == -2:
            if len(operands) >= 2:
                # Flatten left-associative trees
                left = operands[len(operands) - 2]
                print 'Left=>',left
                
                if left.type == op:
                    print 'Dude!'
                    right = operands.pop()
                    left.append(right)
                    return (operators, operands, left)

            arity = 2

        # Always use push to add operands to n, to update start and end.
        # print 'Before slicing =>',len(operands)
        startidx, endidx = len(operands)-arity, 2*len(operands) - arity
        a = operands[startidx:endidx]
        operands = List2(operands[:startidx])
        # print 'After slicing =>',len(operands)
        # for x in operands:
        #     print "Optype=>",x.type
            
#         print a
#         print arity
        for x in range(arity):
#             print x
#             print a[x]
            # print 'Type=>',a[x].type
            n.push(a[x])

        # Include closing bracket or postfix operator in [start,end).
        if n.end < t.token().end:
            n.end = t.token().end

        operands.append(n)
        # print 'Operands length =>',len(operands)
        return (operators, operands, n)

    while True: # (t.token() and t.token().type != consts["END"]):
        if (t.token() and t.token().type == consts["END"]): break
        tt = t.get()
        if tt  == consts["END"]: break
        
        print 'TT ==>',tt
        # Stop only if tt matches the optional stop parameter, and that
        # token is not quoted by some kind of bracket.        
        if (tt==stop) and \
           (x.bracketLevel == bl) and \
           (x.curlyLevel == cl) and \
           (x.parenLevel == pl) and \
           (x.hookLevel == hl):
            break

        if tt == consts["SEMICOLON"]:
            # NB: cannot be empty, Statement handled that.
            break
        elif (tt==consts["ASSIGN"]) or \
             (tt==consts["HOOK"]) or \
             (tt==consts["COLON"]):
            if t.scanOperand:
                break

#             print 'here....'
#             print operators
#             print operands
#             print len(operands)
            # Use >, not >=, for right-associative ASSIGN and HOOK/COLON.            
            while len(operators) > 0 and \
                  opPrecedence.get(operators.last().type) and \
                  (opPrecedence.get(operators.last().type) > opPrecedence.get(tt)):

                operators, operands, ret = Reduce(operators, operands, t)

            # print 'Operands length2 =>',len(operands)
            if tt == consts["COLON"]:
                n = operators.last()
                if n.type != consts["HOOK"]:
                    raise NarcissusError("Invalid label", t)
            
                n.type = consts["CONDITIONAL"]
                x.hookLevel -= 1
            else:
                operators.append(Node(t))
                if tt == consts["ASSIGN"]:
#                     print operands
                    operands.last().assignOp = t.token().assignOp
                else:
                    x.hookLevel += 1 # tt == HOOK

            t.scanOperand = True

        # Treat comma as left-associative so reduce can fold left-heavy
        # COMMA trees into a single array.
        elif tt in (consts["COMMA"], consts["OR"], consts["AND"], consts["BITWISE_OR"],
                    consts["BITWISE_XOR"], consts["BITWISE_AND"], consts["EQ"],
                    consts["NE"], consts["STRICT_EQ"], consts["STRICT_NE"],
                    consts["LT"], consts["LE"], consts["GE"], consts["GT"],
                    consts["INSTANCEOF"], consts["LSH"], consts["RSH"],
                    consts["URSH"], consts["PLUS"], consts["MINUS"], consts["MUL"],
                    consts["DIV"], consts["MOD"], consts["DOT"], consts["IN"]):

            # print 'here...'
            # An in operator should not be parsed if we're parsing the head of
            # a for (...) loop, unless it is in the then part of a conditional
            # expression, or parenthesized somehow.            
            if (tt == consts["IN"]) and \
               x.inForLoopInit and \
               x.hookLevel == 0 and \
               x.bracketLevel == 0 and \
               x.curlyLevel == 0 and \
               x.parenLevel == 0:
                break

            if t.scanOperand:
                break

            while (len(operators)) and \
                  (opPrecedence.get(operators.last().type)) and \
                  (opPrecedence.get(operators.last().type) >= opPrecedence.get(tt)):
                operators, operands, ret = Reduce(operators, operands, t)

            # print 'Operands length2 =>',len(operands)
            
            if tt == consts["DOT"]:
                t.mustMatch(consts["IDENTIFIER"])
                node = Node(t, consts["DOT"])
                node.push(operands.pop())
                node.push(Node(t))
                operands.append(node)
            else:
                operators.append(Node(t))
                # print operators
                t.scanOperand = True

        elif tt in (consts["DELETE"], consts["VOID"], consts["TYPEOF"],
                    consts["NOT"], consts["BITWISE_NOT"], consts["UNARY_PLUS"],
                    consts["UNARY_MINUS"], consts["NEW"]):

            if not t.scanOperand:
                break

            operators.append(Node(t))

        elif tt in (consts["INCREMENT"], consts["DECREMENT"]):
            if t.scanOperand:
                operators.append(Node(t)) # prefix increment or decrement
            else:
                # Use >, not >=, so postfix has higher precedence than prefix.
                while (len(operators)) and \
                      (opPrecedence.get(operators.last().type)) and \
                      (opPrecedence.get(operators.last().type) > opPrecedence.get(tt)):
                    operators, operands, ret = Reduce(operators, operands, t)                    

                n = Node(t, tt)
                n.push(operands.pop())
                n.postfix = True
                operands.append(n)

        elif tt == consts["FUNCTION"]:
#             print 'HERE'
            if not t.scanOperand:
                break
            operands.append(FunctionDefinition(t, x, False, consts.get("EXPRESSED_FORM")))
            t.scanOperand = False

        elif tt in (consts["NULL"], consts["THIS"], consts["TRUE"], consts["FALSE"],
                    consts["IDENTIFIER"], consts["NUMBER"], consts["STRING"],
                    consts["REGEXP"]):

            if not t.scanOperand:
                break
            # print 'HERE2'
            operands.append(Node(t))
#             print operands
            t.scanOperand = False

        elif tt == consts["LEFT_BRACKET"]:
            if t.scanOperand:
                # Array initialiser.  Parse using recursive descent, as the
                # sub-grammar here is not an operator grammar.
                n = Node(t, consts["ARRAY_INIT"])

                while True:
                    tt = t.peek()
                    if tt == consts["RIGHT_BRACKET"]: break
                    if tt == consts["COMMA"]:
                        print 'Tt Iz',t.get()
                        n.push(None)

                        # FIXME: What is this next ?
                        next

                    n.push(Expression(t, x, consts["COMMA"]))
                    if not t.match(consts["COMMA"]):
                        continue
                    
                t.mustMatch(consts["RIGHT_BRACKET"])
                operands.append(n)
                t.scanOperand = False
            else:
                # Property indexing operator.
                operators.append(Node(t, consts["INDEX"]))
                t.scanOperand = True
                x.bracketLevel += 1

        elif tt == consts["RIGHT_BRACKET"]:
            if t.scanOperand or x.bracketLevel == bl:
                break

            while True:
                operators, operands, ret = Reduce(operators, operands, t)
                if ret.type == consts["INDEX"]: break
                pass
            x.bracketLevel -= 1

        elif tt == consts["LEFT_CURLY"]:
            if not t.scanOperand:
                break
            # Object initialiser.  As for array initialisers (see above),
            # parse using recursive descent.
            x.curlyLevel += 1
            n = Node(t, consts["OBJECT_INIT"])
            
            if not t.match(consts["RIGHT_CURLY"]):
                while True:
                    tt = t.get()
                    print 'tt IZ',tt
                    if (t.token().value == 'get') or (t.token().value=='set') and (t.peek() == consts["IDENTIFIER"]):
                        if x.ecmaStrictMode:
                            raise NarcissusError("Illegal property accessor", t)
                        n.push(FunctionDefinition(t, x, True, consts["EXPRESSED_FORM"]))
                    elif tt in (consts["IDENTIFIER"], consts["NUMBER"], consts["STRING"]):
                        id = Node(t)
                    elif tt == consts["RIGHT_CURLY"]:
                        if x.ecmaStrictMode:
                            raise NarcissusError("Illegal training", t)
                    else:
                        raise NarcissusError("Invalid property name", t)

                    t.mustMatch(consts["COLON"])
                    n2 = Node(t, consts["PROPERTY_INIT"])
                    n2.push(id)
                    n2.push(Expression(t, x, consts["COMMA"]))
                    n.push(n2)                    
                    if not t.match(consts["COMMA"]): break

                t.mustMatch(consts["RIGHT_CURLY"])

            operands.append(n)
            t.scanOperand = False
            x.curlyLevel -= 1

        elif tt == consts["RIGHT_CURLY"]:
            if not t.scanOperand and x.curlyLevel != cl:
                raise NarcissusError("PANIC: right curly botch", t)
            break

        elif tt == consts["LEFT_PAREN"]:
            if t.scanOperand:
                operators.append(Node(t, consts["GROUP"]))
            else:
                print operators, type(operators)
                while len(operators) and \
                      opPrecedence.get(operators.last().type) and \
                      opPrecedence.get(operators.last().type) > opPrecedence.get(consts["NEW"]):
                    operators, operands, ret = Reduce(operators, operands, t)

                # Handle () now, to regularize the n-ary case for n > 0.
                # We must set scanOperand in case there are arguments and
                # the first one is a regexp or unary+/-.
                n = operators.last()
                # print n, n.type, consts["NEW"]
                t.scanOperand = True
                print 'I WENT HERE'
                if t.match(consts["RIGHT_PAREN"]):
                    if n != None and n.type == consts["NEW"]:
                        print "INSIDE" 
                        operators.pop()
                        n.push(operands.pop())
                    else:
                        print "OUTSIDE"
                        n = Node(t, consts["CALL"])
                        n.push(operands.pop())
                        n.push(Node(t, consts["LIST"]))

                    operands.append(n)
                    t.scanOperand = False
                    continue
   
                if n != None and n.type == consts["NEW"]:
                    n.type = consts["NEW_WITH_ARGS"]
                else:
                    operators.append(Node(t, consts["CALL"]))

            x.parenLevel += 1

        elif tt == consts["RIGHT_PAREN"]:
            if t.scanOperand or x.parenLevel == pl:
                break
            while True:
                print 'Operators =>',len(operators),len(operands)
                
                operators, operands, tt = Reduce(operators, operands, t)
                print 'TT=>',tt,tt.type
                if (tt.type == consts["GROUP"]) or \
                       (tt.type == consts["CALL"]) or \
                       (tt.type == consts["NEW_WITH_ARGS"]):
                    print 'Breaking'
                    break
                
            if tt != consts["GROUP"]:
                n = operands.last()
                if n[1].type != consts["COMMA"]:
                    n2 = n[1]
                    n[1] = Node(t, consts["LIST"])
                    n[1].push(n2)
                else:
                    n[1].type = consts["LIST"]

            x.parenLevel -= 1
                
        else:
            # Automatic semicolon insertion means we may scan across a newline
            # and into the beginning of another statement.  If so, break out of
            # the while loop and let the t.scanOperand logic handle errors.
            break

    if x.hookLevel != hl:
        raise NarcissusError("Missing : after ?", t)
    if t.scanOperand:
        raise NarcissusError("Missing operand", t)

    # Resume default mode, scanning for operands, not operators.
    t.scanOperand = True
    print 'Ungetting...'
    print t.unget()
#     print 'HERE4'    
    while len(operators) > 0:
        operators, operands, ret = Reduce(operators, operands, t)

    # print 'Operands length2 =>',len(operands)        
    return operands.pop()
        
def parse(source, filename, line = 1):
    t = Tokenizer(source, filename, line)
    x = CompilerContext(False)
    n = Script(t, x)
    if not t.done:
        raise NarcissusError("Syntax error", t)

    return n


        

            
            
        
    
