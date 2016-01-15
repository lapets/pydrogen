###############################################################################
## 
## pydrogen.py
##
##   Python library for building embedded languages within Python
##   that have alternative operational semantics and abstract
##   interpretations.
##
##   Web:     pydrogen.org
##   Version: 0.0.1.0
##
##

###############################################################################
##

import ast     # For working with Python abstract syntax trees.
import inspect # To retrieve a function body's source code.
#import sympy  # For symbolic polynomials and other expressions.

# A PydrogenError occurs if a user of the library tries doing
# something the library does not currently support.
class PydrogenError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# A SemanticError occurs if a user-defined Pydrogen class does not
# handle a syntactic construct that is contained in the function body
# that the class must interpret.
class SemanticError(Exception):
    def __init__(self, value):
        if value == "Statements":
            self.value = "No semantics specified for statement sequences."
        else:
            self.value = "No semantics specified for '" + value + "' nodes."
    def __str__(self):
        return repr(self.value)

# The result of an alternative interpretation is a Function object
# that contains annotations for each of the possible alternative
# interpretations of the function. This makes it possible to
# "stack" decorators for multiple interpretations above a single
# function definition.
class Function():
    def __init__(self, func, cls, interpretation = None):
        self._func = func
        self._interpretations = {}
        if type(func) == Function:
            self._interpretations = func._interpretations
        self._interpretations[cls.__class__.__name__] = interpretation
    def __getattr__(self, attr):
        if (attr in self._interpretations): # Alternative interpretations.
            return self._interpretations[attr]
        return getattr(self._func, attr)
    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)
    def __repr__(self):
        return repr(self._func)
    def __str__(self):
        return str(self._func)

# An alternative interpretation algorithm may want access to the
# abstract syntax subtrees of a node both pre- and post-interpretation.
# Thus, both are supplied within an instance of the below wrapper class.
# Note the "lazy" evaluation of post-interpretation values (computed
# only if they are requested).
class Subtree():
    def __init__(self, pre, post = None):
        self._pre = pre
        self._post = post
    def pre(self):
        return self._pre
    def post(self):
        if self._post is None:
            raise PydrogenError(\
                    "Pydrogen does not currently support definitions for "\
                    + "alternative interpretations of nodes of this type: "\
                    + ast.dump(self._pre)\
                )
        return self._post()

