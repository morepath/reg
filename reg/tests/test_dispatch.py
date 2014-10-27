from __future__ import unicode_literals
import pytest

from reg.implicit import NoImplicitLookupError
from reg.registry import KeyRegistry as Registry
from reg.predicate import (class_predicate, key_predicate,
                           match_instance, match_key)
from reg.dispatch import dispatch
from reg.error import RegError, KeyExtractorError


class IAlpha(object):
    pass


class Alpha(IAlpha):
    pass


class IBeta(object):
    pass


class Beta(IBeta):
    pass


def test_dispatch_argname():
    @dispatch('obj')
    def foo(obj):
        pass

    def for_bar(obj):
        return obj.method()

    def for_qux(obj):
        return obj.method()

    class Bar(object):
        def method(self):
            return "bar's method"

    class Qux(object):
        def method(self):
            return "qux's method"

    registry = Registry()

    registry.register_dispatch(foo)

    registry.register_dispatch_value(foo, (Bar,), for_bar)
    registry.register_dispatch_value(foo, (Qux,), for_qux)

    lookup = registry.lookup()
    assert foo(Bar(), lookup=lookup) == "bar's method"
    assert foo(Qux(), lookup=lookup) == "qux's method"


def test_dispatch_match_instance():
    @dispatch(match_instance(lambda obj: obj))
    def foo(obj):
        pass

    def for_bar(obj):
        return obj.method()

    def for_qux(obj):
        return obj.method()

    class Bar(object):
        def method(self):
            return "bar's method"

    class Qux(object):
        def method(self):
            return "qux's method"

    registry = Registry()

    registry.register_dispatch(foo)

    registry.register_dispatch_value(foo, (Bar,), for_bar)
    registry.register_dispatch_value(foo, (Qux,), for_qux)

    lookup = registry.lookup()
    assert foo(Bar(), lookup=lookup) == "bar's method"
    assert foo(Qux(), lookup=lookup) == "qux's method"


def test_dispatch_no_arguments():
    @dispatch()
    def foo():
        pass

    registry = Registry()

    registry.register_dispatch(foo)

    def special_foo():
        return "special"

    registry.register_dispatch_value(foo, (), special_foo)

    lookup = registry.lookup()
    assert foo.component(lookup=lookup) is special_foo
    assert list(foo.all(lookup=lookup)) == [special_foo]
    assert foo(lookup=lookup) == 'special'


def test_all():
    class Base(object):
        pass

    class Sub(Base):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    registry = Registry()
    registry.register_dispatch(target)
    registry.register_value(target.wrapped_func, (Sub,), 'registered for sub')
    registry.register_value(target.wrapped_func, (Base,), 'registered for base')

    base = Base()
    sub = Sub()

    lookup = registry.lookup()
    assert list(target.all(sub, lookup=lookup)) == [
        'registered for sub',
        'registered for base']
    assert list(target.all(base, lookup=lookup)) == [
        'registered for base']


def test_component_no_source():
    reg = Registry()
    foo = object()

    @dispatch()
    def target():
        pass

    reg.register_dispatch(target)
    reg.register_value(target.wrapped_func, (), foo)
    assert target.component(lookup=reg.lookup()) is foo


def test_component_one_source():
    reg = Registry()
    foo = object()

    @dispatch('obj')
    def target(obj):
        pass

    reg.register_dispatch(target)
    reg.register_value(target.wrapped_func, (Alpha,), foo)

    alpha = Alpha()
    assert target.component(alpha, lookup=reg.lookup()) is foo


def test_component_two_sources():
    reg = Registry()
    foo = object()

    @dispatch('a', 'b')
    def target(a, b):
        pass

    reg.register_dispatch(target)
    reg.register_value(target.wrapped_func, (IAlpha, IBeta), foo)

    alpha = Alpha()
    beta = Beta()
    assert target.component(alpha, beta, lookup=reg.lookup()) is foo


def test_component_inheritance():
    reg = Registry()
    foo = object()

    class Gamma(object):
        pass

    class Delta(Gamma):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    reg.register_dispatch(target)
    reg.register_value(target.wrapped_func, (Gamma,), foo)

    delta = Delta()

    assert target.component(delta, lookup=reg.lookup()) is foo


