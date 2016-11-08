from types import FunctionType
import pytest
from ..context import (
    dispatch, dispatch_method, methodify, clean_dispatch_methods)
from ..predicate import match_instance
from ..error import RegistrationError


def test_dispatch_method_explicit_fallback():
    def obj_fallback(self, obj):
        return "Obj fallback"

    class Foo(object):
        @dispatch_method(match_instance('obj', fallback=obj_fallback))
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
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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
    class Foo(object):
        @dispatch_method()
        def bar(self, obj):
            return "default"

    Foo.bar.add_predicates([match_instance('obj')])

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
    class Foo(object):
        @dispatch_method(match_instance('obj'))
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()

    assert foo.bar(Alpha()) == "default"

    Foo.bar.register(methodify(lambda obj: "Alpha"), obj=Alpha)
    Foo.bar.register(methodify(lambda obj: "Beta"), obj=Beta)

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
        Foo.bar.register(methodify(lambda obj, extra: "Alpha"), obj=Alpha)


def test_dispatch_method_register_function_wrong_signature_too_short():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    with pytest.raises(RegistrationError):
        Foo.bar.register(methodify(lambda: "Alpha"), obj=Alpha)


def test_dispatch_method_register_non_callable():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    with pytest.raises(RegistrationError):
        Foo.bar.register("cannot call this", obj=Alpha)


def test_dispatch_method_methodify_non_callable():
    with pytest.raises(TypeError):
        methodify("cannot call this")


def test_dispatch_method_register_auto():
    class Foo(object):
        x = 'X'

        @dispatch_method(match_instance('obj'))
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    foo = Foo()

    assert foo.bar(Alpha()) == "default"

    Foo.bar.register(methodify(lambda obj: "Alpha", 'app'), obj=Alpha)
    Foo.bar.register(
        methodify(lambda app, obj: "Beta %s" % app.x, 'app'),
        obj=Beta)

    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta X"
    assert foo.bar(None) == "default"


