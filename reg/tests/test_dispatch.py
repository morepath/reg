from __future__ import unicode_literals
import pytest

from ..predicate import match_instance, match_key, match_class
from ..dispatch import dispatch
from ..error import RegistrationError


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
    @dispatch(match_instance('obj'))
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

    assert foo.by_args().component is special_foo
    assert foo.by_args().all_matches == [special_foo]
    assert foo() == 'special'
    assert foo.by_args().fallback is None


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

    assert target.by_args(sub).all_matches == [
        registered_for_sub, registered_for_base]
    assert target.by_args(base).all_matches == [
        registered_for_base]


def test_all_by_keys():
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

    assert target.by_predicates(obj=Sub).all_matches == [
        registered_for_sub, registered_for_base]
    assert target.by_predicates(obj=Base).all_matches == [
        registered_for_base]


def test_component_no_source():
    @dispatch()
    def target():
        pass

    def foo():
        pass

    target.register(foo)
    assert target.by_args().component is foo


def test_component_no_source_key_dict():
    @dispatch()
    def target():
        pass

    def foo():
        pass

    target.register(foo)
    assert target.by_predicates().component is foo


def test_component_one_source():
    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    target.register(foo, obj=Alpha)

    alpha = Alpha()
    assert target.by_args(alpha).component is foo


def test_component_one_source_key_dict():
    @dispatch('obj')
    def target(obj):
        pass

    def foo(obj):
        pass

    target.register(foo, obj=Alpha)

    assert target.by_predicates(obj=Alpha).component is foo


def test_component_two_sources():
    @dispatch('a', 'b')
    def target(a, b):
        pass

    def foo(a, b):
        pass

    target.register(foo, a=IAlpha, b=IBeta)

    alpha = Alpha()
    beta = Beta()
    assert target.by_args(alpha, beta).component is foo


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

    assert target.by_args(delta).component is foo


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

    assert target.by_args(gamma).component is foo

    # inheritance case
    assert target.by_args(delta).component is foo


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

    assert target.by_args().component is None


def test_call_not_found_no_sources():
    @dispatch()
    def target():
        return "default"

    assert target() == "default"


def test_component_not_found_one_source():
    @dispatch('obj')
    def target(obj):
        pass

    assert target.by_args('dummy').component is None


def test_call_not_found_one_source():
    @dispatch('obj')
    def target(obj):
        return "default: %s" % obj

    assert target('dummy') == 'default: dummy'


def test_component_not_found_two_sources():
    @dispatch('a', 'b')
    def target(a, b):
        pass

    assert target.by_args('dummy', 'dummy').component is None


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

    non_callable = 42

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

    with pytest.raises(TypeError):
        target.by_args().component


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

    with pytest.raises(TypeError):
        target.by_args(wrong=1)


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

    @dispatch(match_instance('obj', fallback=fallback))
    def target(obj):
        return 'not the fallback we want'

    def specific_target(obj):
        return 'specific'

    target.register(specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta) == 'fallback!'
    # this is *not* a registered fallback so won't be returned here
    assert target.by_args(beta).fallback is fallback
    # we cannot find a fallback for alpha, as it doesn't hit the fallback
    assert target(Alpha()) == 'specific'
    assert target.by_args(Alpha()).fallback is None


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
    assert target.by_args(beta).fallback is None


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


def test_different_defaults_in_specific_non_dispatch_arg():
    @dispatch('obj')
    def target(obj, blah='default'):
        return 'fallback: %s' % blah

    def a(obj, blah='default 2'):
        return 'a: %s' % blah

    target.register(a, obj=Alpha)

    assert target(Alpha()) == 'a: default'


def test_different_defaults_in_specific_dispatch_arg():
    @dispatch(match_key('key'))
    def target(key='default'):
        return 'fallback: %s' % key

    def a(key='default 2'):
        return 'a: %s' % key

    target.register(a, key='foo')

    assert target('foo') == 'a: foo'
    assert target('bar') == 'fallback: bar'
    assert target() == 'fallback: default'


def test_different_defaults_in_specific_dispatch_arg_causes_dispatch():
    @dispatch(match_key('key'))
    def target(key='foo'):
        return 'fallback: %s' % key

    def a(key='default 2'):
        return 'a: %s' % key

    target.register(a, key='foo')

    assert target('foo') == 'a: foo'
    assert target('bar') == 'fallback: bar'
    assert target() == 'a: foo'


