#####################################################################
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

#####################################################################
## ...
##

import ast     # For working with Python abstract syntax trees.
import inspect # To retrieve a function body's source code.
#import sympy   # For symbolic polynomials and other expressions.

class PydrogenError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SemanticError(Exception):
    def __init__(self, value):
        if value == "Statements":
            self.value = "No semantics specified for statement sequences."
        else:
            self.value = "No semantics specified for '" + value + "' nodes."
    def __str__(self):
        return repr(self.value)

# The Pydrogen class can be extended to define a new operational
# semantics or abstract interpretation for abstract syntax trees,
# and then used as a decorator that is applied to functions that
# must be processed using that alternative semantics/interpretation.
#
# The cases are derived directly from the Python abstract syntax
# definition (https://docs.python.org/3/library/ast.html), with a
# few deviations to accommodate the usage model for this library.
class Pydrogen():
    def __new__(cls, func = None):
        # Either create a new object of this class in order to
        # process functions in the future (if no function is
        # supplied at the time of creation), or immediately
        # process the supplied function and return the result.
        # This allows the class to also be used as a decorator.
        if func is None:
            return object.__new__(cls)
        else:
            return object.__new__(cls).process(func)

    def process(self, func):
        a = ast.parse(inspect.getsource(func))
        return self.interpret(a)

    def interpret(self, a):
        if type(a) == ast.Module:
            return self.Module(self.Statements([self.interpret(s) for s in a.body]))
        elif type(a) == ast.FunctionDef:
            return self.FunctionDef(self.Statements([self.interpret(s) for s in a.body]))
        elif type(a) == ast.Return:
            return self.Return(self.interpret(a.value))
        elif type(a) == ast.Assign:
            return self.Assign(targets, self.interpret(a.value)) 
        elif type(a) == ast.For:
            return\
                self.For(\
                    a.target, a.iter,\
                    self.Statements([self.interpret(s) for s in a.body]),\
                    self.Statements([self.interpret(s) for s in a.orelse])\
                )
        elif type(a) == ast.While:
            return\
                self.While(\
                    a.test,\
                    self.Statements([self.interpret(s) for s in a.body]),\
                    self.Statements([self.interpret(s) for s in a.orelse])\
                )
        elif type(a) == ast.If:
            return\
                self.If(\
                    a.test,\
                    self.Statements([self.interpret(s) for s in a.body]),\
                    self.Statements([self.interpret(s) for s in a.orelse])\
                )
        elif type(a) == ast.Expr:
            return self.interpret(a.value)
        elif type(a) == ast.Pass:
            return self.Pass()
        elif type(a) == ast.Break:
            return self.Break()
        elif type(a) == ast.Continue:
            return self.Continue()
        elif type(a) == ast.Set:
            return self.Set([self.interpret(e) for e in a.elts])
        elif type(a) == ast.Compare:
            if len(a.ops) == 1 and len(a.comparators) == 1:
                op = a.ops[0]
                right = a.comparators[0]
                if type(op) == ast.Eq: return self.Eq(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.NotEq: return self.NotEq(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.Lt: return self.Lt(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.LtE: return self.LtE(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.Gt: return self.Gt(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.GtE: return self.GtE(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.Is: return self.Is(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.IsNot: return self.IsNot(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.In: return self.In(self.interpret(a.left), self.interpret(right))
                if type(op) == ast.NotIn: return self.NotIn(self.interpret(a.left), self.interpret(right))
            else:
                raise PydrogenError("Pydrogen does not currently support expressions with chained comparison operations.")
        elif type(a) == ast.Call:
            return self.Call(a.func, [self.interpret(e) for e in a.args])
        elif type(a) == ast.Num:
            return self.Num(a.n)
        elif type(a) == ast.Str:
            return self.Str(a.s)
        elif type(a) == ast.Bytes:
            return self.Bytes(a.s)
        elif type(a) == ast.List:
            return self.List([self.interpret(e) for e in a.elts])
        elif type(a) == ast.Tuple:
            return self.Tuple([self.interpret(e) for e in a.elts])
        elif type(a) == ast.BoolOp:
            if type(a.op) == ast.And: return self.And([self.interpret(e) for e in a.values])
            if type(a.op) == ast.Or: return self.Or([self.interpret(e) for e in a.values])
        elif type(a) == ast.BinOp:
            if type(a.op) == ast.Add: return self.Add(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.Sub: return self.Sub(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.Mult: return self.Mult(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.MatMult: return self.MatMult(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.Div: return self.Div(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.Mod: return self.Mod(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.Pow: return self.Pow(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.LShift: return self.LShift(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.RShift: return self.RShift(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.BitOr: return self.BitOr(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.BitXor: return self.BitXor(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.BitAnd: return self.BitAnd(self.interpret(a.left), self.interpret(a.right))
            if type(a.op) == ast.FloorDiv: return self.FloorDiv(self.interpret(a.left), self.interpret(a.right))
        elif type(a) == ast.UnaryOp:
            if type(a.op) == ast.Invert: return self.Invert(self.interpret(a.operand))
            if type(a.op) == ast.Not: return self.Not(self.interpret(a.operand))
            if type(a.op) == ast.UAdd: return self.UAdd(self.interpret(a.operand))
            if type(a.op) == ast.USub: return self.USub(self.interpret(a.operand))
        else:
            raise PydrogenError("Pydrogen does not currently support nodes of this type: " + ast.dump(a))

    def Module(self, ss): raise SemanticError("Module")
    def FunctionDef(self, ss): raise SemanticError("FunctionDef")
    def Return(self, e): raise SemanticError("Return")
    def Assign(self, targets, e): raise SemanticError("Assign")
    def Statements(self, ss): raise SemanticError("Statements") # Special case.
    def For(self, target, iter, ss, orelse): raise SemanticError("For")
    def While(self, test, ss, orelse): raise SemanticError("While")
    def If(self, test, ss, orelse): raise SemanticError("If")

    def Set(self, es): raise SemanticError("Set")
    def Call(self, func, args): raise SemanticError("Call")
    def Num(self, n): raise SemanticError("Num")
    def Str(self, s): raise SemanticError("Str")
    def Bytes(self, b): raise SemanticError("Bytes")
    def List(self, es): raise SemanticError("List")
    def Tuple(self, es): raise SemanticError("Tuple")

    def And(self, e1, e2): raise SemanticError("And")
    def Or(self, e1, e2): raise SemanticError("Or")
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

# A simple example extension containing the typical definitions,
# such as passing the recursive result up through 'Module' and
# 'FunctionDef' nodes.
class Typical(Pydrogen):
    def Module(self, ss): return ss
    def FunctionDef(self, ss): return ss
    def Return(self, e): return e

# A simple example extension for computing the size of the abstract
# syntax tree.
class Size(Typical):
    def Statements(self, ss): return sum(ss)
    def Call(self, func, args): return sum(args)
    def Num(self, n): return 1

##eof