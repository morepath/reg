from __future__ import unicode_literals
import pytest

from reg.error import NoImplicitLookupError
from reg.implicit import implicit
from reg.registry import Registry
from reg.predicate import (
    match_instance, match_key, match_class, key_predicate, NOT_FOUND)
from reg.dispatch import dispatch, dispatch_external_predicates
from reg.error import RegistrationError, KeyExtractorError


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

    registry.register_function(foo, for_bar, obj=Bar)
    registry.register_function(foo, for_qux, obj=Qux)

    lookup = registry.lookup()
    assert foo(Bar(), lookup=lookup) == "bar's method"
    assert foo(Qux(), lookup=lookup) == "qux's method"


def test_dispatch_match_instance():
    @dispatch(match_instance('obj', lambda obj: obj))
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

    registry.register_function(foo, for_bar, obj=Bar)
    registry.register_function(foo, for_qux, obj=Qux)

    lookup = registry.lookup()
    assert foo(Bar(), lookup=lookup) == "bar's method"
    assert foo(Qux(), lookup=lookup) == "qux's method"


def test_dispatch_no_arguments():
    @dispatch()
    def foo():
        pass

    registry = Registry()

    def special_foo():
        return "special"

    registry.register_function(foo, special_foo)

    lookup = registry.lookup()
    assert foo.component(lookup=lookup) is special_foo
    assert list(foo.all(lookup=lookup)) == [special_foo]
    assert foo(lookup=lookup) == 'special'
    assert foo.fallback(lookup=lookup) is None


def test_all():
    class Base(object):
        pass

    class Sub(Base):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    def registered_for_sub(obj):
        pass

    def registered_for_base(obj):
        pass

    registry = Registry()

    registry.register_function(target, registered_for_sub, obj=Sub)
    registry.register_function(target, registered_for_base, obj=Base)

    base = Base()
    sub = Sub()

    lookup = registry.lookup()
    assert list(target.all(sub, lookup=lookup)) == [
        registered_for_sub, registered_for_base]
    assert list(target.all(base, lookup=lookup)) == [
        registered_for_base]


def test_all_key_dict():
    class Base(object):
        pass

    class Sub(Base):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    def registered_for_sub(obj):
        pass

    def registered_for_base(obj):
        pass

    registry = Registry()

    registry.register_function(target, registered_for_sub, obj=Sub)
    registry.register_function(target, registered_for_base, obj=Base)

    lookup = registry.lookup()
    assert list(target.all_key_dict(obj=Sub, lookup=lookup)) == [
        registered_for_sub, registered_for_base]
    assert list(target.all_key_dict(obj=Base, lookup=lookup)) == [
        registered_for_base]


def test_component_no_source():
    reg = Registry()

    @dispatch()
    def target():
        pass

    def foo():
        pass

    reg.register_function(target, foo)
    assert target.component(lookup=reg.lookup()) is foo


def test_component_no_source_key_dict():
    reg = Registry()

    @dispatch()
    def target():
        pass

    def foo():
        pass

    reg.register_function(target, foo)
    assert target.component_key_dict(lookup=reg.lookup()) is foo


def test_component_one_source():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    reg.register_function(target, foo, obj=Alpha)

    alpha = Alpha()
    assert target.component(alpha, lookup=reg.lookup()) is foo


def test_component_one_source_key_dict():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    reg.register_function(target, foo, obj=Alpha)

    assert target.component_key_dict(obj=Alpha, lookup=reg.lookup()) is foo


def test_component_two_sources():
    reg = Registry()

    @dispatch('a', 'b')
    def target(a, b):
        pass

    def foo(a, b):
        pass

    reg.register_dispatch(target)
    reg.register_function(target, foo, a=IAlpha, b=IBeta)

    alpha = Alpha()
    beta = Beta()
    assert target.component(alpha, beta, lookup=reg.lookup()) is foo


def test_component_inheritance():
    reg = Registry()

    class Gamma(object):
        pass

    class Delta(Gamma):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    reg.register_dispatch(target)
    reg.register_function(target, foo, obj=Gamma)

    delta = Delta()

    assert target.component(delta, lookup=reg.lookup()) is foo


