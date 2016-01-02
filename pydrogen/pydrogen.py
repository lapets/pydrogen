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
        elif type(a) == ast.For:
            return\
                self.For(\
                    a.target, a.iter,\
                    self.Statements([self.interpret(s) for s in a.body]),\
                    self.Statements([self.interpret(s) for s in a.orelse])\
                )
        elif type(a) == ast.Return:
            return self.Return(self.interpret(a.value))
        elif type(a) == ast.Expr:
            return self.interpret(a.value)
        elif type(a) == ast.Call:
            return self.Call(a.func, [self.interpret(e) for e in a.args])
        elif type(a) == ast.Num:
            return self.Num(a.n)
        else:
            raise PydrogenError("Pydrogen does not currently support nodes of this type: " + ast.dump(a))

    def Module(self, ss): raise SemanticError("Module")
    def FunctionDef(self, ss): raise SemanticError("FunctionDef")
    def Return(self, e): raise SemanticError("Return")
    def Statements(self, ss): raise SemanticError("Statements")
    def For(self, target, iter, body, orelse): raise SemanticError("For")
    def Call(self, func, args): raise SemanticError("Call")
    def Num(self, n): raise SemanticError("Num")
    def Str(): raise SemanticError("Str")
    def Bytes(): raise SemanticError("Bytes")
    def List(): raise SemanticError("List")

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