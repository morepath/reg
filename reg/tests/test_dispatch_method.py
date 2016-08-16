import pytest
from ..dispatch import (dispatch_method,
                        install_auto_method,
                        clean_dispatch_methods)
from ..predicate import match_instance
from ..error import RegistrationError


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


def test_dispatch_method_string_predicates():
    def get_obj(obj):
        return obj

    class Foo(object):
        @dispatch_method('obj')
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


def test_dispatch_method_add_predicates():
    def get_obj(obj):
        return obj

    class Foo(object):
        @dispatch_method()
        def bar(self, obj):
            return "default"

    Foo.bar.add_predicates([match_instance('obj', get_obj)])

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


def test_dispatch_method_register_function():
    def get_obj(obj):
        return obj

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

    Foo.bar.register_function(lambda obj: "Alpha", obj=Alpha)
    Foo.bar.register_function(lambda obj: "Beta", obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"


def test_dispatch_method_register_function_wrong_signature_too_long():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    with pytest.raises(RegistrationError):
        Foo.bar.register_function(lambda obj, extra: "Alpha", obj=Alpha)


def test_dispatch_method_register_function_wrong_signature_too_short():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    with pytest.raises(RegistrationError):
        Foo.bar.register_function(lambda: "Alpha", obj=Alpha)


def test_dispatch_method_register_function_non_callable():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    with pytest.raises(RegistrationError):
        Foo.bar.register_function("cannot call this", obj=Alpha)


def test_dispatch_method_register_auto():
    def get_obj(obj):
        return obj

    class Foo(object):
        x = 'X'

        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()

    assert foo.bar(Alpha()) == "default"

    Foo.bar.register_auto(lambda obj: "Alpha", obj=Alpha)
    Foo.bar.register_auto(lambda app, obj: "Beta %s" % app.x, obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta X"
    assert foo.bar(None) == "default"


def test_dispatch_method_class_method_accessed_first():
    def get_obj(obj):
        return obj

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    Foo.bar.register(lambda self, obj: "Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Beta", obj=Beta)

    foo = Foo()

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"


def test_dispatch_method_accesses_instance():
    def get_obj(obj):
        return obj

    class Foo(object):
        def __init__(self, x):
            self.x = x

        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default %s" % self.x

    class Alpha(object):
        pass

    class Beta(object):
        pass

    Foo.bar.register(lambda self, obj: "Alpha %s" % self.x, obj=Alpha)
    Foo.bar.register(lambda self, obj: "Beta %s" % self.x, obj=Beta)

    foo = Foo('hello')

    assert foo.bar(Alpha()) == "Alpha hello"
    assert foo.bar(Beta()) == "Beta hello"
    assert foo.bar(None) == "default hello"


def test_dispatch_method_inheritance_register_on_subclass():
    def get_obj(obj):
        return obj

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


def test_dispatch_method_inheritance_separation():
    def get_obj(obj):
        return obj

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


def test_dispatch_method_inheritance_separation_multiple():
    def get_obj(obj):
        return obj

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "bar default"

        @dispatch_method(match_instance('obj', get_obj))
        def qux(self, obj):
            return "qux default"

    class Sub(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    Foo.bar.register(lambda self, obj: "Bar Foo Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Bar Foo Beta", obj=Beta)
    Sub.bar.register(lambda self, obj: "Bar Sub Alpha", obj=Alpha)
    Sub.bar.register(lambda self, obj: "Bar Sub Beta", obj=Beta)

    Foo.qux.register(lambda self, obj: "Qux Foo Alpha", obj=Alpha)
    Foo.qux.register(lambda self, obj: "Qux Foo Beta", obj=Beta)
    Sub.qux.register(lambda self, obj: "Qux Sub Alpha", obj=Alpha)
    Sub.qux.register(lambda self, obj: "Qux Sub Beta", obj=Beta)

    foo = Foo()
    sub = Sub()

    assert foo.bar(Alpha()) == "Bar Foo Alpha"
    assert foo.bar(Beta()) == "Bar Foo Beta"
    assert foo.bar(None) == "bar default"

    assert sub.bar(Alpha()) == "Bar Sub Alpha"
    assert sub.bar(Beta()) == "Bar Sub Beta"
    assert sub.bar(None) == "bar default"

    assert foo.qux(Alpha()) == "Qux Foo Alpha"
    assert foo.qux(Beta()) == "Qux Foo Beta"
    assert foo.qux(None) == "qux default"

    assert sub.qux(Alpha()) == "Qux Sub Alpha"
    assert sub.qux(Beta()) == "Qux Sub Beta"
    assert sub.qux(None) == "qux default"


def test_dispatch_method_api_available():
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

    def alpha_func(self, obj):
        return "Alpha"

    def beta_func(self, obj):
        return "Beta"

    Foo.bar.register(alpha_func, obj=Alpha)
    Foo.bar.register(beta_func, obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert Foo.bar.component(Alpha()) == alpha_func
    assert foo.bar.component(Alpha()) == alpha_func
    assert list(foo.bar.all(Alpha())) == [alpha_func]
    assert foo.bar.component(Beta()) == beta_func
    assert foo.bar.component(None) is None
    assert foo.bar.fallback(None) is obj_fallback
    assert list(foo.bar.all(None)) == []


def test_dispatch_method_with_register_function_value():
    def get_obj(obj):
        return obj

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

    def alpha_func(obj):
        return "Alpha"

    def beta_func(obj):
        return "Beta"

    Foo.bar.register_function(alpha_func, obj=Alpha)
    Foo.bar.register_function(beta_func, obj=Beta)

    assert foo.bar.component(Alpha()).value is alpha_func


def test_dispatch_method_with_register_auto_value():
    def get_obj(obj):
        return obj

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

    def alpha_func(obj):
        return "Alpha"

    def beta_func(app, obj):
        return "Beta"

    Foo.bar.register_auto(alpha_func, obj=Alpha)
    Foo.bar.register_auto(beta_func, obj=Beta)

    assert foo.bar.component(Alpha()).value is alpha_func
    assert foo.bar.component(Beta()).value is beta_func
    # actually since this is a method this is also unwrapped
    assert foo.bar.component(Beta()) is beta_func


def test_install_auto_method_function_no_app_arg():
    class Target(object):
        pass

    def f(a):
        return a

    install_auto_method(Target, 'm', f)

    t = Target()

    assert t.m('A') == 'A'
    assert t.m.value is f


def test_install_auto_method_function_app_arg():
    class Target(object):
        pass

    def g(app, a):
        assert isinstance(app, Target)
        return a

    install_auto_method(Target, 'm', g)

    t = Target()
    assert t.m('A') == 'A'
    assert t.m.value is g


def test_install_auto_method_method_no_app_arg():
    class Target(object):
        pass

    class Foo(object):
        def f(self, a):
            return a

    f = Foo().f

    install_auto_method(Target, 'm', f)

    t = Target()

    assert t.m('A') == 'A'
    assert t.m.value is f


def test_install_auto_method_method_app_arg():
    class Target(object):
        pass

    class Bar(object):
        def g(self, app, a):
            assert isinstance(app, Target)
            return a

    g = Bar().g

    install_auto_method(Target, 'm', g)

    t = Target()

    assert t.m('A') == 'A'
    assert t.m.value is g


def test_dispatch_method_clean():
    def get_obj(obj):
        return obj

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Qux(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()
    qux = Qux()

    Foo.bar.register(lambda self, obj: "Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Beta", obj=Beta)
    Qux.bar.register(lambda self, obj: "Qux Alpha", obj=Alpha)
    Qux.bar.register(lambda self, obj: "Qux Beta", obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"
    assert qux.bar(Alpha()) == "Qux Alpha"
    assert qux.bar(Beta()) == "Qux Beta"
    assert qux.bar(None) == "default"

    Foo.bar.clean()

    assert foo.bar(Alpha()) == "default"

    # but hasn't affected qux registry
    assert qux.bar(Alpha()) == "Qux Alpha"


def test_clean_dispatch_methods():
    def get_obj(obj):
        return obj

    class Foo(object):
        @dispatch_method(match_instance('obj', get_obj))
        def bar(self, obj):
            return "default"

    class Qux(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()
    qux = Qux()

    Foo.bar.register(lambda self, obj: "Alpha", obj=Alpha)
    Foo.bar.register(lambda self, obj: "Beta", obj=Beta)
    Qux.bar.register(lambda self, obj: "Qux Alpha", obj=Alpha)
    Qux.bar.register(lambda self, obj: "Qux Beta", obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"
    assert qux.bar(Alpha()) == "Qux Alpha"
    assert qux.bar(Beta()) == "Qux Beta"
    assert qux.bar(None) == "default"

    clean_dispatch_methods(Foo)

    assert foo.bar(Alpha()) == "default"
    # but hasn't affected qux registry
    assert qux.bar(Alpha()) == "Qux Alpha"