def test_component_inheritance_old_style_class():
    reg = Registry()

    class Gamma:
        pass

    class Delta(Gamma):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    reg.register_dispatch(target)
    reg.register_function(target, foo, obj=Gamma)

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
    reg.register_function(target, factory)

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
    reg.register_function(target, foo, obj=IAlpha)
    reg.register_function(target, bar, obj=IBeta)

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
    reg.register_function(target, foo, a=IAlpha, b=IBeta)
    reg.register_function(target, bar, a=IBeta, b=IAlpha)
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
    with pytest.raises(RegistrationError):
        reg.register_function(target, callable, a=Alpha)


def test_non_callable_registered():
    reg = Registry()

    @dispatch('obj')
    def target(obj):
        pass

    non_callable = None

    reg.register_dispatch(target)
    with pytest.raises(RegistrationError):
        reg.register_function(target, non_callable, a=Alpha)


def test_call_with_no_args_while_arg_expected():
    @dispatch('obj')
    def target(obj):
        pass

    def specific(obj):
        return "specific"

    reg = Registry()
    reg.register_dispatch(target)
    reg.register_function(target, specific, obj=Alpha)

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
    reg.register_function(target, specific, obj=Alpha)

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
    reg.register_function(target, specific, obj=Alpha)

    alpha = Alpha()
    beta = Beta()

    lookup = reg.lookup()

    assert target(alpha, lookup=lookup, extra="allowed") == 'Specific: allowed'
    assert target(beta, lookup=lookup, extra="allowed") == 'General: allowed'
    assert target(alpha, 'allowed', lookup=lookup) == 'Specific: allowed'
    assert target(beta, 'allowed', lookup=lookup) == 'General: allowed'


def test_no_implicit():
    implicit.clear()

    @dispatch('obj')
    def target(obj):
        pass

    alpha = Alpha()
    with pytest.raises(NoImplicitLookupError):
        target.component(alpha)


def test_fallback_to_fallback():

    def fallback(obj):
        return 'fallback!'

    @dispatch(match_instance('obj', lambda obj: obj,
                             fallback=fallback))
    def target(obj):
        return 'not the fallback we want'

    reg = Registry()

    def specific_target(obj):
        return 'specific'

    reg.register_dispatch(target)
    reg.register_function(target, specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta, lookup=reg.lookup()) == 'fallback!'
    # this is *not* a registered fallback so won't be returned here
    assert target.fallback(beta, lookup=reg.lookup()) is fallback
    # we cannot find a fallback for alpha, as it doesn't hit the fallback
    assert target(Alpha(), lookup=reg.lookup()) == 'specific'
    assert target.fallback(Alpha(), lookup=reg.lookup()) is NOT_FOUND


def test_fallback_to_dispatch():
    @dispatch('obj')
    def target(obj):
        return 'fallback'

    reg = Registry()

    def specific_target(obj):
        return 'specific'

    reg.register_dispatch(target)
    reg.register_function(target, specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta, lookup=reg.lookup()) == 'fallback'
    # this is *not* a registered fallback so won't be returned here
    assert target.fallback(beta, lookup=reg.lookup()) is None


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

    reg.register_function(target, a, obj=Alpha)
    reg.register_function(target, b, obj=Beta)

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

    reg.register_function(g1, g1_impl, obj=Alpha)
    reg.register_function(g2, g2_impl, obj=Alpha)

    assert g1(Alpha(), lookup=reg.lookup()) == 'g2'


def test_different_defaults_in_specific_non_dispatch_arg():
    @dispatch('obj')
    def target(obj, blah='default'):
        return 'fallback: %s' % blah

    reg = Registry()

    def a(obj, blah='default 2'):
        return 'a: %s' % blah

    reg.register_dispatch(target)
    reg.register_function(target, a, obj=Alpha)

    lookup = reg.lookup()

    assert target(Alpha(), lookup=lookup) == 'a: default 2'


def test_different_defaults_in_specific_dispatch_arg():
    @dispatch(match_key('key', lambda key: key))
    def target(key='default'):
        return 'fallback: %s' % key

    reg = Registry()

    def a(key='default 2'):
        return 'a: %s' % key

    reg.register_dispatch(target)
    reg.register_function(target, a, key='foo')

    lookup = reg.lookup()

    assert target('foo', lookup=lookup) == 'a: foo'
    assert target('bar', lookup=lookup) == 'fallback: bar'
    assert target(lookup=lookup) == 'fallback: default'


