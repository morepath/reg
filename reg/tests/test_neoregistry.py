from ..neoregistry import Registry, Lookup
from ..neopredicate import match_instance, match_key, match_class


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
        match_instance(get_model, model_fallback),
        match_key(get_name, name_fallback),
        match_key(get_request_method, request_method_fallback)])

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

    l = Lookup(r)

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
