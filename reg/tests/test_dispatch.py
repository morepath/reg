import py.test

from reg.interface import Interface, abstractmethod, NoImplicitLookupError
from reg.registry import Registry
from reg.interfaces import ComponentLookupError
from reg.dispatch import dispatch

class IAlpha(Interface):
    pass


class Alpha(IAlpha):
    pass


class IBeta(Interface):
    pass


class Beta(IBeta):
    pass


def test_call():
    @dispatch
    def foo(obj):
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

    registry.register(foo, (Bar,), Foo)

    bar = Bar()
    assert foo(bar, lookup=registry).foo() == "Foo called: bar's method"


def test_component():
    @dispatch
    def foo():
        pass

    registry = Registry()

    registry.register(foo, (), "test component")

    assert foo.component(lookup=registry) == 'test component'


def test_all():
    class Base(object):
        pass

    class Sub(Base):
        pass

    @dispatch
    def target(obj):
        pass
    
    registry = Registry()
    registry.register(target, (Sub,), 'registered for sub')
    registry.register(target, (Base,), 'registered for base')

    base = Base()
    sub = Sub()

    assert list(registry.all(target, [sub])) == [
        'registered for sub', 'registered for base']
    assert list(registry.all(target, [base])) == [
        'registered for base'
        ]
    assert list(target.all(sub, lookup=registry)) == [
        'registered for sub',
        'registered for base']
    assert list(target.all(base, lookup=registry)) == [
        'registered for base']


def test_component_no_source():
    reg = Registry()
    foo = object()
    @dispatch
    def target():
        pass
    reg.register(target, (), foo)
    assert reg.component(target, []) is foo
    assert target.component(lookup=reg) is foo


def test_component_one_source():
    reg = Registry()
    foo = object()
    @dispatch
    def target():
        pass
    reg.register(target, [Alpha], foo)

    alpha = Alpha()
    assert reg.component(target, [alpha]) is foo
    assert target.component(alpha, lookup=reg) is foo

    
def test_component_two_sources():
    reg = Registry()
    foo = object()
    @dispatch
    def target():
        pass
    reg.register(target, (IAlpha, IBeta), foo)
    alpha = Alpha()
    beta = Beta()
    assert reg.component(target, [alpha, beta]) is foo
    assert target.component(alpha, beta, lookup=reg) is foo


def test_component_inheritance():
    reg = Registry()
    foo = object()

    class Gamma(object):
        pass

    class Delta(Gamma):
        pass

    @dispatch
    def target():
        pass
    
    reg.register(target, [Gamma], foo)

    delta = Delta()

    assert reg.component(target, [delta]) is foo
    assert target.component(delta, lookup=reg) is foo


def test_component_not_found():
    reg = Registry()

    @dispatch
    def target(obj):
        pass
    
    with py.test.raises(ComponentLookupError):
        reg.component(target, []) is None
    assert reg.component(target, [], 'default') == 'default'

    alpha = Alpha()
    with py.test.raises(ComponentLookupError):
        assert reg.component(target, [alpha])
    assert reg.component(target, [], 'default') == 'default'

    assert target.component(alpha, lookup=reg, default='default') == 'default'
    with py.test.raises(ComponentLookupError):
        target.component(alpha, lookup=reg)


# def test_component_to_itself():
#     reg = Registry()
#     alpha = Alpha()

#     foo = object()

#     reg.register(IAlpha, [IAlpha], foo)

#     assert reg.component(IAlpha, [alpha]) is foo
#     assert IAlpha.component(alpha, lookup=reg) is foo


def test_adapter_no_source():
    reg = Registry()

    foo = object()

    @dispatch
    def target():
        pass
    
    def factory():
        return foo

    reg.register(target, (), factory)

    assert reg.adapt(target, []) is foo
    assert target(lookup=reg) is foo


