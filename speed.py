from timeit import timeit
from reg.fastmapply import lookup_mapply as c_lookup_mapply
from reg.fastmapply import mapply as c_mapply
from reg.mapply import py_lookup_mapply, py_mapply


class Foo(object):
    def __init__(self, a):
        self.a = a


class FooLookup(object):
    def __init__(self, a, lookup):
        self.a = a


def foo(a):
    return a


def foo_lookup(a, lookup):
    return a


class Bar(object):
    def __call__(self, a):
        return a


class BarLookup(object):
    def __call__(self, a, lookup):
        return a


def c_generic():
    c_mapply(foo, 1, lookup='lookup')


def c_specialized():
    c_lookup_mapply(foo, 'lookup', 1)


def py():
    py_lookup_mapply(foo, 'lookup', 1)


def direct():
    foo(1)


def main():
    print "Python version:"
    print timeit(py)

    print "C version generic:"
    print timeit(c_generic)

    print "C version specialized:"
    print timeit(c_specialized)

    print "Direct call:"
    print timeit(direct)

if __name__ == '__main__':
    main()
