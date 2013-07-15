import py.test

from comparch.interface import Interface, abstractmethod, NoImplicitLookupError
from comparch.registry import Registry
from comparch.interfaces import ComponentLookupError

class IAlpha(Interface):
    pass

class Alpha(IAlpha):
    pass

class IBeta(Interface):
    pass

class Beta(IBeta):
    pass

class ITarget(Interface):
    @abstractmethod
    def foo(self):
        """A target method"""

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
    
def test_component_no_source():
    reg = Registry()
    foo = object()
    reg.register(ITarget, (), None, foo)
    assert reg.component(ITarget, [], None) is foo
    assert ITarget.component(lookup=reg) is foo

def test_component_two_sources():
    reg = Registry()
    foo = object()
    reg.register(ITarget, (IAlpha, IBeta), None, foo)
    alpha = Alpha()
    beta = Beta()
    assert reg.component(ITarget, [alpha, beta], None) is foo
    assert ITarget.component(alpha, beta, lookup=reg) is foo
    
def test_component_class_based_registration():
    reg = Registry()
    foo = object()
    reg.register(ITarget, (Alpha,), None, foo)

    alpha = Alpha()
    assert reg.component(ITarget, [alpha], None) is foo
    assert ITarget.component(alpha, lookup=reg) is foo
    
def test_component_inheritance():
    reg = Registry()
    foo = object()

    class Gamma(object):
        pass

    class Delta(Gamma):
        pass
    
    reg.register(ITarget, [Gamma], None, foo)

    delta = Delta()
    
    assert reg.component(ITarget, [delta], None) is foo
    assert ITarget.component(delta, lookup=reg) is foo
    
def test_component_not_found():
    reg = Registry()

    with py.test.raises(ComponentLookupError):
        reg.component(ITarget, [], None) is None
    assert reg.component(ITarget, [], None, 'default') == 'default'
               
    alpha = Alpha()
    with py.test.raises(ComponentLookupError):
        assert reg.component(ITarget, [alpha], '')
    assert reg.component(ITarget, [], None, 'default') == 'default'
    
    assert ITarget.component(alpha, lookup=reg, default='default') == 'default'
    with py.test.raises(ComponentLookupError):
        ITarget.component(alpha, lookup=reg)

def test_component_to_itself():
    reg = Registry()
    alpha = Alpha()

    foo = object()
    
    reg.register(IAlpha, [IAlpha], None, foo)

    assert reg.component(IAlpha, [alpha], None) is foo
    assert IAlpha.component(alpha, lookup=reg) is foo

def test_adapter_no_source():
    reg = Registry()

    foo = object()
    def factory():
        return foo
    
    reg.register(ITarget, (), None, factory)

    assert reg.adapt(ITarget, [], None) is foo
    assert ITarget.adapt(lookup=reg) is foo
    
def test_adapter_one_source():
    reg = Registry()

    class Adapted(ITarget):
        def __init__(self, context):
            self.context = context

        def foo(self):
            pass
        
    reg.register(ITarget, [IAlpha], None, Adapted)
    
    alpha = Alpha()
    adapted = reg.adapt(ITarget, [alpha], None)
    assert isinstance(adapted, Adapted)
    assert adapted.context is alpha
    adapted = ITarget.adapt(alpha, lookup=reg)
    assert isinstance(adapted, Adapted)
    assert adapted.context is alpha
    
def test_adapter_to_itself():
    reg = Registry()

    alpha = Alpha()

    class Adapter(IAlpha):
        def __init__(self, context):
            self.context = context

    # behavior without any registration; we get the object back
    assert reg.adapt(IAlpha, [alpha], None) is alpha
    assert IAlpha.adapt(alpha, lookup=reg) is alpha
    # it works even without registry (even implicitly registered!)
    assert IAlpha.adapt(alpha) is alpha
    
    # behavior is the same with registration
    reg.register(IAlpha, [IAlpha], None, Adapter)
    assert reg.adapt(IAlpha, [alpha], None) is alpha
    assert IAlpha.adapt(alpha, lookup=reg) is alpha
    assert IAlpha.adapt(alpha) is alpha
    
def test_adapter_two_sources():
    reg = Registry()

    class Adapted(ITarget):
        def __init__(self, alpha, beta):
            self.alpha = alpha
            self.beta = beta

        def foo(self):
            pass
        
    reg.register(ITarget, [IAlpha, IBeta], None, Adapted)

    alpha = Alpha()
    beta = Beta()
    adapted = reg.adapt(ITarget, [alpha, beta], None)

    assert isinstance(adapted, Adapted)
    assert adapted.alpha is alpha
    assert adapted.beta is beta

    adapted = ITarget.adapt(alpha, beta, lookup=reg)
    assert isinstance(adapted, Adapted)
    assert adapted.alpha is alpha
    assert adapted.beta is beta
    
def test_default():
    reg = Registry()

    assert ITarget.component(lookup=reg, default='blah') == 'blah'

def test_discriminator():
    reg = Registry()
    foo = object()
    reg.register(ITarget, [Alpha], (), foo)
    alpha = Alpha()
    assert ITarget.component(alpha, lookup=reg, discriminator=()) is foo
    assert ITarget.component(alpha, lookup=reg, default='default') is 'default'

def test_name():
    reg = Registry()
    foo = object()
    reg.register(ITarget, [Alpha],  'x', foo)
    alpha = Alpha()
    assert ITarget.component(alpha, lookup=reg, name='x') is foo
    assert ITarget.component(alpha, lookup=reg, default='default') is 'default'
    None

def test_non_adapter_looked_up_as_adapter():
    reg = Registry()
    foo = object()
    reg.register(ITarget, [Alpha], None, foo)
    alpha = Alpha()
    
    with py.test.raises(TypeError):
        ITarget.adapt(alpha, lookup=reg)
    
def test_adapter_with_wrong_args():
    class Adapter(object):
        # takes no args
        def __init__(self):
            pass
    reg = Registry()
    reg.register(ITarget, [Alpha], None, Adapter)
    alpha = Alpha()
    
    with py.test.raises(TypeError) as e:
        ITarget.adapt(alpha, lookup=reg)

    assert str(e.value) == ("__init__() takes exactly 1 argument (2 given) "
                            "(<class 'comparch.tests.test_interface.Adapter'>)")
    
def test_extra_kw():
    reg = Registry()
    foo = object()
    
    reg.register(ITarget, [Alpha], None, foo)
    alpha = Alpha()
    
    with py.test.raises(TypeError) as e:
        ITarget.component(alpha, lookup=reg, extra="illegal")
    assert str(e.value) == 'Illegal extra keyword arguments: extra'

def test_no_implicit():
    alpha = Alpha()
    with py.test.raises(NoImplicitLookupError):
        ITarget.component(alpha)
