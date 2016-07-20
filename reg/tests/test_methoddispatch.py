import pytest
from reg.dispatch import dispatch_method, dispatch_classmethod
from reg.registry import Registry
from reg.error import RegistrationError


def test_dispatch():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

    def for_bar(self, obj):
        return "we got bar"

    def for_qux(self, obj):
        return "we got qux"

    class Bar(object):
        pass

    class Qux(object):
        pass

    registry = Registry()
    registry.register_method(Example.foo, for_bar, obj=Bar)
    registry.register_method(Example.foo, for_qux, obj=Qux)

    lookup = registry.lookup()

    example = Example(lookup)

    assert example.foo(Bar()) == "we got bar"

    assert example.foo(Qux()) == "we got qux"

    assert example.foo(None) == "default"


def test_dispatch_name():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

        @dispatch_classmethod()
        def bar(cls):
            pass

    assert repr(Example.foo).startswith('<dispatch function Example.foo at')

    example = Example(Registry().lookup())

    assert repr(example.foo).startswith(
        '<bound dispatch method Example.foo of <')

    assert repr(Example.bar).startswith('<bound dispatch method type.bar of')

    assert repr(example.bar).startswith('<bound dispatch method type.bar of')


def test_dispatch_call_too_early():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

        @dispatch_method()
        def bar(self):
            return "default"

    with pytest.raises(TypeError):
        Example.foo(None)

    with pytest.raises(TypeError):
        Example.bar()


def test_dispatch_no_self():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

    def for_bar(obj):
        return "we got bar"

    def for_qux(obj):
        return "we got qux"

    class Bar(object):
        pass

    class Qux(object):
        pass

    registry = Registry()
    registry.register_function(Example.foo, for_bar, obj=Bar)
    registry.register_function(Example.foo, for_qux, obj=Qux)

    lookup = registry.lookup()

    example = Example(lookup)

    assert example.foo(Bar()) == "we got bar"

    assert example.foo(Qux()) == "we got qux"

    assert example.foo(None) == "default"


def test_dispatch_function_wrong_arguments():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

    def for_bar():
        return "we got bar"

    def for_qux(obj, another):
        return "we got qux"

    class Bar(object):
        pass

    registry = Registry()
    with pytest.raises(RegistrationError):
        registry.register_function(Example.foo, for_bar, obj=Bar)
    with pytest.raises(RegistrationError):
        registry.register_function(Example.foo, for_qux, obj=Bar)


def test_classdispatch():
    registry = Registry()

    class Example(object):
        lookup = registry.lookup()

        @dispatch_classmethod('obj')
        def foo(cls, obj):
            return "default"

    def for_bar(cls, obj):
        return "we got bar"

    def for_qux(cls, obj):
        return "we got qux"

    class Bar(object):
        pass

    class Qux(object):
        pass

    registry.register_method(Example.foo, for_bar, obj=Bar)
    registry.register_method(Example.foo, for_qux, obj=Qux)

    assert Example.foo(Bar()) == "we got bar"

    assert Example.foo(Qux()) == "we got qux"

    assert Example.foo(None) == "default"


def test_dispatch_identity_method_on_class():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

    assert Example.foo is Example.foo


def test_dispatch_identity_classmethod_on_class():
    class Example(object):
        lookup = Registry().lookup()

        @dispatch_classmethod('obj')
        def foo(cls, obj):
            return "default"

    assert Example.foo is Example.foo


def test_dispatch_identity_method_on_instance():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @dispatch_method('obj')
        def foo(self, obj):
            return "default"

    registry = Registry()
    example = Example(registry.lookup())

    assert example.foo is example.foo


def test_dispatch_identity_classmethod_on_instance():
    class Example(object):
        lookup = Registry().lookup()

        @dispatch_classmethod('obj')
        def foo(self, obj):
            return "default"

    example = Example()

    assert example.foo is example.foo
