import ast
import inspect
import pydrogen
import sympy
from sympy import O, symbols, oo

class Complexity(pydrogen.Typical):
    """ Complexity approximation for a small subset of Python. """
    # some complexity classes using sympy's O notation
    poly = lambda _, n, power: O(n**power, (n, oo))
    log = lambda _, n: O(sympy.log(n), (n,oo))
    exp = lambda _, n, base: O(base**n, (n,oo))
    constant = O(1)

    # store the complexity of some known functions for added expressibility
    functions = {'len': constant}

    def preprocess(self, context):
        syms = []
        for var, symbol in context.items():
            if type(symbol) == str:
                symbol = symbols(symbol)
                context[var] = symbol
            syms.append((symbol, oo))

    def Statements(self, ss, context=None): return sum(ss.post(context)[0])
    def Assign(self, targets, e, context=None): return self.constant + e.post(context)
    # if iterable maps to a symbol, use it. otherwise, assume it is constant.
    def For(self, target, itr, ss, orelse, context=None):
        itr = itr.pre().id
        if itr in context:
            loops = self.poly(context[itr], 1)
        else:
            loops = self.constant
        work = ss.post(context)
        # sympy raises error if you try to do O(1) * O(x, (x,oo)) for e.g.
        return loops * work if work.contains(loops) else work * loops
    def BoolOp(self, es, context=None): return self.constant + sum(es.post(context))
    def BinOp(self, e1, e2, context): return self.constant + e1.post(context) + e2.post(context)
    def Call(self, func, args, context=None):
        func = func.pre()
        if context is None:
            context = {}
        return self.functions[func.id] if func.id in self.functions else Complexity(func, **context)
    def Num(self, n, context=None): return 0
    def NameConstant(self): return 0
    def Name(self, id, context=None): return 0

@Complexity(items='n')
def average(items):
    total = 0
    for item in items:
        for item in items:
            total = total + item
    return total/len(items)


#####################################################################
## Defining a running time approximation algorithm for a small subset
## of Python.
##

class Size(pydrogen.Typical):
    def Statements(self, ss): return sum(ss.post())
    def List(self, elts): return len(elts.post())
    def Num(self, n): return n.post()
    def Call(self, func, args): return 1 + sum(args.post())
    def BinOp(self, e1, e2): return 1 + e1.post() + e2.post()
    def Name(self): return 1

class Time(pydrogen.Typical):
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


print("The approximate running time of example() is " + str(example.Time) + ".")


"""
@Time
def eg():
    return [a*y for a in [1,2,3,4] if a == 1 for y in [1,2,3,4] if y == 2]
"""
##eof
