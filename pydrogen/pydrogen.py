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
import sympy   # For symbolic polynomials and other expressions.

def __function(name):
    return ast.parse(inspect.getsource(name))

##eof