def test_different_defaults_in_specific_dispatch_arg_causes_dispatch():
    @dispatch(match_key('key', lambda key: key))
    def target(key='foo'):
        return 'fallback: %s' % key

    reg = Registry()

    def a(key='default 2'):
        return 'a: %s' % key

    reg.register_dispatch(target)
    reg.register_function(target, a, key='foo')

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


def test_register_dispatch_predicates_no_defaults():
    r = Registry()

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self):
        return self

    def get_name(request):
        return request.name

    def get_request_method(request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    r.register_dispatch_predicates(view, [
        match_instance('model', get_model, model_fallback),
        match_key('name', get_name, name_fallback),
        match_key('request_method', get_request_method,
                  request_method_fallback)])

    def foo_default(self, request):
        return "foo default"

    def foo_post(self, request):
        return "foo default post"

    def foo_edit(self, request):
        return "foo edit"

    r.register_function(view, foo_default,
                        model=Foo, name='', request_method='GET')
    r.register_function(view, foo_post,
                        model=Foo, name='', request_method='POST')
    r.register_function(view, foo_edit,
                        model=Foo, name='edit', request_method='POST')

    l = r.lookup()

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET'), lookup=l) == 'foo default'
    assert view(FooSub(), Request('', 'GET'), lookup=l) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST'), lookup=l) == 'foo edit'

    class Bar(object):
        pass

    assert view(Bar(), Request('', 'GET'), lookup=l) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET'), lookup=l) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT'),
                lookup=l) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET'), lookup=l) == 'Name fallback'


def test_dispatch_external_predicates():
    r = Registry()

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch_external_predicates()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self):
        return self

    def get_name(request):
        return request.name

    def get_request_method(request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    r.register_external_predicates(view, [
        match_instance('model', get_model, model_fallback),
        match_key('name', get_name, name_fallback),
        match_key('request_method', get_request_method,
                  request_method_fallback)])

    def foo_default(self, request):
        return "foo default"

    def foo_post(self, request):
        return "foo default post"

    def foo_edit(self, request):
        return "foo edit"

    r.register_function(view, foo_default,
                        model=Foo, name='', request_method='GET')
    r.register_function(view, foo_post,
                        model=Foo, name='', request_method='POST')
    r.register_function(view, foo_edit,
                        model=Foo, name='edit', request_method='POST')

    l = r.lookup()

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET'), lookup=l) == 'foo default'
    assert view(FooSub(), Request('', 'GET'), lookup=l) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST'), lookup=l) == 'foo edit'

    class Bar(object):
        pass

    assert view(Bar(), Request('', 'GET'), lookup=l) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET'), lookup=l) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT'),
                lookup=l) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET'), lookup=l) == 'Name fallback'
    assert view.fallback(Bar(), Request('', 'GET'), lookup=l) is model_fallback


def test_register_dispatch_predicates_register_defaults():
    r = Registry()

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self):
        return self

    def get_name(request):
        return request.name

    def get_request_method(request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    r.register_dispatch_predicates(view, [
        match_instance('model', get_model, model_fallback,
                       default=None),
        match_key('name', get_name, name_fallback,
                  default=''),
        match_key('request_method', get_request_method,
                  request_method_fallback,
                  default='GET')])

    def foo_default(self, request):
        return "foo default"

    def foo_post(self, request):
        return "foo default post"

    def foo_edit(self, request):
        return "foo edit"

    r.register_function(
        view, foo_default, model=Foo)
    r.register_function(
        view, foo_post,
        model=Foo, request_method='POST')
    r.register_function(
        view, foo_edit,
        model=Foo, name='edit', request_method='POST')

    l = r.lookup()

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET'), lookup=l) == 'foo default'
    assert view(FooSub(), Request('', 'GET'), lookup=l) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST'), lookup=l) == 'foo edit'

    class Bar(object):
        pass

    assert view(Bar(), Request('', 'GET'), lookup=l) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET'), lookup=l) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT'),
                lookup=l) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET'), lookup=l) == 'Name fallback'


