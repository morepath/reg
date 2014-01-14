from __future__ import unicode_literals
from future.builtins import str
import pytest

from reg.implicit import NoImplicitLookupError
from reg.registry import Registry
from reg.lookup import ComponentLookupError
from reg.generic import generic


class IAlpha(object):
    pass


class Alpha(IAlpha):
    pass


class IBeta(object):
    pass


class Beta(IBeta):
    pass


def test_call():
    @generic
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
    @generic
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

    @generic
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

    @generic
    def target():
        pass

    reg.register(target, (), foo)
    assert reg.component(target, []) is foo
    assert target.component(lookup=reg) is foo


def test_component_one_source():
    reg = Registry()
    foo = object()

    @generic
    def target():
        pass

    reg.register(target, [Alpha], foo)

    alpha = Alpha()
    assert reg.component(target, [alpha]) is foo
    assert target.component(alpha, lookup=reg) is foo


def test_component_two_sources():
    reg = Registry()
    foo = object()

    @generic
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

    @generic
    def target():
        pass

    reg.register(target, [Gamma], foo)

    delta = Delta()

    assert reg.component(target, [delta]) is foo
    assert target.component(delta, lookup=reg) is foo


def test_component_not_found():
    reg = Registry()

    @generic
    def target(obj):
        pass

    with pytest.raises(ComponentLookupError):
        reg.component(target, []) is None
    assert reg.component(target, [], 'default') == 'default'

    alpha = Alpha()
    with pytest.raises(ComponentLookupError):
        assert reg.component(target, [alpha])
    assert reg.component(target, [], 'default') == 'default'

    assert target.component(alpha, lookup=reg, default='default') == 'default'
    with pytest.raises(ComponentLookupError):
        target.component(alpha, lookup=reg)


# def test_component_to_itself():
#     reg = Registry()
#     alpha = Alpha()

#     foo = object()

#     reg.register(IAlpha, [IAlpha], foo)

#     assert reg.component(IAlpha, [alpha]) is foo
#     assert IAlpha.component(alpha, lookup=reg) is foo


def test_call_no_source():
    reg = Registry()

    foo = object()

    @generic
    def target():
        pass

    def factory():
        return foo

    reg.register(target, (), factory)

    assert reg.call(target, []) is foo
    assert target(lookup=reg) is foo


def test_call_one_source():
    reg = Registry()

    @generic
    def target(obj):
        pass

    class Adapted(object):
        def __init__(self, context):
            self.context = context

        def foo(self):
            pass

    reg.register(target, [IAlpha], Adapted)

    alpha = Alpha()
    adapted = reg.call(target, [alpha])
    assert isinstance(adapted, Adapted)
    assert adapted.context is alpha
    adapted = target(alpha, lookup=reg)
    assert isinstance(adapted, Adapted)
    assert adapted.context is alpha


def test_call_two_sources():
    reg = Registry()

    @generic
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
    adapted = reg.call(target, [alpha, beta])

    assert isinstance(adapted, Adapted)
    assert adapted.alpha is alpha
    assert adapted.beta is beta

    adapted = target(alpha, beta, lookup=reg)
    assert isinstance(adapted, Adapted)
    assert adapted.alpha is alpha
    assert adapted.beta is beta


def test_default():
    reg = Registry()

    @generic
    def target():
        pass

    assert target.component(lookup=reg, default='blah') == 'blah'
    assert target(lookup=reg, default='blah') == 'blah'


def test_non_function_called():
    reg = Registry()
    foo = object()

    @generic
    def target(obj):
        pass

    reg.register(target, [Alpha], foo)
    alpha = Alpha()

    with pytest.raises(TypeError):
        target(alpha, lookup=reg)


def test_call_with_wrong_args():
    @generic
    def target(obj):
        pass

    class Adapter(object):
        # takes no args
        def __init__(self):
            pass
    reg = Registry()
    reg.register(target, [Alpha], Adapter)
    alpha = Alpha()

    with pytest.raises(TypeError):
        target(alpha, lookup=reg)


def test_func_returns_none():
    @generic
    def target(obj):
        raise NotImplementedError

    def adapt(obj):
        return None
    reg = Registry()
    reg.register(target, [Alpha], adapt)
    alpha = Alpha()
    assert target(alpha, lookup=reg) is None
    assert target(alpha, lookup=reg, default='default') == 'default'


def test_extra_kw_for_component():
    @generic
    def target(obj):
        pass

    reg = Registry()
    foo = object()

    reg.register(target, [Alpha], foo)
    alpha = Alpha()

    with pytest.raises(TypeError) as e:
        target.component(alpha, lookup=reg, extra="illegal")
    assert str(e.value) == ("component() got an unexpected keyword "
                            "argument 'extra'")


def test_extra_kw_for_call():
    @generic
    def target(obj, extra):
        return "General: %s" % extra

    reg = Registry()

    def specific(obj, extra):
        return "Specific: %s" % extra

    reg.register(target, [Alpha], specific)
    alpha = Alpha()
    beta = Beta()
    assert target(alpha, lookup=reg, extra="allowed") == 'Specific: allowed'
    assert target(beta, lookup=reg, extra="allowed") == 'General: allowed'
    assert target(alpha, lookup=reg, default='default',
                  extra='allowed') == 'Specific: allowed'
    assert target(beta, lookup=reg, default='default',
                  extra='allowed') == 'default'


def test_no_implicit():
    @generic
    def target(obj):
        pass

    alpha = Alpha()
    with pytest.raises(NoImplicitLookupError):
        target.component(alpha)


def test_fallback():
    @generic
    def target(obj):
        return 'fallback'

    reg = Registry()

    def specific_target(obj):
        return 'specific'

    reg.register(target, [Alpha], specific_target)
    beta = Beta()
    assert target(beta, lookup=reg) == 'fallback'


def test_calling_twice():
    @generic
    def target(obj):
        return 'fallback'

    reg = Registry()

    def a(obj):
        return 'a'

    def b(obj):
        return 'b'

    reg.register(target, [Alpha], a)
    reg.register(target, [Beta], b)

    assert target(Alpha(), lookup=reg) == 'a'
    assert target(Beta(), lookup=reg) == 'b'


def test_lookup_passed_along():
    @generic
    def g1(obj):
        pass

    @generic
    def g2(obj):
        pass

    reg = Registry()

    def g1_impl(obj, lookup):
        return g2(obj, lookup=lookup)

    def g2_impl(obj):
        return "g2"

    reg.register(g1, [Alpha], g1_impl)
    reg.register(g2, [Alpha], g2_impl)

    assert g1(Alpha(), lookup=reg) == 'g2'


def test_lookup_passed_along_fallback():
    @generic
    def a(lookup):
        return "fallback"

    reg = Registry()

    assert a(lookup=reg) == 'fallback'
