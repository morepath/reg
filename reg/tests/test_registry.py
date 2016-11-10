from __future__ import unicode_literals
from ..predicate import PredicateRegistry, match_instance, match_key
from ..cache import DictCachingKeyLookup, LruCachingKeyLookup
from ..error import RegistrationError
from ..dispatch import dispatch
import pytest


def register_value(generic, key, value):
    """Low-level function that directly uses the internal registry of the
    generic function to register an implementation.
    """
    generic.register.__self__.registry.register(key, value)


def test_registry():
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

    register_value(view, (Foo, '', 'GET'), foo_default)
    register_value(view, (Foo, '', 'POST'), foo_post)
    register_value(view, (Foo, 'edit', 'POST'), foo_edit)

    key_lookup = view.key_lookup
    assert key_lookup.component((Foo, '', 'GET')) is foo_default
    assert key_lookup.component((Foo, '', 'POST')) is foo_post
    assert key_lookup.component((Foo, 'edit', 'POST')) is foo_edit
    assert key_lookup.component((FooSub, '', 'GET')) is foo_default
    assert key_lookup.component((FooSub, '', 'POST')) is foo_post

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(
        Foo(), Request('', 'GET')) == 'foo default'
    assert view(
        FooSub(), Request('', 'GET')) == 'foo default'
    assert view(
        FooSub(), Request('edit', 'POST')) == 'foo edit'

    class Bar(object):
        pass

    assert view(
        Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(
        Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(
        Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(
        FooSub(), Request('dummy', 'GET')) == 'Name fallback'


def test_predicate_registry_class_lookup():
    reg = PredicateRegistry(match_instance('obj'))

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    reg.register((Document,), 'document line count')
    reg.register((SpecialDocument,),
                 'special document line count')

    assert (reg.component((Document,)) ==
            'document line count')

    assert (reg.component((SpecialDocument,)) ==
            'special document line count')

    class AnotherDocument(Document):
        pass

    assert (reg.component((AnotherDocument,)) ==
            'document line count')

    class Other(object):
        pass

    assert reg.component((Other,)) is None


def test_predicate_registry_target_find_specific():
    reg = PredicateRegistry(match_instance('obj'))
    reg2 = PredicateRegistry(match_instance('obj'))

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    def linecount(obj):
        pass

    def special_linecount(obj):
        pass

    reg.register((Document,), 'line count')
    reg2.register((Document,), 'special line count')

    assert reg.component((Document,)) == 'line count'
    assert (reg2.component((Document,)) ==
            'special line count')

    assert reg.component((SpecialDocument,)) == 'line count'
    assert (reg2.component((SpecialDocument,)) ==
            'special line count')


def test_registry_no_sources():
    reg = PredicateRegistry()

    class Animal(object):
        pass

    reg.register((), 'elephant')
    assert reg.component(()) == 'elephant'


def test_register_twice_with_predicate():
    reg = PredicateRegistry(match_instance('obj'))

    class Document(object):
        pass

    reg.register((Document,), 'document line count')
    with pytest.raises(RegistrationError):
        reg.register((Document,), 'another line count')


def test_register_twice_without_predicates():
    reg = PredicateRegistry()

    reg.register((), 'once')
    with pytest.raises(RegistrationError):
        reg.register((), 'twice')


def test_dict_caching_registry():
    class Foo(object):
        pass

    class FooSub(Foo):
        pass

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

    def get_caching_key_lookup(r):
        return DictCachingKeyLookup(r)

    @dispatch(
        match_instance('model', get_model, model_fallback),
        match_key('name', get_name, name_fallback),
        match_key('request_method', get_request_method,
                  request_method_fallback),
        get_key_lookup=get_caching_key_lookup)
    def view(self, request):
        raise NotImplementedError()

    def foo_default(self, request):
        return "foo default"

    def foo_post(self, request):
        return "foo default post"

    def foo_edit(self, request):
        return "foo edit"

    register_value(view, (Foo, '', 'GET'), foo_default)
    register_value(view, (Foo, '', 'POST'), foo_post)
    register_value(view, (Foo, 'edit', 'POST'), foo_edit)

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(
        FooSub(), Request('', 'GET')) == 'foo default'
    assert view(
        FooSub(), Request('edit', 'POST')) == 'foo edit'
    assert view.by_predicates(
        model=Foo, name='', request_method='GET').key == (Foo, '', 'GET')

    # use a bit of inside knowledge to check the cache is filled
    assert view.key_lookup.component.__self__.get(
        (Foo, '', 'GET')) is not None
    assert view.key_lookup.component.__self__.get(
        (FooSub, '', 'GET')) is not None
    assert view.key_lookup.component.__self__.get(
        (FooSub, 'edit', 'POST')) is not None

    # now let's do this again. this time things come from the component cache
    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST')) == 'foo edit'

    key_lookup = view.key_lookup
    # prime and check the all cache
    assert view.by_args(Foo(), Request('', 'GET')).all_matches == [foo_default]
    assert key_lookup.all.__self__.get((Foo, '', 'GET')) is not None
    # should be coming from cache now
    assert view.by_args(Foo(), Request('', 'GET')).all_matches == [foo_default]

    class Bar(object):
        pass
    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'

    # fallbacks get cached too
    assert key_lookup.fallback.__self__.get((Bar, '', 'GET')) is model_fallback

    # these come from the fallback cache now
    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'


def test_lru_caching_registry():
    class Foo(object):
        pass

    class FooSub(Foo):
        pass

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

    def get_caching_key_lookup(r):
        return LruCachingKeyLookup(r, 100, 100, 100)

    @dispatch(
        match_instance('model', get_model, model_fallback),
        match_key('name', get_name, name_fallback),
        match_key('request_method', get_request_method,
                  request_method_fallback),
        get_key_lookup=get_caching_key_lookup)
    def view(self, request):
        raise NotImplementedError()

    def foo_default(self, request):
        return "foo default"

    def foo_post(self, request):
        return "foo default post"

    def foo_edit(self, request):
        return "foo edit"

    register_value(view, (Foo, '', 'GET'), foo_default)
    register_value(view, (Foo, '', 'POST'), foo_post)
    register_value(view, (Foo, 'edit', 'POST'), foo_edit)

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(
        FooSub(), Request('', 'GET')) == 'foo default'
    assert view(
        FooSub(), Request('edit', 'POST')) == 'foo edit'
    assert view.by_predicates(
        model=Foo, name='', request_method='GET').key == (Foo, '', 'GET')

    # use a bit of inside knowledge to check the cache is filled
    component_cache = view.key_lookup.component.__closure__[0].cell_contents
    assert component_cache.get(((Foo, '', 'GET'),)) is not None
    assert component_cache.get(((FooSub, '', 'GET'),)) is not None
    assert component_cache.get(((FooSub, 'edit', 'POST'),)) is not None

    # now let's do this again. this time things come from the component cache
    assert view(Foo(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('', 'GET')) == 'foo default'
    assert view(FooSub(), Request('edit', 'POST')) == 'foo edit'

    all_cache = view.key_lookup.all.__closure__[0].cell_contents
    # prime and check the all cache
    assert view.by_args(Foo(), Request('', 'GET')).all_matches == [foo_default]
    assert all_cache.get(((Foo, '', 'GET'),)) is not None
    # should be coming from cache now
    assert view.by_args(Foo(), Request('', 'GET')).all_matches == [foo_default]

    class Bar(object):
        pass
    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'

    # fallbacks get cached too
    fallback_cache = view.key_lookup.fallback.__closure__[0].cell_contents
    assert fallback_cache.get(((Bar, '', 'GET'),)) is model_fallback

    # these come from the fallback cache now
    assert view(Bar(), Request('', 'GET')) == 'Model fallback'
    assert view(Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert view(Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert view(FooSub(), Request('dummy', 'GET')) == 'Name fallback'
