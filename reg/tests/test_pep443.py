from __future__ import division
from __future__ import unicode_literals
from reg.pep443 import singledispatch
from decimal import Decimal


@singledispatch
def fun(arg, verbose=False):
    if verbose:
        return "Let me just say, %s" % arg
    return arg


@fun.register(int)
def int_func(arg, verbose=False):
    if verbose:
        return "Strength in numbers, eh? %s" % arg
    return arg


@fun.register(list)
def list_fun(arg, verbose=False):
    result = []
    if verbose:
        result.append("Enumerate this:\n")
    for i, elem in enumerate(arg):
        result.append("%s %s\n" % (i, elem))
    return ''.join(result)


def nothing(arg, verbose=False):
    return "Nothing."


@fun.register(float)
@fun.register(Decimal)
def fun_num(arg, verbose=False):
    if verbose:
        return "Half of your number: %s" % arg
    return arg / 2


def test_string():
    assert fun("Hello, world.") == "Hello, world."
    assert fun("test.", verbose=True) == "Let me just say, test."


def test_int():
    assert fun(42, verbose=True) == "Strength in numbers, eh? 42"


def test_list():
    assert fun(['spam', 'spam', 'eggs', 'spam'], verbose=True) == '''\
Enumerate this:
0 spam
1 spam
2 eggs
3 spam
'''


def test_none():
    fun.register(type(None), nothing)
    assert fun(None) == "Nothing."


def test_multi_reg():
    assert fun(1.23) == 0.615
    assert fun(Decimal('1.23')) == Decimal('0.615')
