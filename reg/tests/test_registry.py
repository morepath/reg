from __future__ import unicode_literals
from reg.registry import Registry, CachingKeyLookup
from reg.predicate import (class_predicate,
                           match_instance, match_key)
from reg.error import RegistrationError
import pytest


def test_registry():
    r = Registry()

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

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

    r.register_callable_predicates(view, [
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

    r.register_value(view, (Foo, '', 'GET'), foo_default)
    r.register_value(view, (Foo, '', 'POST'), foo_post)
    r.register_value(view, (Foo, 'edit', 'POST'), foo_edit)

    assert r.component(view, (Foo, '', 'GET')) is foo_default
    assert r.component(view, (Foo, '', 'POST')) is foo_post
    assert r.component(view, (Foo, 'edit', 'POST')) is foo_edit
    assert r.component(view, (FooSub, '', 'GET')) is foo_default
    assert r.component(view, (FooSub, '', 'POST')) is foo_post

    l = r.lookup()

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert l.call(view, Foo(), Request('', 'GET')) == 'foo default'
    assert l.call(view, FooSub(), Request('', 'GET')) == 'foo default'
    assert l.call(view, FooSub(), Request('edit', 'POST')) == 'foo edit'

    class Bar(object):
        pass

    assert l.call(view, Bar(), Request('', 'GET')) == 'Model fallback'
    assert l.call(view, Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert l.call(view, Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert l.call(view, FooSub(), Request('dummy', 'GET')) == 'Name fallback'


def test_registry_class_lookup():
    reg = Registry()

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    linecount = 'linecount'

    reg.register_predicates(linecount, [class_predicate('obj')])
    reg.register_value(linecount, [Document], 'document line count')
    reg.register_value(linecount, [SpecialDocument],
                       'special document line count')

    assert (reg.component(linecount, Document) ==
            'document line count')

    assert (reg.component(linecount, SpecialDocument) ==
            'special document line count')

    class AnotherDocument(Document):
        pass

    assert (reg.component(linecount, AnotherDocument) ==
            'document line count')

    class Other(object):
        pass

    assert reg.component(linecount, Other) is None


def test_registry_target_find_specific():
    reg = Registry()

    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    def linecount(obj):
        pass

    def special_linecount(obj):
        pass

    reg.register_predicates(linecount, [class_predicate('obj')])
    reg.register_value(linecount, [Document], 'line count')
    reg.register_predicates(special_linecount, [class_predicate('obj')])
    reg.register_value(special_linecount, [Document], 'special line count')

    assert reg.component(linecount, Document) == 'line count'
    assert (reg.component(special_linecount, Document) ==
            'special line count')

    assert reg.component(linecount, SpecialDocument) == 'line count'
    assert (reg.component(special_linecount, SpecialDocument) ==
            'special line count')


def test_registry_no_sources():
    reg = Registry()

    class Animal(object):
        pass

    def something():
        pass

    reg.register_predicates(something, [])
    reg.register_value(something, (), 'elephant')
    assert reg.component(something, ()) == 'elephant'


def test_register_twice_with_predicate():
    reg = Registry()

    class Document(object):
        pass

    def linecount(obj):
        pass

    reg.register_predicates(linecount, [class_predicate('obj')])
    reg.register_value(linecount, [Document], 'document line count')
    with pytest.raises(RegistrationError):
        reg.register_value(linecount, [Document], 'another line count')


def test_register_twice_without_predicates():
    reg = Registry()

    def linecount(obj):
        pass

    reg.register_predicates(linecount, [])
    reg.register_value(linecount, (), 'once')
    with pytest.raises(RegistrationError):
        reg.register_value(linecount, (), 'twice')


def test_clear():
    reg = Registry()

    def linecount():
        pass

    reg.register_predicates(linecount, [])
    reg.register_value(linecount, (), 'once')
    assert reg.component(linecount, ()) == 'once'
    reg.clear()
    reg.register_predicates(linecount, [])
    assert reg.component(linecount, ()) is None


def test_caching_registry():
    r = Registry()

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

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

    r.register_callable_predicates(view, [
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

    r.register_value(view, (Foo, '', 'GET'), foo_default)
    r.register_value(view, (Foo, '', 'POST'), foo_post)
    r.register_value(view, (Foo, 'edit', 'POST'), foo_edit)

    l = CachingKeyLookup(r, 100, 100, 100).lookup()

    class Request(object):
        def __init__(self, name, request_method):
            self.name = name
            self.request_method = request_method

    assert l.call(view, Foo(), Request('', 'GET')) == 'foo default'
    assert l.call(view, FooSub(), Request('', 'GET')) == 'foo default'
    assert l.call(view, FooSub(), Request('edit', 'POST')) == 'foo edit'

    # use a bit of inside knowledge to check the cache is filled
    assert l.key_lookup.component_cache.get(
        (view, (Foo, '', 'GET'))) is not None
    assert l.key_lookup.component_cache.get(
        (view, (FooSub, '', 'GET'))) is not None
    assert l.key_lookup.component_cache.get(
        (view, (FooSub, 'edit', 'POST'))) is not None

    # now let's do this again. this time things come from the component cache
    assert l.call(view, Foo(), Request('', 'GET')) == 'foo default'
    assert l.call(view, FooSub(), Request('', 'GET')) == 'foo default'
    assert l.call(view, FooSub(), Request('edit', 'POST')) == 'foo edit'

    # prime and check the all cache
    assert list(l.all(view, Foo(), Request('', 'GET'))) == [foo_default]
    assert l.key_lookup.all_cache.get(
        (view, (Foo, '', 'GET'))) is not None
    # should be coming from cache now
    assert list(l.all(view, Foo(), Request('', 'GET'))) == [foo_default]

    class Bar(object):
        pass
    assert l.call(view, Bar(), Request('', 'GET')) == 'Model fallback'
    assert l.call(view, Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert l.call(view, Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert l.call(view, FooSub(), Request('dummy', 'GET')) == 'Name fallback'

    # fallbacks get cached too
    assert l.key_lookup.fallback_cache.get(
        (view, (Bar, '', 'GET'))) is model_fallback

    # these come from the fallback cache now
    assert l.call(view, Bar(), Request('', 'GET')) == 'Model fallback'
    assert l.call(view, Foo(), Request('dummy', 'GET')) == 'Name fallback'
    assert l.call(view, Foo(), Request('', 'PUT')) == 'Request method fallback'
    assert l.call(view, FooSub(), Request('dummy', 'GET')) == 'Name fallback'