def test_component_inheritance_old_style_class():
    reg = Registry()
    foo = object()

    class Gamma:
        pass

    class Delta(Gamma):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    reg.register_dispatch(target)
    reg.register_value(target.wrapped_func, (Gamma,), foo)

    gamma = Gamma()
    delta = Delta()

    lookup = reg.lookup()
    assert target.component(gamma, lookup=lookup) is foo

    # inheritance case
    assert target.component(delta, lookup=lookup) is foo


def test_call_no_source():
    reg = Registry()

    foo = object()

    @dispatch()
    def target():
        pass

    def factory():
        return foo

    reg.register_dispatch(target)
    reg.register_value(target.wrapped_func, (), factory)

    assert target(lookup=reg.lookup()) is foo


def test_call_one_source():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        return "foo"

    def bar(obj):
        return "bar"

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (IAlpha,), foo)
    reg.register_dispatch_value(target, (IBeta,), bar)

    lookup = reg.lookup()
    assert target(Alpha(), lookup=lookup) == 'foo'
    assert target(Beta(), lookup=lookup) == 'bar'


def test_call_two_sources():
    reg = Registry()

    @dispatch('a', 'b')
    def target(a, b):
        pass

    def foo(a, b):
        return "foo"

    def bar(a, b):
        return "bar"

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (IAlpha, IBeta), foo)
    reg.register_dispatch_value(target, (IBeta, IAlpha), bar)
    alpha = Alpha()
    beta = Beta()

    lookup = reg.lookup()

    assert target(alpha, beta, lookup=lookup) == 'foo'
    assert target(beta, alpha, lookup=lookup) == 'bar'


def test_component_not_found_no_sources():
    reg = Registry()

    @dispatch()
    def target():
        pass

    reg.register_dispatch(target)

    lookup = reg.lookup()
    assert target.component(lookup=lookup) is None


def test_call_not_found_no_sources():
    reg = Registry()

    @dispatch()
    def target():
        return "default"

    reg.register_dispatch(target)

    lookup = reg.lookup()
    assert target(lookup=lookup) == "default"


def test_component_not_found_one_source():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    reg.register_dispatch(target)

    lookup = reg.lookup()

    assert target.component('dummy', lookup=lookup) is None


def test_call_not_found_one_source():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        return "default: %s" % obj

    reg.register_dispatch(target)

    lookup = reg.lookup()

    assert target('dummy', lookup=lookup) == 'default: dummy'


def test_component_not_found_two_sources():
    reg = Registry()

    @dispatch('a', 'b')
    def target(a, b):
        pass

    reg.register_dispatch(target)

    lookup = reg.lookup()

    assert target.component('dummy', 'dummy', lookup=lookup) is None


def test_call_not_found_two_sources():
    reg = Registry()

    @dispatch('a', 'b')
    def target(a, b):
        return "a: %s b: %s" % (a, b)

    reg.register_dispatch(target)

    lookup = reg.lookup()

    assert target('dummy1', 'dummy2', lookup=lookup) == "a: dummy1 b: dummy2"


def test_wrong_callable_registered():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    def callable(a, b):
        pass

    reg.register_dispatch(target)
    with pytest.raises(RegError):
        reg.register_dispatch_value(target, (Alpha,), callable)


def test_non_callable_registered():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    non_callable = None

    reg.register_dispatch(target)
    with pytest.raises(RegError):
        reg.register_dispatch_value(target, (Alpha,), non_callable)



def test_call_with_no_args_while_arg_expected():
    @dispatch('obj')
    def target(obj):
        pass

    def specific(obj):
        return "specific"

    reg = Registry()
    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (Alpha,), specific)

    lookup = reg.lookup()

    # we are not allowed to call target without arguments
    with pytest.raises(TypeError):
        target(lookup=lookup)

    with pytest.raises(KeyExtractorError):
        target.component(lookup=lookup)


def test_call_with_wrong_args():
    @dispatch('obj')
    def target(obj):
        pass

    def specific(obj):
        return "specific"

    reg = Registry()
    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (Alpha,), specific)

    lookup = reg.lookup()

    # we are not allowed to call target without arguments
    with pytest.raises(TypeError):
        target(wrong=1, lookup=lookup)

    with pytest.raises(KeyExtractorError):
        target.component(wrong=1, lookup=lookup)


