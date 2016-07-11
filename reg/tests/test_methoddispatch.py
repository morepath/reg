from reg.dispatch import methoddispatch, classmethoddispatch
from reg.registry import Registry


def test_dispatch():
    class Example(object):
        def __init__(self, lookup):
            self.lookup = lookup

        @methoddispatch('obj')
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
    registry.register_function(Example.foo, for_bar, obj=Bar)
    registry.register_function(Example.foo, for_qux, obj=Qux)

    lookup = registry.lookup()

    example = Example(lookup)

    assert example.foo(Bar()) == "we got bar"

    assert example.foo(Qux()) == "we got qux"

    assert example.foo(None) == "default"


def test_classdispatch():
    registry = Registry()

    class Example(object):
        lookup = registry.lookup()

        @classmethoddispatch('obj')
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

    registry.register_function(Example.foo, for_bar, obj=Bar)
    registry.register_function(Example.foo, for_qux, obj=Qux)

    assert Example.foo(Bar()) == "we got bar"

    assert Example.foo(Qux()) == "we got qux"

    assert Example.foo(None) == "default"

# reprs of the various objects