def test_adapter_one_source():
    reg = Registry()

    @dispatch
    def target(obj):
        pass
    
    class Adapted(object):
        def __init__(self, context):
            self.context = context

        def foo(self):
            pass

    reg.register(target, [IAlpha], Adapted)

    alpha = Alpha()
    adapted = reg.adapt(target, [alpha])
    assert isinstance(adapted, Adapted)
    assert adapted.context is alpha
    adapted = target(alpha, lookup=reg)
    assert isinstance(adapted, Adapted)
    assert adapted.context is alpha


# def test_adapter_to_itself():
#     reg = Registry()

#     alpha = Alpha()

#     class Adapter(IAlpha):
#         def __init__(self, context):
#             self.context = context

#     # behavior without any registration; we get the object back
#     assert reg.adapt(IAlpha, [alpha]) is alpha
#     assert IAlpha.adapt(alpha, lookup=reg) is alpha
#     # it works even without registry (even implicitly registered!)
#     assert IAlpha.adapt(alpha) is alpha

#     # behavior is the same with registration
#     reg.register(IAlpha, [IAlpha], Adapter)
#     assert reg.adapt(IAlpha, [alpha]) is alpha
#     assert IAlpha.adapt(alpha, lookup=reg) is alpha
#     assert IAlpha.adapt(alpha) is alpha


def test_adapter_two_sources():
    reg = Registry()

    @dispatch
    def target(a, b):
        pass
    
    class Adapted(object):
        def __init__(self, alpha, beta):
            self.alpha = alpha
            self.beta = beta

        def foo(self):
            pass

    reg.register(target, [IAlpha, IBeta], Adapted)

    alpha = Alpha()
    beta = Beta()
    adapted = reg.adapt(target, [alpha, beta])

    assert isinstance(adapted, Adapted)
    assert adapted.alpha is alpha
    assert adapted.beta is beta

    adapted = target(alpha, beta, lookup=reg)
    assert isinstance(adapted, Adapted)
    assert adapted.alpha is alpha
    assert adapted.beta is beta


def test_default():
    reg = Registry()

    @dispatch
    def target():
        pass
    
    assert target.component(lookup=reg, default='blah') == 'blah'
    assert target(lookup=reg, default='blah') == 'blah'

    
def test_non_adapter_called():
    reg = Registry()
    foo = object()
    @dispatch
    def target(obj):
        pass
    
    reg.register(target, [Alpha], foo)
    alpha = Alpha()

    with py.test.raises(TypeError):
        target(alpha, lookup=reg)


def test_adapter_with_wrong_args():
    @dispatch
    def target(obj):
        pass
    
    class Adapter(object):
        # takes no args
        def __init__(self):
            pass
    reg = Registry()
    reg.register(target, [Alpha], Adapter)
    alpha = Alpha()

    with py.test.raises(TypeError) as e:
        target(alpha, lookup=reg)

    assert str(e.value) == ("__init__() takes exactly 1 argument (2 given)")


def test_adapter_returns_none():
    @dispatch
    def target(obj):
        pass
    
    def adapt(obj):
        return None
    reg = Registry()
    reg.register(target, [Alpha], adapt)
    alpha = Alpha()
    with py.test.raises(ComponentLookupError):
        target(alpha, lookup=reg)
    assert target(alpha, lookup=reg, default='default') == 'default'


# XXX review this; pep 443 supports extra kw arguments passed through
# to func
def test_extra_kw():
    @dispatch
    def target(obj):
        pass
    
    reg = Registry()
    foo = object()

    reg.register(target, [Alpha], foo)
    alpha = Alpha()

    with py.test.raises(TypeError) as e:
        target.component(alpha, lookup=reg, extra="illegal")
    assert str(e.value) == "component() got an unexpected keyword argument 'extra'"


def test_no_implicit():
    @dispatch
    def target(obj):
        pass
    
    alpha = Alpha()
    with py.test.raises(NoImplicitLookupError):
        target.component(alpha)
