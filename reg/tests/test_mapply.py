import pytest
from reg.mapply import mapply

def test_mapply():
    def foo(a):
        return "foo with %s" % a

    assert mapply(foo, a=1) == "foo with 1"
    assert mapply(foo, a=1, b=2) == "foo with 1"


def test_mapply_fail():
    def foo(a):
        return "foo with %s" % a

    with pytest.raises(TypeError):
        mapply(foo, b=2)


def test_mapply_args():
    def foo(a):
        return "foo with %s" % a

    assert mapply(foo, 1) == 'foo with 1'


def test_mapply_with_method():
    class Foo(object):
        def method(self, a):
            return "method with %s" % a

    f = Foo()
    assert mapply(f.method, a=1) == "method with 1"
    assert mapply(f.method, a=1, b=2) == "method with 1"


def test_mapply_with_constructor():
    class Foo(object):
        def __init__(self, a):
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1

def test_mapply_with_old_style_class():
    class Foo:
        def __init__(self, a):
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_callable_object():
    class Foo(object):
        def __call__(self, a):
            return "called with %s" % a

    f = Foo()
    assert mapply(f, a=1) == 'called with 1'
    assert mapply(f, a=1, b=1) == 'called with 1'


def test_mapply_non_function():
    a = 1

    with pytest.raises(TypeError):
        assert mapply(a, a=1)
