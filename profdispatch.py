from cProfile import run
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


def repeat_args4():
    for i in xrange(10000):
        args4(Foo(), Foo(), Foo(), Foo())


run("repeat_args4()", sort="tottime")