def test_dispatch_method_class_method_accessed_first():
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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
    class Foo(object):
        def __init__(self, x):
            self.x = x

        @dispatch_method(match_instance('obj'))
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
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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
    class Foo(object):
        @dispatch_method(match_instance('obj'))
        def bar(self, obj):
            return "default"

    class Sub(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    # programmatic style:
    Foo.bar.register(lambda self, obj: "Foo Alpha", obj=Alpha)
    # decorator style:
    Foo.bar.register(obj=Beta)(lambda self, obj: "Foo Beta")
    # programmatic style:
    Sub.bar.register(lambda self, obj: "Sub Alpha", obj=Alpha)
    # decorator style:
    Sub.bar.register(obj=Beta)(lambda self, obj: "Sub Beta")

    foo = Foo()
    sub = Sub()

    assert foo.bar(Alpha()) == "Foo Alpha"
    assert foo.bar(Beta()) == "Foo Beta"
    assert foo.bar(None) == "default"

    assert sub.bar(Alpha()) == "Sub Alpha"
    assert sub.bar(Beta()) == "Sub Beta"
    assert sub.bar(None) == "default"


def test_dispatch_method_inheritance_separation_multiple():
    class Foo(object):
        @dispatch_method(match_instance('obj'))
        def bar(self, obj):
            return "bar default"

        @dispatch_method(match_instance('obj'))
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
    def obj_fallback(self, obj):
        return "Obj fallback"

    class Foo(object):
        @dispatch_method(match_instance('obj', fallback=obj_fallback))
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
    assert Foo.bar.by_args(Alpha()).component == alpha_func
    assert foo.bar.by_args(Alpha()).component == alpha_func
    assert foo.bar.by_args(Alpha()).all_matches == [alpha_func]
    assert foo.bar.by_args(Beta()).component == beta_func
    assert foo.bar.by_args(None).component is None
    assert foo.bar.by_args(None).fallback is obj_fallback
    assert foo.bar.by_args(None).all_matches == []


def test_dispatch_method_with_register_function_value():
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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

    Foo.bar.register(methodify(alpha_func), obj=Alpha)
    Foo.bar.register(methodify(beta_func), obj=Beta)

    assert unmethodify(foo.bar.by_args(Alpha()).component) is alpha_func


def test_dispatch_method_with_register_auto_value():
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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

    Foo.bar.register(methodify(alpha_func, 'app'), obj=Alpha)
    Foo.bar.register(methodify(beta_func, 'app'), obj=Beta)

    assert unmethodify(foo.bar.by_args(Alpha()).component) is alpha_func
    assert unmethodify(foo.bar.by_args(Beta()).component) is beta_func
    # actually since this is a method this is also unwrapped
    assert foo.bar.by_args(Beta()).component is beta_func


def test_install_method():
    class Target(object):
        pass

    def f(self, a):
        return a

    Target.m = f

    t = Target()

    assert t.m('A') == 'A'


def test_install_auto_method_function_no_app_arg():
    class Target(object):
        pass

    def f(a):
        return a

    Target.m = methodify(f, 'app')

    t = Target()

    assert t.m('A') == 'A'
    assert unmethodify(t.m) is f


def test_install_auto_method_function_app_arg():
    class Target(object):
        pass

    def g(app, a):
        assert isinstance(app, Target)
        return a

    Target.m = methodify(g, 'app')

    t = Target()
    assert t.m('A') == 'A'
    assert unmethodify(t.m) is g


def test_install_auto_method_method_no_app_arg():
    class Target(object):
        pass

    class Foo(object):
        def f(self, a):
            return a

    f = Foo().f

    Target.m = methodify(f, 'app')

    t = Target()

    assert t.m('A') == 'A'
    assert unmethodify(t.m) is f


def test_install_auto_method_method_app_arg():
    class Target(object):
        pass

    class Bar(object):
        def g(self, app, a):
            assert isinstance(app, Target)
            return a

    g = Bar().g

    Target.m = methodify(g, 'app')

    t = Target()

    assert t.m('A') == 'A'
    assert unmethodify(t.m) is g


def test_install_instance_method():
    class Target(object):
        pass

    class Bar(object):
        def g(self, a):
            assert isinstance(self, Bar)
            return a

    g = Bar().g

    Target.m = methodify(g)

    t = Target()

    assert t.m('A') == 'A'
    assert unmethodify(t.m) is g


def test_dispatch_method_introspection():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            "Return the bar of an object."
            return "default"

    assert Foo.bar.__name__ == 'bar'
    assert Foo.bar.__doc__ == "Return the bar of an object."
    assert Foo.bar.__module__ == __name__


def test_dispatch_method_clean():
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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
    class Foo(object):
        @dispatch_method(match_instance('obj'))
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


def test_replacing_with_normal_method():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class Alpha(object):
        pass

    class Beta(object):
        pass

    # At this moment Foo.bar is still a descriptor, even though it is
    # not easy to see that:
    assert isinstance(vars(Foo)['bar'], dispatch_method)

    # Simply using Foo.bar wouldn't have worked here, as it would
    # invoke the descriptor:
    assert isinstance(Foo.bar, FunctionType)

    # We now replace the descriptor with the actual unbound method:
    Foo.bar = Foo.bar

    # Now the descriptor is gone
    assert isinstance(vars(Foo)['bar'], FunctionType)

    # But we can still use the generic function as usual, and even
    # register new implementations:
    Foo.bar.register(obj=Alpha)(lambda self, obj: "Alpha")
    Foo.bar.register(obj=Beta)(lambda self, obj: "Beta")
    foo = Foo()
    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"


def test_replacing_with_normal_method_and_its_effect_on_inheritance():
    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class SubFoo(Foo):
        pass

    class Alpha(object):
        pass

    class Beta(object):
        pass

    Foo.bar.register(obj=Alpha)(lambda self, obj: "Alpha")
    Foo.bar.register(obj=Beta)(lambda self, obj: "Beta")

    foo = Foo()
    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"

    # SubFoo has different dispatching from Foo
    subfoo = SubFoo()
    assert subfoo.bar(Alpha()) == "default"
    assert subfoo.bar(Beta()) == "default"
    assert subfoo.bar(None) == "default"

    # We now replace the descriptor with the actual unbound method:
    Foo.bar = Foo.bar

    # Now the descriptor is gone
    assert isinstance(vars(Foo)['bar'], FunctionType)

    # Foo.bar works as before:
    foo = Foo()
    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"

    # But now SubFoo.bar shares the dispatch registry with Foo:
    subfoo = SubFoo()
    assert subfoo.bar(Alpha()) == "Alpha"
    assert subfoo.bar(Beta()) == "Beta"
    assert subfoo.bar(None) == "default"

    # This is exactly the same behavior we'd get by using dispatch
    # instead of dispatch_method:
    del Foo, SubFoo

    class Foo(object):
        @dispatch('obj')
        def bar(self, obj):
            return "default"

    class SubFoo(Foo):
        pass

    # Foo and SubFoo share the same registry:
    Foo.bar.register(obj=Alpha)(lambda self, obj: "Alpha")
    SubFoo.bar.register(obj=Beta)(lambda self, obj: "Beta")

    foo = Foo()
    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"

    subfoo = SubFoo()
    assert subfoo.bar(Alpha()) == "Alpha"
    assert subfoo.bar(Beta()) == "Beta"
    assert subfoo.bar(None) == "default"

    # Now we start again, and do the replacement for both subclass and
    # parent class, in this order:
    del Foo, SubFoo

    class Foo(object):
        @dispatch_method('obj')
        def bar(self, obj):
            return "default"

    class SubFoo(Foo):
        pass

    Foo.bar.register(obj=Alpha)(lambda self, obj: "Alpha")
    Foo.bar.register(obj=Beta)(lambda self, obj: "Beta")

    SubFoo.bar = SubFoo.bar
    Foo.bar = Foo.bar

    # This has kept two separate registries:
    foo = Foo()
    assert foo.bar(Alpha()) == "Alpha"
    assert foo.bar(Beta()) == "Beta"
    assert foo.bar(None) == "default"

    subfoo = SubFoo()
    assert subfoo.bar(Alpha()) == "default"
    assert subfoo.bar(Beta()) == "default"
    assert subfoo.bar(None) == "default"


def unmethodify(func):
    """Reverses methodify operation.

    Given an object that is returned from a call to
    :func:`reg.methodify` return the original object. This can be used to
    discover the original object that was registered. You can apply
    this to a function after it was attached as a method.

    :param func: the methodified function.
    :returns: the original function.
    """
    func = getattr(func, '__func__', func)
    return func.__globals__.get('_func', func)