# The Pydrogen class can be extended to define a new operational
# semantics or abstract interpretation for abstract syntax trees,
# and then used as a decorator that is applied to functions that
# must be processed using that alternative semantics/interpretation.
#
# The cases are derived directly from the Python abstract syntax
# definition (https://docs.python.org/3/library/ast.html), with a
# few deviations to accommodate the usage model for this library.
class Pydrogen():
    def __new__(cls, arg = None):
        # Either create a new object of this class in order to
        # process functions in the future (if no function is
        # supplied at the time of creation), or immediately
        # process the supplied function and return the result.
        # This allows the class to also be used as a decorator.
        # Abstract syntax tree arguments are simply interpreted
        # according to the class.
        if arg is None:
            return object.__new__(cls)
        elif hasattr(arg, '__call__'): # Is a function.
            return object.__new__(cls).process(arg)
        else:
            return object.__new__(cls).interpret(arg)

    def process(self, func):
        original = func._func if type(func) == Function else func
        return Function(func, self, self.interpret(ast.parse(inspect.getsource(original))))

    def interpret(self, a):
        if type(a) == ast.Module:
            return self.Module(Subtree(a.body, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.body]))))
        elif type(a) == ast.FunctionDef:
            return self.FunctionDef(Subtree(a.body, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.body]))))
        elif type(a) == ast.Return:
            return self.Return(Subtree(a.value, lambda:self.interpret(a.value)))
        elif type(a) == ast.Assign:
            return self.Assign(Subtree(targets), Subtree(a.value, lambda:self.interpret(a.value))) 
        elif type(a) == ast.For:
            return\
                self.For(\
                    Subtree(a.target), Subtree(a.iter, lambda:self.interpret(a.iter)),\
                    Subtree(a.body, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.body]))),\
                    Subtree(a.orelse, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.orelse])))\
                )
        elif type(a) == ast.While:
            return\
                self.While(\
                    Subtree(a.test, lambda:self.interpret(a.test)),\
                    Subtree(a.body, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.body]))),\
                    Subtree(a.orelse, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.orelse])))\
                )
        elif type(a) == ast.If:
            return\
                self.If(\
                    Subtree(a.test, lambda:self.interpret(a.test)),\
                    Subtree(a.body, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.body]))),\
                    Subtree(a.orelse, lambda:self.Statements(Subtree(a.body, lambda:[self.interpret(s) for s in a.orelse])))\
                )
        elif type(a) == ast.Expr:
            return self.interpret(a.value)
        elif type(a) == ast.Pass:
            return self.Pass()
        elif type(a) == ast.Break:
            return self.Break()
        elif type(a) == ast.Continue:
            return self.Continue()
        elif type(a) == ast.BoolOp:
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if type(a.op) == ast.And: return self.And(Subtree(a.values, lambda:[self.interpret(e) for e in a.values]))
                if type(a.op) == ast.Or: return self.Or(Subtree(a.values, lambda:[self.interpret(e) for e in a.values]))
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.BoolOp(Subtree(a.values, lambda:[self.interpret(e) for e in a.values]))
        elif type(a) == ast.BinOp:
            l = Subtree(a.left, lambda:self.interpret(a.left))
            r = Subtree(a.right, lambda:self.interpret(a.right))
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if type(a.op) == ast.Add: return self.Add(l, r)
                if type(a.op) == ast.Sub: return self.Sub(l, r)
                if type(a.op) == ast.Mult: return self.Mult(l, r)
                if type(a.op) == ast.MatMult: return self.MatMult(l, r)
                if type(a.op) == ast.Div: return self.Div(l, r)
                if type(a.op) == ast.Mod: return self.Mod(l, r)
                if type(a.op) == ast.Pow: return self.Pow(l, r)
                if type(a.op) == ast.LShift: return self.LShift(l, r)
                if type(a.op) == ast.RShift: return self.RShift(l, r)
                if type(a.op) == ast.BitOr: return self.BitOr(l, r)
                if type(a.op) == ast.BitXor: return self.BitXor(l, r)
                if type(a.op) == ast.BitAnd: return self.BitAnd(l, r)
                if type(a.op) == ast.FloorDiv: return self.FloorDiv(l, r)
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.BinOp(l, r)
        elif type(a) == ast.UnaryOp:
            b = Subtree(a.operand, lambda:self.interpret(a.operand))
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if type(a.op) == ast.Invert: return self.Invert(b)
                if type(a.op) == ast.Not: return self.Not(b)
                if type(a.op) == ast.UAdd: return self.UAdd(b)
                if type(a.op) == ast.USub: return self.USub(b)
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.UnaryOp(b)
        elif type(a) == ast.Set:
            return self.Set(Subtree(a.elts, lambda:[self.interpret(e) for e in a.elts]))
        elif type(a) == ast.Compare:
            if len(a.ops) == 1 and len(a.comparators) == 1:
                op = a.ops[0]
                right = a.comparators[0]
                l = Subtree(a.left, lambda:self.interpret(a.left))
                r = Subtree(right, lambda:self.interpret(right))
                # Performance is not usually a serious issue in abstract interpretation
                # and static analysis applications, so we use exceptions.
                try:
                    if type(op) == ast.Eq: return self.Eq(l, r)
                    if type(op) == ast.NotEq: return self.NotEq(l, r)
                    if type(op) == ast.Lt: return self.Lt(l, r)
                    if type(op) == ast.LtE: return self.LtE(l, r)
                    if type(op) == ast.Gt: return self.Gt(l, r)
                    if type(op) == ast.GtE: return self.GtE(l, r)
                    if type(op) == ast.Is: return self.Is(l, r)
                    if type(op) == ast.IsNot: return self.IsNot(l, r)
                    if type(op) == ast.In: return self.In(l, r)
                    if type(op) == ast.NotIn: return self.NotIn(l, r)
                except SemanticError: # Attempt catch-all definitions if above failed.
                    return self.Compare(l, r)
            else:
                raise PydrogenError("Pydrogen does not currently support expressions with chained comparison operations.")
        elif type(a) == ast.Call:
            return self.Call(Subtree(a.func), Subtree(a.args, lambda:[self.interpret(e) for e in a.args]))
        elif type(a) == ast.Num:
            return self.Num(Subtree(a.n, lambda:a.n))
        elif type(a) == ast.Str:
            return self.Str(Subtree(a.s, lambda:a.s))
        elif type(a) == ast.Bytes:
            return self.Bytes(Subtree(a.s, lambda:a.s))
        elif type(a) == ast.NameConstant:
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if a.value == True: return self.True_()
                if a.value == False: return self.False_()
                if a.value == None: return self.None_()
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.NameConstant()
        elif type(a) == ast.Name:
            return self.Name()
        elif type(a) == ast.List:
            return self.List(Subtree(a.elts, lambda:[self.interpret(e) for e in a.elts]))
        elif type(a) == ast.Tuple:
            return self.Tuple(Subtree(a.elts, lambda:[self.interpret(e) for e in a.elts]))
        else:
            raise PydrogenError("Pydrogen does not currently support nodes of this type: " + ast.dump(a))

    def Statements(self, ss): raise SemanticError("Statements") # Special case.

    def Module(self, ss): raise SemanticError("Module")
    def FunctionDef(self, ss): raise SemanticError("FunctionDef")
    def Return(self, e): raise SemanticError("Return")
    def Assign(self, targets, e): raise SemanticError("Assign")
    def For(self, target, iter, ss, orelse): raise SemanticError("For")
    def While(self, test, ss, orelse): raise SemanticError("While")
    def If(self, test, ss, orelse): raise SemanticError("If")

    def BoolOp(self, es): raise SemanticError("BoolOp")
    def BinOp(self, e1, e2): raise SemanticError("BinOp")
    def UnaryOp(self, e): raise SemanticError("UnaryOp")
    def Set(self, es): raise SemanticError("Set")
    def Compare(self, e1, e2): raise SemanticError("Compare")
    def Call(self, func, args): raise SemanticError("Call")
    def Num(self, n): raise SemanticError("Num")
    def Str(self, s): raise SemanticError("Str")
    def Bytes(self, b): raise SemanticError("Bytes")
    def NameConstant(self): raise SemanticError("NameConstant")
    def Name(self): raise SemanticError("Name")
    def List(self, es): raise SemanticError("List")
    def Tuple(self, es): raise SemanticError("Tuple")

    def And(self, es): raise SemanticError("And")
    def Or(self, es): raise SemanticError("Or")
    def Add(self, e1, e2): raise SemanticError("Add")
    def Sub(self, e1, e2): raise SemanticError("Sub")
    def Mult(self, e1, e2): raise SemanticError("Mult")
    def MatMult(self, e1, e2): raise SemanticError("MatMult")
    def Div(self, e1, e2): raise SemanticError("Div")
    def Mod(self, e1, e2): raise SemanticError("Mod")
    def Pow(self, e1, e2): raise SemanticError("Pow")
    def LShift(self, e1, e2): raise SemanticError("LShift")
    def RShift(self, e1, e2): raise SemanticError("RShift")
    def BitOr(self, e1, e2): raise SemanticError("BitOr")
    def BitXor(self, e1, e2): raise SemanticError("BixXor")
    def BitAnd(self, e1, e2): raise SemanticError("BitAnd")
    def FloorDiv(self, e1, e2): raise SemanticError("FloorDiv")
    def Invert(self, e): raise SemanticError("Invert")
    def Not(self, e): raise SemanticError("Not")
    def UAdd(self, e): raise SemanticError("UAdd")
    def USub(self, e): raise SemanticError("USub")

    def Eq(self, e1, e2): raise SemanticError("Eq")
    def NotEq(self, e1, e2): raise SemanticError("NotEq")
    def Lt(self, e1, e2): raise SemanticError("Lt")
    def LtE(self, e1, e2): raise SemanticError("LtE")
    def Gt(self, e1, e2): raise SemanticError("Gt")
    def GtE(self, e1, e2): raise SemanticError("GtE")
    def Is(self, e1, e2): raise SemanticError("Is")
    def IsNot(self, e1, e2): raise SemanticError("IsNot")
    def In(self, e1, e2): raise SemanticError("In")
    def NotIn(self, e1, e2): raise SemanticError("NotIn")

    def True_(self): raise SemanticError("True")
    def False_(self): raise SemanticError("False")
    def None_(self): raise SemanticError("None")

# A simple example extension containing the typical definitions,
# such as passing the recursive result up through 'Module' and
# 'FunctionDef' nodes.
class Typical(Pydrogen):
    def Module(self, ss): return ss.post()
    def FunctionDef(self, ss): return ss.post()
    def Return(self, e): return e.post()

# A simple example extension for computing the size of the abstract
# syntax tree.
class ASTSize(Typical):
    def Statements(self, ss): return sum(ss.post())

    def Return(self, e): return 1 + e.post()
    def Assign(self, targets, e): return 1 + e.post()

    def Call(self, func, args): return 1 + sum(args.post())
    def Num(self, n): return 1
    def NameConstant(self): return 1
    def Name(self): return 1

    def BoolOp(self, es): return 1 + sum(es.post())
    def BinOp(self, e1, e2): return 1 + e1.post() + e2.post()
    def UnaryOp(self, e): return 1 + e.post()
    def Compare(self, e1, e2): return 1 + e1.post() + e2.post()
    def NameConstant(self): return 1

##eof