def test_key_dict_to_predicate_key():
    r = Registry()

    @dispatch(
        key_predicate('foo', default='default foo'),
        key_predicate('bar', default='default bar'))
    def view(self, request):
        raise NotImplementedError()

    r.register_dispatch(view)

    assert r.key_dict_to_predicate_key(view.wrapped_func, {
        'foo': 'FOO',
        'bar': 'BAR'}) == ('FOO', 'BAR')
    assert r.key_dict_to_predicate_key(view.wrapped_func, {}) == (
        'default foo',
        'default bar')


def test_key_dict_to_predicate_key_unknown_keys():
    r = Registry()

    @dispatch(
        key_predicate('foo', default='default foo'),
        key_predicate('bar', default='default bar'))
    def view(self, request):
        raise NotImplementedError()

    r.register_dispatch(view)

    # unknown keys are just ignored
    r.key_dict_to_predicate_key(view.wrapped_func, {
        'unknown': 'blah'})


def test_register_dispatch_key_dict():
    r = Registry()

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch_external_predicates()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self):
        return self

    def get_name(request):
        return request.name

    def get_request_method(request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    r.register_external_predicates(view, [
        match_instance('model', get_model, model_fallback,
                       default=None),
        match_key('name', get_name, name_fallback,
                  default=''),
        match_key('request_method', get_request_method,
                  request_method_fallback,
                  default='GET')])

    r.register_dispatch(view)

    assert r.key_dict_to_predicate_key(
        view.wrapped_func, {}) == (None, '', 'GET')


def test_fallback_should_already_use_subset():
    class Request(object):
        def __init__(self, name, request_method, body_obj):
            self.name = name
            self.request_method = request_method
            self.body_obj = body_obj

    def get_model(self):
        return self

    def get_name(request):
        return request.name

    def get_request_method(request):
        return request.request_method

    def get_body_model(request):
        return request.body_obj.__class__

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    def body_model_fallback(self, request):
        return "Body model fallback"

    @dispatch(
        match_instance('model', get_model, model_fallback, default=None),
        match_key('name', get_name, name_fallback, default=''),
        match_key('request_method', get_request_method,
                  request_method_fallback, default='GET'),
        match_class('body_model', get_body_model,
                    body_model_fallback, default=object))
    def view(self, request):
        return "view fallback"

    r = Registry()

    def exception_view(self, request):
        return "exception view"

    r.register_function(view, exception_view, model=Exception)

    class Collection(object):
        pass

    class Item(object):
        pass

    class Item2(object):
        pass

    def collection_add(self, request):
        return "collection add"

    r.register_function(view, collection_add,
                        model=Collection, request_method='POST',
                        body_model=Item)

    assert view.fallback(Collection(),
                         Request('', 'POST', Item2()),
                         lookup=r.lookup()) is body_model_fallback
    assert view(Collection(), Request('', 'POST', Item2()),
                lookup=r.lookup()) == 'Body model fallback'


def test_dispatch_missing_argument():
    @dispatch('obj')
    def foo(obj):
        pass

    def for_bar(obj):
        return "for bar"

    class Bar(object):
        pass

    registry = Registry()

    registry.register_function(foo, for_bar, obj=Bar)

    lookup = registry.lookup()

    with pytest.raises(TypeError):
        assert foo(lookup=lookup)


def test_register_dispatch_predicates_twice():
    @dispatch_external_predicates()
    def foo(obj):
        pass

    def for_bar(obj):
        return "for bar"

    def for_qux(obj):
        return "for qux"

    class Bar(object):
        pass

    class Qux(object):
        pass

    registry = Registry()

    registry.register_dispatch_predicates(
        foo, [match_instance('obj',
                             lambda obj: obj)])
    assert foo in registry.initialized
    # second time has no effect
    registry.register_dispatch_predicates(
        foo, [match_instance('obj',
                             lambda obj: obj)])


def test_register_external_predicates_for_non_external():
    @dispatch()
    def foo():
        pass

    r = Registry()

    with pytest.raises(RegistrationError):
        r.register_external_predicates(foo, [])


def test_register_no_external_predicates_for_external():
    @dispatch_external_predicates()
    def foo():
        pass

    r = Registry()
    with pytest.raises(RegistrationError):
        r.register_dispatch(foo)


def test_dict_to_predicate_key_for_unknown_dispatch():
    @dispatch()
    def foo():
        pass

    r = Registry()

    with pytest.raises(KeyError):
        r.key_dict_to_predicate_key(foo, {})
