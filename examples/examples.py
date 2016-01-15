#####################################################################
## 
## examples.py
##
##   Small examples that illustrate how the pydrogen.py module can
##   be used.
##
##

import pydrogen

#####################################################################
## Computing the size of the abstract syntax tree of a function body.
##

@pydrogen.ASTSize
def add(x, y):
    return x + y

print("The size of the function body is " + str(add.ASTSize) + ".")

#####################################################################
## Defining a simple type checking algorithm.
##

class Ty(pydrogen.Pydrogen):
    def Statements(self, ss): return ss.post()[-1] # Last statement.
    def Module(self, ss): return ss.post()
    def FunctionDef(self, ss): return ss.post()
    def Return(self, e): return e.post()

    def True_(self): return 'Bool'
    def False_(self): return 'Bool'
    def BoolOp(self, es): return 'Bool'if frozenset(es.post()) == {'Bool'} else 'Error'
    def Not(self, e): return 'Bool' if e.post() == 'Bool' else 'Error'

    def Num(self, n): return 'Int'
    def Add(self, e1, e2): return 'Int' if e1.post() == 'Int' and e2.post() == 'Int' else 'Error'
    def Sub(self, e1, e2): return 'Int' if e1.post() == 'Int' and e2.post() == 'Int' else 'Error'
    def Mult(self, e1, e2): return 'Int' if e1.post() == 'Int' and e2.post() == 'Int' else 'Error'
    def USub(self, e): return 'Int' if e.post() == 'Int' else 'Error'

# Stacking is possible.
@Ty
@pydrogen.ASTSize
def correct():
    return -1 + 2 - 3 * 4

print("The type of 'correct' is " + str(correct.Ty) + ".")

@Ty
def incorrect():
    return 123 and False

print("The type of 'incorrect' is " + str(incorrect.Ty) + ".")

#####################################################################
## Defining a running time approximation algorithm for a small subset
## of Python.
##

class Size(pydrogen.Typical):
    def List(self, elts): return len(elts.post())
    def Num(self, n): return 1

class Time(pydrogen.Typical):
    def Statements(self, ss): return sum(ss.post())
    def Assign(self, targets, e): return 1 + e.post()
    def For(self, target, itr, ss, orelse): return Size(itr.pre()) * (1 + ss.post())
    def BoolOp(self, es): return 1 + sum(es.post())
    def BinOp(self, e1, e2): return 1 + e1.post() + e2.post()
    def Call(self, func, args): return 1 + sum(args.post())
    def Num(self, n): return 0
    def NameConstant(self): return 0

@Time
def example():
    for x in [1,2,3,4,5,6,7]:
        print(True and False)
        print(123 + 456)

print("The approximate running time of example is " + str(example.Time) + ".")

##eof
