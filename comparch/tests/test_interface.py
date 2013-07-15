from comparch.interface import Interface
from comparch.registry import Registry

def test_interface_component():
    class IFoo(Interface):
        pass

    registry = Registry()

    registry.register(IFoo, (), None, "test component")

    assert IFoo.component(lookup=registry)  == 'test component' 

def test_interface_adapt():
    class IFoo(Interface):
        pass

    class Foo(object):
        def __init__(self, bar):
            self.bar = bar

        def foo(self):
            return "Foo called: " + self.bar.bar()

    class Bar(object):
        def bar(self):
            return "bar's method"

    registry = Registry()

    registry.register(IFoo, (Bar,), None, Foo)

    bar = Bar()
    assert IFoo.adapt(bar, lookup=registry).foo() == "Foo called: bar's method"
