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
        # we want to create the Function object with the original function to
        # allow any other stacked interpretations to access it -- this means the
        # interpretations will be independent of each other, but the final
        # returned Function will have access to all the interpretations
        self._interpretations = {}
        if type(func) == Function:
            self._interpretations.update(func._interpretations)
            self._func = func._func
        else:
            self._func = func
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
    def post(self, context = None):
        if self._post is None:
            raise PydrogenError(\
                    "Pydrogen does not currently support definitions for "\
                    + "alternative interpretations of nodes of this type: "\
                    + ast.dump(self._pre)\
                )
        result = self._post(context)
        if type(result) == tuple:
            if context is None:
                return result[0] # Discard context.
            else:
                return result # With context.
        else:
            return result

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
        return Function(func, self, self.interpret(ast.parse(inspect.getsource(original)), {}))

    # Attempt running the function with only the number of arguments
    # that it can handle. This allows users to completely ignore the
    # context argument if they do not need contexts in their alternative
    # interpretation.
    def attempt(self, f, *args):
        return f(*args[0:len(inspect.getargspec(f).args)-1])

    # Interpret a list of abstract syntax tree nodes in order, threading the
    # context through the process (or throwing it away if it is not supplied).
    def interprets(self, ss, context = None):
        rs = []
        for s in ss:
            r = self.interpret(s, context)
            if type(r) == tuple:
                (r, context) = r
            rs.append(r)
        if context is None:
            return rs
        else:
            return (rs, context)

    # Interpret a single abstract syntax tree node by calling the appropriate
    # (user-overloaded) handler for that node. Note that we attempt to use a
    # handler that can accept a context, and if that fails, we revert to a
    # call without a context.
    def interpret(self, a, context = None):
        if type(a) == ast.Module:
            body = Subtree(
                    a.body,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.body, lambda context: self.interprets(a.body, context)),
                        context))
            return self.attempt(self.Module, body, context)

        elif type(a) == ast.FunctionDef:
            body = Subtree(
                    a.body,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.body, lambda context: self.interprets(a.body, context)),
                        context))
            return self.attempt(self.FunctionDef, body, context)

        elif type(a) == ast.Return:
            value = Subtree(a.value, lambda context: self.interpret(a.value, context))
            return self.attempt(self.FunctionDef, value, context)

        elif type(a) == ast.Assign:
            value = Subtree(a.value, lambda context: self.interpret(a.value, context))
            return self.attempt(self.Assign, Subtree(a.targets), value, context)

        elif type(a) == ast.For:
            iter = Subtree(a.iter, lambda context: self.interpret(a.iter, context))
            body = Subtree(
                    a.body,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.body, lambda context: self.interprets(a.body, context)),
                        context))
            orelse = Subtree(
                    a.orelse,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.orelse, lambda context: self.interprets(a.orelse, context)),
                        context))
            return self.attempt(self.For, Subtree(a.target), iter, body, orelse, context)

        elif type(a) == ast.While:
            test = Subtree(a.test, lambda context: self.interpret(a.test, context))
            body = Subtree(
                    a.body,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.body, lambda context: self.interprets(a.body, context)),
                        context))
            orelse = Subtree(
                    a.orelse,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.orelse, lambda context: self.interprets(a.orelse, context)),
                        context))
            return self.attempt(self.While, test, body, orelse, context)

        elif type(a) == ast.If:
            test = Subtree(a.test, lambda context: self.interpret(a.test, context))
            body = Subtree(
                    a.body,
                    lambda context: self.attempt(
                        self.Statements, Subtree(a.body, lambda context: self.interprets(a.body, context)),
                        context))
            orelse = Subtree(
                    a.orelse,
                    lambda context: self.attempt(
                        self.Statements,
                        Subtree(a.orelse, lambda context: self.interprets(a.orelse, context)),
                        context))
            return self.attempt(self.If, test, body, orelse, context)

        elif type(a) == ast.Expr:
            return self.interpret(a.value, context)

        elif type(a) == ast.Pass:
            return self.attempt(self.Pass, context)

        elif type(a) == ast.Break:
            return self.attempt(self.Break, context)

        elif type(a) == ast.Continue:
            return self.attempt(self.Continue, context)

        elif type(a) == ast.BoolOp:
            values = Subtree(a.values, lambda context: self.interprets(a.values, context))
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if type(a.op) == ast.And: return self.attempt(self.And, values, context)
                if type(a.op) == ast.Or:  return self.attempt(self.Or, values, context)
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.attempt(self.BoolOp, values, context)

        elif type(a) == ast.BinOp:
            l = Subtree(a.left, lambda context: self.interpret(a.left, context))
            r = Subtree(a.right, lambda context: self.interpret(a.right, context))
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if type(a.op) == ast.Add: return self.attempt(self.Add, l, r, context)
                if type(a.op) == ast.Sub: return self.attempt(self.Sub, l, r, context)
                if type(a.op) == ast.Mult: return self.attempt(self.Mult, l, r, context)
                if type(a.op) == ast.MatMult: return self.attempt(self.MatMult, l, r, context)
                if type(a.op) == ast.Div: return self.attempt(self.Div, l, r, context)
                if type(a.op) == ast.Mod: return self.attempt(self.Mod, l, r, context)
                if type(a.op) == ast.Pow: return self.attempt(self.Pow, l, r, context)
                if type(a.op) == ast.LShift: return self.attempt(self.LShift, l, r, context)
                if type(a.op) == ast.RShift: return self.attempt(self.RShift, l, r, context)
                if type(a.op) == ast.BitOr: return self.attempt(self.BitOr, l, r, context)
                if type(a.op) == ast.BitXor: return self.attempt(self.BitXor, l, r, context)
                if type(a.op) == ast.BitAnd: return self.attempt(self.BitAnd, l, r, context)
                if type(a.op) == ast.FloorDiv: return self.attempt(self.FloorDiv, l, r, context)
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.attempt(self.BinOp, l, r, context)

        elif type(a) == ast.UnaryOp:
            operand = Subtree(a.operand, lambda context: self.interpret(a.operand, context))
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if type(a.op) == ast.Invert: return self.attempt(self.Invert, operand, context)
                if type(a.op) == ast.Not: return self.attempt(self.Not, operand, context)
                if type(a.op) == ast.UAdd: return self.attempt(self.UAdd, operand, context)
                if type(a.op) == ast.USub: return self.attempt(self.USub, operand, context)
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.attempt(self.UnaryOp, operand, context)

        elif type(a) == ast.Set:
            return self.attempt(
                    self.Set,
                    Subtree(a.elts, lambda context: self.interprets(a.elts, context)),
                    context)

        elif type(a) == ast.Compare:
            if not(len(a.ops) == 1 and len(a.comparators) == 1):
                raise PydrogenError("Pydrogen does not currently support expressions with chained comparison operations.")
            else:
                op = a.ops[0]
                right = a.comparators[0]
                l = Subtree(a.left, lambda context: self.interpret(a.left, context))
                r = Subtree(right, lambda context: self.interpret(right, context))
                # Performance is not usually a serious issue in abstract interpretation
                # and static analysis applications, so we use exceptions.
                try:
                    if type(op) == ast.Eq: return self.attempt(self.Eq, l, r, context)
                    if type(op) == ast.NotEq: return self.attempt(self.NotEq, l, r, context)
                    if type(op) == ast.Lt: return self.attempt(self.Lt, l, r, context)
                    if type(op) == ast.LtE: return self.attempt(self.LtE, l, r, context)
                    if type(op) == ast.Gt: return self.attempt(self.Gt, l, r, context)
                    if type(op) == ast.GtE: return self.attempt(self.GtE, l, r, context)
                    if type(op) == ast.Is: return self.attempt(self.Is, l, r, context)
                    if type(op) == ast.IsNot: return self.attempt(self.IsNot, l, r, context)
                    if type(op) == ast.In: return self.attempt(self.In, l, r, context)
                    if type(op) == ast.NotIn: return self.attempt(self.NotIn, l, r, context)
                except SemanticError: # Attempt catch-all definitions if above failed.
                    return self.attempt(self.Compare, l, r, context)

        elif type(a) == ast.Call:
            return self.attempt(
                    self.Call,
                    Subtree(a.func),
                    Subtree(a.args, lambda context: self.interprets(a.args, context)),
                    context)

        elif type(a) == ast.Num:
            return self.attempt(self.Num, Subtree(a.n, lambda context: a.n), context)

        elif type(a) == ast.Str:
            return self.attempt(self.Str, Subtree(a.s, lambda context: a.s), context)

        elif type(a) == ast.Bytes:
            return self.attempt(self.Bytes, Subtree(a.s, lambda context: a.s), context)

        elif type(a) == ast.NameConstant:
            # Performance is not usually a serious issue in abstract interpretation
            # and static analysis applications, so we use exceptions.
            try:
                if a.value == True: return self.attempt(self.True_, context)
                if a.value == False: return self.attempt(self.False_, context)
                if a.value == None: return self.attempt(self.None_, context)
            except SemanticError: # Attempt catch-all definitions if above failed.
                return self.attempt(self.NameConstant, context)

        elif type(a) == ast.Name:
            return self.attempt(self.Name, Subtree(a.id, lambda context: a.id), context)

        elif type(a) == ast.List:
            return self.attempt(
                    self.List,
                    Subtree(a.elts, lambda context: self.interprets(a.elts, context)),
                    context)

        elif type(a) == ast.Tuple:
            return self.attempt(
                    self.Tuple,
                    Subtree(a.elts, lambda context: self.interprets(a.elts, context)),
                    context)

        elif type(a) == ast.ListComp:
            # a list comprehension contains elt, the element being generated,
            # and generators, a list of comprehensions -- (target, iter, ifs)
            # tuples -- that generate the final list of elts
            iter_node = lambda iter: Subtree(iter, lambda context: self.interpret(iter, context))
            if_node = lambda i: Subtree(i, lambda context: self.interpret(i, context))
            comp = lambda g: (Subtree(g.target), iter_node(g.iter), [if_node(i) for i in g.ifs])
            generators = [comp(g) for g in a.generators]
            return self.attempt(
                    self.ListComp,
                    Subtree(a.elt, lambda context: self.interpret(a.elt, context)),
                    generators,
                    context)

        else:
            raise PydrogenError("Pydrogen does not currently support nodes of this type: " + ast.dump(a))

    # Special case.
    def Statements(self, ss, context = None): raise SemanticError("Statements (Pydrogen-specific case)")

    def Module(self, ss, context = None): raise SemanticError("Module")
    def FunctionDef(self, ss, context = None): raise SemanticError("FunctionDef")
    def Return(self, e, context = None): raise SemanticError("Return")
    def Assign(self, targets, e, context = None): raise SemanticError("Assign")
    def For(self, target, iter, ss, orelse, context = None): raise SemanticError("For")
    def While(self, test, ss, orelse, context = None): raise SemanticError("While")
    def If(self, test, ss, orelse, context = None): raise SemanticError("If")
    def Pass(self, context = None): raise SemanticError("Pass")
    def Break(self, context = None): raise SemanticError("Break")
    def Continue(self, context = None): raise SemanticError("Continue")
    def ListComp(self, elt, generators, context = None): raise SemanticError("ListComp")

    def BoolOp(self, es, context = None): raise SemanticError("BoolOp")
    def BinOp(self, e1, e2, context = None): raise SemanticError("BinOp")
    def UnaryOp(self, e, context = None): raise SemanticError("UnaryOp")
    def Set(self, es, context = None): raise SemanticError("Set")
    def Compare(self, e1, e2, context = None): raise SemanticError("Compare")
    def Call(self, func, args, context = None): raise SemanticError("Call")
    def Num(self, n, context = None): raise SemanticError("Num")
    def Str(self, s, context = None): raise SemanticError("Str")
    def Bytes(self, b, context = None): raise SemanticError("Bytes")
    def NameConstant(self, context = None): raise SemanticError("NameConstant")
    def Name(self, id, context = None): raise SemanticError("Name")
    def List(self, es, context = None): raise SemanticError("List")
    def Tuple(self, es, context = None): raise SemanticError("Tuple")

    def And(self, es, context = None): raise SemanticError("And")
    def Or(self, es, context = None): raise SemanticError("Or")
    def Add(self, e1, e2, context = None): raise SemanticError("Add")
    def Sub(self, e1, e2, context = None): raise SemanticError("Sub")
    def Mult(self, e1, e2, context = None): raise SemanticError("Mult")
    def MatMult(self, e1, e2, context = None): raise SemanticError("MatMult")
    def Div(self, e1, e2, context = None): raise SemanticError("Div")
    def Mod(self, e1, e2, context = None): raise SemanticError("Mod")
    def Pow(self, e1, e2, context = None): raise SemanticError("Pow")
    def LShift(self, e1, e2, context = None): raise SemanticError("LShift")
    def RShift(self, e1, e2, context = None): raise SemanticError("RShift")
    def BitOr(self, e1, e2, context = None): raise SemanticError("BitOr")
    def BitXor(self, e1, e2, context = None): raise SemanticError("BixXor")
    def BitAnd(self, e1, e2, context = None): raise SemanticError("BitAnd")
    def FloorDiv(self, e1, e2, context = None): raise SemanticError("FloorDiv")
    def Invert(self, e, context = None): raise SemanticError("Invert")
    def Not(self, e, context = None): raise SemanticError("Not")
    def UAdd(self, e, context = None): raise SemanticError("UAdd")
    def USub(self, e, context = None): raise SemanticError("USub")

    def Eq(self, e1, e2, context = None): raise SemanticError("Eq")
    def NotEq(self, e1, e2, context = None): raise SemanticError("NotEq")
    def Lt(self, e1, e2, context = None): raise SemanticError("Lt")
    def LtE(self, e1, e2, context = None): raise SemanticError("LtE")
    def Gt(self, e1, e2, context = None): raise SemanticError("Gt")
    def GtE(self, e1, e2, context = None): raise SemanticError("GtE")
    def Is(self, e1, e2, context = None): raise SemanticError("Is")
    def IsNot(self, e1, e2, context = None): raise SemanticError("IsNot")
    def In(self, e1, e2, context = None): raise SemanticError("In")
    def NotIn(self, e1, e2, context = None): raise SemanticError("NotIn")

    def True_(self, context = None): raise SemanticError("True")
    def False_(self, context = None): raise SemanticError("False")
    def None_(self, context = None): raise SemanticError("None")

# A simple example extension containing the typical definitions,
# such as passing the recursive result up through 'Module' and
# 'FunctionDef' nodes.
class Typical(Pydrogen):
    def Module(self, ss, context): return ss.post(context)
    def FunctionDef(self, ss, context): return ss.post(context)
    def Return(self, e, context): return e.post(context)

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
