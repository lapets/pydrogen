import ast
import inspect
import pydrogen
import sympy
from sympy import O, symbols, oo


# some complexity classes using sympy's O notation
linear = lambda n: O(n, (n, oo))
quadratic = lambda n: O(n**2, (n,oo))
logarithmic = lambda n: O(sympy.log(n, 2), (n,oo))
exponential = lambda n: O(2**n, (n,oo))
constant = lambda _: O(1)

class Complexity(pydrogen.Typical):
    """ Complexity approximation for a small subset of Python. """

    # store the complexity of some known functions for added expressibility
    functions = {'len': constant}

    def preprocess(self, context):
        syms = []
        # allow for specification of running time of certain functions as well (?)
        if 'functions' in context and type(context['functions']) == dict:
            self.functions.update(context['functions'])
            del context['functions']
        for var, symbol in context.items():
            if type(symbol) == str:
                symbol = symbols(symbol)
                context[var] = symbol
            syms.append((symbol, oo))

    def Statements(self, ss, context=None): return sum(ss.post(context)[0])
    def Assign(self, targets, e, context=None): return constant(None) + e.post(context)
    # if iterable maps to a symbol, use it. otherwise, assume it is constant.
    def For(self, target, itr, ss, orelse, context=None):
        # we make the simplifying assumption that whatever being iterated over
        # is either:
        #   a named variable, where we look up the context for a symbol and
        #       regard as constant size if not present
        #   a built-in sequence (list, string, dictionary, tuple, set) which we
        #       regard as constant size
        #   a function call, where we assume that the complexity of the function
        #       call is also the size of the iterable returned. This is
        #       obviously not always the case but we assume relatively
        #       simple functions.
        if hasattr(itr.pre(), 'id'):
            itr = itr.pre().id
            if itr in context:
                loops = linear(context[itr])
            else:
                loops = constant(None)
        elif type(itr.pre()) in (ast.List, ast.Tuple, ast.Str, ast.Dict, ast.Set):
            loops = constant(None)
        else:
            loops = itr.post(context)
        work = ss.post(context)
        # sympy raises error if you try to do O(1) * O(x, (x,oo)) for e.g.
        return loops * work if work.contains(loops) else work * loops
    def BoolOp(self, es, context=None): return constant(None) + sum(es.post(context))
    def BinOp(self, e1, e2, context): return constant(None) + e1.post(context) + e2.post(context)
    def Call(self, func, args, context=None):
        func = func.pre()
        if context is None:
            context = {}
        if func.id in self.functions:
            symbol = None
            # check context if any arg maps to a symbol; take first one we find
            # and return complexity class of the function.
            for arg in args.pre():
                if arg.id in context:
                    symbol = context[arg.id]
                    break
            if symbol or self.functions[func.id] == constant:
                return self.functions[func.id](symbol)
        # otherwise, attempt to interpret the function directly
        return Complexity(func, **context)
    def Num(self, n, context=None): return 0
    def NameConstant(self): return 0
    def Name(self, id, context=None): return 0
    def If(self, test, body, orelse, context=None):
        return test.post(context) + body.post(context) + orelse.post(context)
    def Compare(self, l, r, context=None):
        return constant(None) + l.post(context) + r.post(context)

@Complexity(items='n')
def average(items):
    total = 0
    for item in [1,2,3,4]:
        for item in items:
            total = total + item
    return total/len(items)

# print('The asymptotic complexity of average() is ' + str(average.Complexity) + '.')


class Size(pydrogen.Typical):
    """ Analyze size of AST for a subset of Python. """
    def Statements(self, ss): return sum(ss.post())
    def List(self, elts): return len(elts.post())
    def Num(self, n): return n.post()
    def Call(self, func, args): return 1 + sum(args.post())
    def BinOp(self, e1, e2): return 1 + e1.post() + e2.post()
    def Name(self): return 1

class Time(pydrogen.Typical):
    """ Numeric running time approximation for a small subset of Python. """
    def Statements(self, ss): return sum(ss.post())
    def Assign(self, targets, e): return 1 + e.post()
    def For(self, target, itr, ss, orelse): return Size(itr.pre()) * ss.post()
    def BoolOp(self, es): return 1 + sum(es.post())
    def BinOp(self, e1, e2): return 1 + e1.post() + e2.post()
    def Call(self, func, args): return 1 + sum(args.post())
    def Num(self, n): return 0
    def NameConstant(self): return 0
    def Name(self): return 0
    def List(self, elts): return len(elts.post())
    """
    def ListComp(self, elt, generators):
        size = 1
        total = 0
        for target, iter, ifs in generators:
            # for each generator:
            # multiply size of iterable since each amounts to a nested loop
            # for filters at a given generator, assume it operates on all
            # generated values thus far, so multiply "cumulative" size by
            # comparison cost
            size *= Size(iter.pre())
            total += size * sum([i.post() for i in ifs])
        # upper bound the final computation required to generate each element
        return total + (elt.post() * size)
    """

    def If(self, test, body, orelse): return test.post() + body.post()
    def Compare(self, l, r): return 1 + l.post() + r.post()

@Time
def example():
    for i in range(100):
        print(i + i + 1)

# print('The approximate running time of example() is ' + str(example.Time) + '.')

##eof
