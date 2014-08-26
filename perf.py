import timeit

from reg.registry import ClassRegistry
from reg.generic import generic
from reg.compose import CachingClassLookup
from reg.lookup import Lookup

@generic
def args0():
    raise NotImplementedError()

@generic
def args1(a):
    raise NotImplementedError()

@generic
def args2(a, b):
    raise NotImplementedError()

@generic
def args3(a, b, c):
    raise NotImplementedError()

@generic
def args4(a, b, c, d):
    raise NotImplementedError()

class Foo(object):
    pass

def myargs0():
    return "args0"

def myargs1(a):
    return "args1"

def myargs2(a, b):
    return "args2"

def myargs3(a, b, c):
    return "args3"

def myargs4(a, b, c, d):
    return "args4"

registry = ClassRegistry()
registry.register(args0, (), myargs0)
registry.register(args1, (Foo,), myargs1)
registry.register(args2, (Foo, Foo), myargs2)
registry.register(args3, (Foo, Foo, Foo), myargs3)
registry.register(args4, (Foo, Foo, Foo, Foo), myargs4)

lookup = Lookup(CachingClassLookup(registry))


def docall0():
    args0(lookup=lookup)

def docall1():
    args1(Foo(), lookup=lookup)

def docall2():
    args2(Foo(), Foo(), lookup=lookup)

def docall3():
    args3(Foo(), Foo(), Foo(), lookup=lookup)

def docall4():
    args4(Foo(), Foo(), Foo(), Foo(), lookup=lookup)

print "0 args"
print timeit.timeit("docall0()", setup="from __main__ import docall0")

print "1 args"
print timeit.timeit("docall1()", setup="from __main__ import docall1")

print "2 args"
print timeit.timeit("docall2()", setup="from __main__ import docall2")

print "3 args"
print timeit.timeit("docall3()", setup="from __main__ import docall3")

print "4 args"
print timeit.timeit("docall4()", setup="from __main__ import docall4")