def test_extra_arg_for_call():
    @dispatch('obj')
    def target(obj, extra):
        return "General: %s" % extra

    reg = Registry()

    def specific(obj, extra):
        return "Specific: %s" % extra

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (Alpha,), specific)

    alpha = Alpha()
    beta = Beta()

    lookup = reg.lookup()

    assert target(alpha, lookup=lookup, extra="allowed") == 'Specific: allowed'
    assert target(beta, lookup=lookup, extra="allowed") == 'General: allowed'
    assert target(alpha, 'allowed', lookup=lookup) == 'Specific: allowed'
    assert target(beta, 'allowed', lookup=lookup) == 'General: allowed'


def test_no_implicit():
    @dispatch('obj')
    def target(obj):
        pass

    alpha = Alpha()
    with pytest.raises(NoImplicitLookupError):
        target.component(alpha)


def test_fallback():
    @dispatch('obj')
    def target(obj):
        return 'fallback'

    reg = Registry()

    def specific_target(obj):
        return 'specific'

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (Alpha,), specific_target)

    beta = Beta()
    assert target(beta, lookup=reg.lookup()) == 'fallback'


def test_calling_twice():
    @dispatch('obj')
    def target(obj):
        return 'fallback'

    reg = Registry()

    def a(obj):
        return 'a'

    def b(obj):
        return 'b'

    reg.register_dispatch(target)

    reg.register_dispatch_value(target, (Alpha,), a)
    reg.register_dispatch_value(target, (Beta,), b)

    lookup = reg.lookup()

    assert target(Alpha(), lookup=lookup) == 'a'
    assert target(Beta(), lookup=lookup) == 'b'


def test_lookup_passed_along():
    @dispatch('obj')
    def g1(obj):
        pass

    @dispatch('obj')
    def g2(obj):
        pass

    reg = Registry()

    def g1_impl(obj, lookup):
        return g2(obj, lookup=lookup)

    def g2_impl(obj):
        return "g2"

    reg.register_dispatch(g1)
    reg.register_dispatch(g2)

    reg.register_dispatch_value(g1, (Alpha,), g1_impl)
    reg.register_dispatch_value(g2, (Alpha,), g2_impl)

    assert g1(Alpha(), lookup=reg.lookup()) == 'g2'


def test_different_defaults_in_specific_non_dispatch_arg():
    @dispatch('obj')
    def target(obj, blah='default'):
        return 'fallback: %s' % blah

    reg = Registry()

    def a(obj, blah='default 2'):
        return 'a: %s' % blah

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, (Alpha,), a)

    lookup = reg.lookup()

    assert target(Alpha(), lookup=lookup) == 'a: default 2'


def test_different_defaults_in_specific_dispatch_arg():
    @dispatch(match_key(lambda key: key))
    def target(key='default'):
        return 'fallback: %s' % key

    reg = Registry()

    def a(key='default 2'):
        return 'a: %s' % key

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, ('foo',), a)

    lookup = reg.lookup()

    assert target('foo', lookup=lookup) == 'a: foo'
    assert target('bar', lookup=lookup) == 'fallback: bar'
    assert target(lookup=lookup) == 'fallback: default'


def test_different_defaults_in_specific_dispatch_arg_causes_dispatch():
    @dispatch(match_key(lambda key: key))
    def target(key='foo'):
        return 'fallback: %s' % key

    reg = Registry()

    def a(key='default 2'):
        return 'a: %s' % key

    reg.register_dispatch(target)
    reg.register_dispatch_value(target, ('foo',), a)

    lookup = reg.lookup()

    assert target('foo', lookup=lookup) == 'a: foo'
    assert target('bar', lookup=lookup) == 'fallback: bar'
    assert target(lookup=lookup) == 'a: default 2'


def test_lookup_passed_along_fallback():
    @dispatch()
    def a(lookup):
        return "fallback"

    reg = Registry()
    reg.register_dispatch(a)

    assert a(lookup=reg.lookup()) == 'fallback'
