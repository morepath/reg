from __future__ import unicode_literals
import pytest

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

    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"


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

    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"


def test_dispatch_no_arguments():
    @dispatch()
    def foo():
        pass

    def special_foo():
        return "special"

    foo.register(special_foo)

    assert foo.component() is special_foo
    assert list(foo.all()) == [special_foo]
    assert foo() == 'special'
    assert foo.fallback() is None


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

    target.register(registered_for_sub, obj=Sub)
    target.register(registered_for_base, obj=Base)

    base = Base()
    sub = Sub()

    assert list(target.all(sub)) == [
        registered_for_sub, registered_for_base]
    assert list(target.all(base)) == [
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

    target.register(registered_for_sub, obj=Sub)
    target.register(registered_for_base, obj=Base)

    assert list(target.all_key_dict(obj=Sub)) == [
        registered_for_sub, registered_for_base]
    assert list(target.all_key_dict(obj=Base)) == [
        registered_for_base]


def test_component_no_source():
    @dispatch()
    def target():
        pass

    def foo():
        pass

    target.register(foo)
    assert target.component() is foo


def test_component_no_source_key_dict():
    @dispatch()
    def target():
        pass

    def foo():
        pass

    target.register(foo)
    assert target.component_key_dict() is foo


def test_component_one_source():
    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    target.register(foo, obj=Alpha)

    alpha = Alpha()
    assert target.component(alpha) is foo


def test_component_one_source_key_dict():
    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    target.register(foo, obj=Alpha)

    assert target.component_key_dict(obj=Alpha) is foo


def test_component_two_sources():
    @dispatch('a', 'b')
    def target(a, b):
        pass

    def foo(a, b):
        pass

    target.register(foo, a=IAlpha, b=IBeta)

    alpha = Alpha()
    beta = Beta()
    assert target.component(alpha, beta) is foo


def test_component_inheritance():
    class Gamma(object):
        pass

    class Delta(Gamma):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    target.register(foo, obj=Gamma)

    delta = Delta()

    assert target.component(delta) is foo


def test_component_inheritance_old_style_class():
    class Gamma:
        pass

    class Delta(Gamma):
        pass

    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    target.register(foo, obj=Gamma)

    gamma = Gamma()
    delta = Delta()

    assert target.component(gamma) is foo

    # inheritance case
    assert target.component(delta) is foo


def test_call_no_source():
    foo = object()

    @dispatch()
    def target():
        pass

    def factory():
        return foo

    target.register(factory)

    assert target() is foo


def test_call_one_source():
    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        return "foo"

    def bar(obj):
        return "bar"

    target.register(foo, obj=IAlpha)
    target.register(bar, obj=IBeta)

    assert target(Alpha()) == 'foo'
    assert target(Beta()) == 'bar'


def test_call_two_sources():
    @dispatch('a', 'b')
    def target(a, b):
        pass

    def foo(a, b):
        return "foo"

    def bar(a, b):
        return "bar"

    target.register(foo, a=IAlpha, b=IBeta)
    target.register(bar, a=IBeta, b=IAlpha)
    alpha = Alpha()
    beta = Beta()

    assert target(alpha, beta) == 'foo'
    assert target(beta, alpha) == 'bar'


def test_component_not_found_no_sources():
    @dispatch()
    def target():
        pass

    assert target.component() is None


def test_call_not_found_no_sources():
    @dispatch()
    def target():
        return "default"

    assert target() == "default"


def test_component_not_found_one_source():
    @dispatch('obj')
    def target(obj):
        pass

    assert target.component('dummy') is None


def test_call_not_found_one_source():
    @dispatch('obj')
    def target(obj):
        return "default: %s" % obj

    assert target('dummy') == 'default: dummy'


def test_component_not_found_two_sources():
    @dispatch('a', 'b')
    def target(a, b):
        pass

    assert target.component('dummy', 'dummy') is None


def test_call_not_found_two_sources():
    @dispatch('a', 'b')
    def target(a, b):
        return "a: %s b: %s" % (a, b)

    assert target('dummy1', 'dummy2') == "a: dummy1 b: dummy2"


def test_wrong_callable_registered():
    @dispatch('obj')
    def target(obj):
        pass

    def callable(a, b):
        pass

    with pytest.raises(RegistrationError):
        target.register(callable, a=Alpha)


def test_non_callable_registered():
    @dispatch('obj')
    def target(obj):
        pass

    non_callable = None

    with pytest.raises(RegistrationError):
        target.register(non_callable, a=Alpha)


def test_call_with_no_args_while_arg_expected():
    @dispatch('obj')
    def target(obj):
        pass

    def specific(obj):
        return "specific"

    target.register(specific, obj=Alpha)

    # we are not allowed to call target without arguments
    with pytest.raises(TypeError):
        target()

    with pytest.raises(KeyExtractorError):
        target.component()


def test_call_with_wrong_args():
    @dispatch('obj')
    def target(obj):
        pass

    def specific(obj):
        return "specific"

    target.register(specific, obj=Alpha)

    # we are not allowed to call target without arguments
    with pytest.raises(TypeError):
        target(wrong=1)

    with pytest.raises(KeyExtractorError):
        target.component(wrong=1)


def test_extra_arg_for_call():
    @dispatch('obj')
    def target(obj, extra):
        return "General: %s" % extra

    def specific(obj, extra):
        return "Specific: %s" % extra

    target.register(specific, obj=Alpha)

    alpha = Alpha()
    beta = Beta()

    assert target(alpha, extra="allowed") == 'Specific: allowed'
    assert target(beta, extra="allowed") == 'General: allowed'
    assert target(alpha, 'allowed') == 'Specific: allowed'
    assert target(beta, 'allowed') == 'General: allowed'


def test_fallback_to_fallback():

    def fallback(obj):
        return 'fallback!'

    @dispatch(match_instance('obj', lambda obj: obj,
                             fallback=fallback))
    def target(obj):
        return 'not the fallback we want'

    def specific_target(obj):
        return 'specific'

    target.register(specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta) == 'fallback!'
    # this is *not* a registered fallback so won't be returned here
    assert target.fallback(beta) is fallback
    # we cannot find a fallback for alpha, as it doesn't hit the fallback
    assert target(Alpha()) == 'specific'
    assert target.fallback(Alpha()) is NOT_FOUND


def test_fallback_to_dispatch():
    @dispatch('obj')
    def target(obj):
        return 'fallback'

    def specific_target(obj):
        return 'specific'

    target.register(specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta) == 'fallback'
    # this is *not* a registered fallback so won't be returned here
    assert target.fallback(beta) is None


def test_calling_twice():
    @dispatch('obj')
    def target(obj):
        return 'fallback'

    def a(obj):
        return 'a'

    def b(obj):
        return 'b'

    target.register(a, obj=Alpha)
    target.register(b, obj=Beta)

    assert target(Alpha()) == 'a'
    assert target(Beta()) == 'b'


def test_lookup_passed_along():
    @dispatch('obj')
    def g1(obj):
        pass

    @dispatch('obj')
    def g2(obj):
        pass

    def g1_impl(obj, lookup):
        return g2(obj)

    def g2_impl(obj):
        return "g2"

    g1.register(g1_impl, obj=Alpha)
    g2.register(g2_impl, obj=Alpha)

    assert g1(Alpha()) == 'g2'


def test_different_defaults_in_specific_non_dispatch_arg():
    @dispatch('obj')
    def target(obj, blah='default'):
        return 'fallback: %s' % blah

    def a(obj, blah='default 2'):
        return 'a: %s' % blah

    target.register(a, obj=Alpha)

    assert target(Alpha()) == 'a: default 2'


def test_different_defaults_in_specific_dispatch_arg():
    @dispatch(match_key('key', lambda key: key))
    def target(key='default'):
        return 'fallback: %s' % key

    def a(key='default 2'):
        return 'a: %s' % key

    target.register(a, key='foo')

    assert target('foo') == 'a: foo'
    assert target('bar') == 'fallback: bar'
    assert target() == 'fallback: default'


def test_different_defaults_in_specific_dispatch_arg_causes_dispatch():
    @dispatch(match_key('key', lambda key: key))
    def target(key='foo'):
        return 'fallback: %s' % key

    def a(key='default 2'):
        return 'a: %s' % key

    target.register(a, key='foo')

    assert target('foo') == 'a: foo'
    assert target('bar') == 'fallback: bar'
    assert target() == 'a: default 2'


def test_lookup_passed_along_fallback():
    @dispatch()
    def a(lookup):
        return "fallback"

    assert a() == 'fallback'


def test_register_dispatch_predicates_no_defaults():
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

    view.register_dispatch_predicates([
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

    view.register(foo_default, model=Foo, name='', request_method='GET')
    view.register(foo_post, model=Foo, name='', request_method='POST')
    view.register(foo_edit, model=Foo, name='edit', request_method='POST')

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST')) == 'foo edit'

    class Bar(object):
        pass

    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'


def test_dispatch_external_predicates():
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

    view.register_external_predicates([
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

    view.register(foo_default, model=Foo, name='', request_method='GET')
    view.register(foo_post, model=Foo, name='', request_method='POST')
    view.register(foo_edit, model=Foo, name='edit', request_method='POST')

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST')) == 'foo edit'

    class Bar(object):
        pass

    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'
    assert view.fallback(Bar(), Request('', 'GET')) is model_fallback


def test_register_dispatch_predicates_register_defaults():
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

    view.register_dispatch_predicates([
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

    view.register(foo_default, model=Foo)
    view.register(foo_post, model=Foo, request_method='POST')
    view.register(foo_edit, model=Foo, name='edit', request_method='POST')

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST')) == 'foo edit'

    class Bar(object):
        pass

    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'


def test_key_dict_to_predicate_key():
    @dispatch(
        key_predicate('foo', default='default foo'),
        key_predicate('bar', default='default bar'))
    def view(self, request):
        raise NotImplementedError()

    assert view.key_dict_to_predicate_key({
        'foo': 'FOO',
        'bar': 'BAR'}) == ('FOO', 'BAR')
    assert view.key_dict_to_predicate_key({}) == (
        'default foo',
        'default bar')


def test_key_dict_to_predicate_key_unknown_keys():
    @dispatch(
        key_predicate('foo', default='default foo'),
        key_predicate('bar', default='default bar'))
    def view(self, request):
        raise NotImplementedError()

    # unknown keys are just ignored
    assert view.key_dict_to_predicate_key({'unknown': 'blah'}) == (
        'default foo',
        'default bar')


def test_register_dispatch_key_dict():
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

    view.register_external_predicates([
        match_instance('model', get_model, model_fallback,
                       default=None),
        match_key('name', get_name, name_fallback,
                  default=''),
        match_key('request_method', get_request_method,
                  request_method_fallback,
                  default='GET')])

    assert view.key_dict_to_predicate_key({}) == (None, '', 'GET')


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

    def exception_view(self, request):
        return "exception view"

    view.register(exception_view, model=Exception)

    class Collection(object):
        pass

    class Item(object):
        pass

    class Item2(object):
        pass

    def collection_add(self, request):
        return "collection add"

    view.register(
        collection_add,
        model=Collection, request_method='POST',
        body_model=Item)

    assert view.fallback(Collection(),
                         Request('', 'POST', Item2()),
                         ) is body_model_fallback
    assert view(Collection(), Request('', 'POST', Item2()),
                ) == 'Body model fallback'


def test_dispatch_missing_argument():
    @dispatch('obj')
    def foo(obj):
        pass

    def for_bar(obj):
        return "for bar"

    class Bar(object):
        pass

    foo.register(for_bar, obj=Bar)

    with pytest.raises(TypeError):
        assert foo()


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

    foo.register_dispatch_predicates(
        [match_instance('obj', lambda obj: obj)])
    assert foo in foo.registry.initialized
    # second time has no effect
    foo.register_dispatch_predicates(
        [match_instance('obj', lambda obj: obj)])


def test_register_external_predicates_for_non_external():
    @dispatch()
    def foo():
        pass

    with pytest.raises(RegistrationError):
        foo.register_external_predicates([])


def test_register_no_external_predicates_for_external():
    @dispatch_external_predicates()
    def foo():
        pass

    with pytest.raises(RegistrationError):
        foo.component()


def test_dict_to_predicate_key_for_unknown_dispatch():
    @dispatch()
    def foo():
        pass

    with pytest.raises(KeyError):
        foo.registry.key_dict_to_predicate_key(foo, {})
