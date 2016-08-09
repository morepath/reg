import pytest

from ..dispatch import dispatch_method
from ..predicate import match_instance


def test_dispatch_method_explicit_fallback():
    def get_obj(obj):
        return obj

    def obj_fallback(self, obj):
        return "Obj fallback"

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj, obj_fallback))
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()

    assert foo.bar(Alpha()) == "Obj fallback"

    Foo.bar.register(lambda self, obj: "Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Beta", obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "Obj fallback"


def test_dispatch_method_without_fallback():
    def get_obj(obj):
        return obj

    def obj_fallback(self, obj):
        return "Obj fallback"

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()

    assert foo.bar(Alpha()) == "default"

    Foo.bar.register(lambda self, obj: "Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Beta", obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"


def test_dispatch_method_inheritance():
    def get_obj(obj):
        return obj

    def obj_fallback(self, obj):
        return "Obj fallback"

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Sub(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    sub = Sub()

    assert sub.bar(Alpha()) == "default"

    Sub.bar.register(lambda self, obj: "Alpha", obj=Alpha)
    Sub.bar.register(lambda self, obj: "Beta", obj=Beta)

    assert sub.bar(Alpha()) == "Alpha"
    assert sub.bar(Beta()) == "Beta"
    assert sub.bar(None) == "default"


@pytest.mark.xfail
def test_dispatch_method_inheritance_separation():
    def get_obj(obj):
        return obj

    def obj_fallback(self, obj):
        return "Obj fallback"

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Sub(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    Foo.bar.register(lambda self, obj: "Foo Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Foo Beta", obj=Beta)
    Sub.bar.register(lambda self, obj: "Sub Alpha", obj=Alpha)
    Sub.bar.register(lambda self, obj: "Sub Beta", obj=Beta)

    foo = Foo()
    sub = Sub()

    assert foo.bar(Alpha()) == "Foo Alpha"
    assert foo.bar(Beta()) == "Foo Beta"
    assert foo.bar(None) == "default"

    assert sub.bar(Alpha()) == "Sub Alpha"
    assert sub.bar(Beta()) == "Sub Beta"
    assert sub.bar(None) == "default"
