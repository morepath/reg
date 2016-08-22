import timeit

from reg import dispatch
from reg import CachingKeyLookup


def get_key_lookup(r):
    return CachingKeyLookup(r, component_cache_size=5000,
                            all_cache_size=5000, fallback_cache_size=5000)


@dispatch(get_key_lookup=get_key_lookup)
def args0():
    raise NotImplementedError()


@dispatch('a', get_key_lookup=get_key_lookup)
def args1(a):
    raise NotImplementedError()


@dispatch('a', 'b', get_key_lookup=get_key_lookup)
def args2(a, b):
    raise NotImplementedError()


@dispatch('a', 'b', 'c', get_key_lookup=get_key_lookup)
def args3(a, b, c):
    raise NotImplementedError()


@dispatch('a', 'b', 'c', 'd', get_key_lookup=get_key_lookup)
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

args0.register(myargs0)
args1.register(myargs1, a=Foo)
args2.register(myargs2, a=Foo, b=Foo)
args3.register(myargs3, a=Foo, b=Foo, c=Foo)
args4.register(myargs4, a=Foo, b=Foo, c=Foo, d=Foo)


def docall0():
    args0()


def docall1():
    args1(Foo())


def docall2():
    args2(Foo(), Foo())


def docall3():
    args3(Foo(), Foo(), Foo())


def docall4():
    args4(Foo(), Foo(), Foo(), Foo())


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
