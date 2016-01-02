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

import ast     # For Python abstract syntax trees.
import inspect # To retrieve a function body source.
#import sympy   # For symbolic polynomials and other expressions.

# The Pydrogen class can be extended to define a new operational
# semantics or abstract interpretation for abstract syntax trees,
# and then used as a decorator that is applied to functions that
# must be processed using that alternative semantics/interpretation.
class Pydrogen():
    def Num():
        return None

    def Str():
        return None

    def Bytes():
        return None

def __function(name):
    return ast.parse(inspect.getsource(name))   

##eof