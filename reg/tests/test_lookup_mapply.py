import pytest

from reg.mapply import lookup_mapply


def test_lookup_mapply_without_lookup_arg():
    def f(a):
        return a

    assert lookup_mapply(f, 'lookup', 1) == 1


def test_lookup_mapply_with_lookup_arg():
    def f(a, lookup):
        return a, lookup

    assert lookup_mapply(f, 'lookup', 1) == (1, 'lookup')


def test_lookup_mapply_defines_kw():
    def f(a, **kw):
        return a, kw

    assert lookup_mapply(f, 'lookup', 1) == (
        1, {})


def test_lookup_mapply_uses_kw_without_lookup_arg():
    def f(a):
        return a

    assert lookup_mapply(f, 'lookup', a=1) == 1


def test_lookup_mapply_uses_kw_with_lookup_arg():
    def f(a, lookup):
        return a, lookup

    assert lookup_mapply(f, 'lookup', a=1) == (1, 'lookup')


def test_lookup_mapply_with_bound_method():
    class Foo(object):
        def f(self, a, lookup):
            return a, lookup

    assert lookup_mapply(Foo().f, 'lookup', 1) == (1, 'lookup')


def test_lookup_mapply_with_bound_method_old_style_class():
    class Foo:
        def f(self, a, lookup):
            return a, lookup

    assert lookup_mapply(Foo().f, 'lookup', 1) == (1, 'lookup')


def test_lookup_mapply_with_instance():
    class Callable(object):
        def __call__(self, a, lookup):
            return a, lookup

    assert lookup_mapply(Callable(), 'lookup', 1) == (1, 'lookup')


def test_lookup_mapply_with_instance_old_style_class():
    class Callable:
        def __call__(self, a, lookup):
            return a, lookup

    assert lookup_mapply(Callable(), 'lookup', 1) == (1, 'lookup')


def test_lookup_mapply_with_class():
    class Callable(object):
        def __init__(self, a, lookup):
            self.a = a
            self.lookup = lookup

    obj = lookup_mapply(Callable, 'lookup', 1)
    assert obj.a == 1
    assert obj.lookup == 'lookup'


def test_lookup_mapply_with_class_without_init():
    class Callable(object):
        pass

    obj = lookup_mapply(Callable, 'lookup')
    assert isinstance(obj, Callable)


def test_lookup_mapply_with_old_style_class():
    class Callable:
        def __init__(self, a, lookup):
            self.a = a
            self.lookup = lookup

    obj = lookup_mapply(Callable, 'lookup', 1)
    assert obj.a == 1
    assert obj.lookup == 'lookup'


def test_lookup_mapply_with_old_style_class_without_init():
    class Callable:
        pass

    with pytest.raises(TypeError):
        lookup_mapply(Callable, 'lookup')


def test_lookup_mapply_with_type():
    obj = lookup_mapply(int, 'lookup', '1')
    assert obj == 1


def test_lookup_mapply_instance_without_call():
    class Callable(object):
        pass

    with pytest.raises(TypeError):
        lookup_mapply(Callable(), 'lookup')


def test_lookup_mapply_old_style_instance_without_call():
    class Callable:
        pass

    with pytest.raises(AttributeError):
        lookup_mapply(Callable(), 'lookup')


def test_lookup_mapply_with_extension_function():
    # use dir which is implemented in C
    with pytest.raises(TypeError):
        lookup_mapply(dir, 'lookup')