def test_add_predicates_no_defaults():
    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self, request):
        return self

    def get_name(self, request):
        return request.name

    def get_request_method(self, request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    view.add_predicates([
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

    @dispatch()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self, request):
        return self

    def get_name(self, request):
        return request.name

    def get_request_method(self, request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    view.add_predicates([
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
    assert view.by_args(Bar(), Request('', 'GET')).fallback is model_fallback


def test_dispatch_predicates_register_defaults():
    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self, request):
        return self

    def get_name(self, request):
        return request.name

    def get_request_method(self, request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    view.add_predicates([
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
        match_key('foo', default='default foo'),
        match_key('bar', default='default bar'))
    def view(self, request):
        raise NotImplementedError()

    assert view.by_predicates(foo='FOO', bar='BAR').key == ('FOO', 'BAR')
    assert view.by_predicates().key == ('default foo', 'default bar')


def test_key_dict_to_predicate_key_unknown_keys():
    @dispatch(
        match_key('foo', default='default foo'),
        match_key('bar', default='default bar'))
    def view(self, request):
        raise NotImplementedError()

    # unknown keys are just ignored
    assert view.by_predicates(unknown='blah').key == \
        ('default foo', 'default bar')


def test_register_dispatch_key_dict():
    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    @dispatch()
    def view(self, request):
        raise NotImplementedError()

    def get_model(self, request):
        return self

    def get_name(self, request):
        return request.name

    def get_request_method(self, request):
        return request.request_method

    def model_fallback(self, request):
        return "Model fallback"

    def name_fallback(self, request):
        return "Name fallback"

    def request_method_fallback(self, request):
        return "Request method fallback"

    view.add_predicates([
        match_instance('model', get_model, model_fallback,
                       default=None),
        match_key('name', get_name, name_fallback,
                  default=''),
        match_key('request_method', get_request_method,
                  request_method_fallback,
                  default='GET')])

    assert view.by_predicates().key == (None, '', 'GET')


def test_fallback_should_already_use_subset():
    class Request(object):
        def __init__(self, name, request_method, body_obj):
            self.name = name
            self.request_method = request_method
            self.body_obj = body_obj

    def get_model(self, request):
        return self

    def get_name(self, request):
        return request.name

    def get_request_method(self, request):
        return request.request_method

    def get_body_model(self, request):
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

    assert view.by_args(
        Collection(), Request('', 'POST', Item2()),
    ).fallback is body_model_fallback
    assert view(
        Collection(), Request('', 'POST', Item2()),
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
    @dispatch()
    def foo(a, b):
        pass

    def for_bar(a, b):
        return "for bar"

    def for_qux(a, b):
        return "for qux"

    class Bar(object):
        pass

    class Qux(object):
        pass

    foo.add_predicates([match_instance('a')])
    # second time adds another one
    foo.add_predicates([match_instance('b')])
    foo.register(for_bar, a=Bar, b=Bar)
    foo.register(for_qux, a=Qux, b=Qux)
    assert foo(Bar(), Bar()) == "for bar"
    assert foo(Qux(), Qux()) == "for qux"


def test_dict_to_predicate_key_for_no_dispatch():
    @dispatch()
    def foo():
        pass

    assert foo.by_predicates().key == ()


def test_dispatch_clean():
    @dispatch('obj')
    def foo(obj):
        return "default"

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

    foo.clean()

    assert foo(Bar()) == "default"
    assert foo(Qux()) == "default"


def test_dispatch_clean_add_predicates():
    @dispatch()
    def foo(obj):
        return "default"

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

    foo.add_predicates([match_instance('obj')])
    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"

    foo.clean()

    foo.register(for_bar)

    # cannot register it for Qux, as this now has no predicates
    with pytest.raises(RegistrationError):
        foo.register(for_qux)


def test_dispatch_introspection():
    @dispatch('obj')
    def foo(obj):
        "return the foo of an object."
        return "default"

    assert foo.__name__ == 'foo'
    assert foo.__doc__ == "return the foo of an object."
    assert foo.__module__ == __name__


def test_dispatch_argname_with_decorator():
    @dispatch('obj')
    def foo(obj):
        pass

    class Bar(object):
        def method(self):
            return "bar's method"

    class Qux(object):
        def method(self):
            return "qux's method"

    @foo.register(obj=Bar)
    def for_bar(obj):
        return obj.method()

    @foo.register(obj=Qux)
    def for_qux(obj):
        return obj.method()

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"

    assert foo(Bar()) == for_bar(Bar())
    assert foo(Qux()) == for_qux(Qux())


def test_component_lookup_before_call_and_no_registrations():
    @dispatch('obj')
    def foo(obj):
        pass

    class Bar(object):
        pass

    assert foo.by_args(Bar()).component is None


def test_predicate_key_too_few_arguments_gives_typeerror():
    @dispatch('obj')
    def foo(obj):
        pass

    def for_bar(obj):
        return obj.method()

    def for_qux(obj):
        return obj.method()

    with pytest.raises(TypeError):
        assert foo.by_args()


def test_predicate_key_too_many_arguments_gives_typeerror():
    @dispatch('obj')
    def foo(obj):
        pass

    def for_bar(obj):
        return obj.method()

    def for_qux(obj):
        return obj.method()

    with pytest.raises(TypeError):
        assert foo.by_args(1, 2)


def test_predicate_key_wrong_keyword_argument_gives_typeerror():
    @dispatch('obj')
    def foo(obj):
        pass

    def for_bar(obj):
        return obj.method()

    def for_qux(obj):
        return obj.method()

    with pytest.raises(TypeError):
        assert foo.by_args(wrong=1)
