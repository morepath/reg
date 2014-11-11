from __future__ import unicode_literals
import pytest
from reg.mapply import mapply
from reg.arginfo import arginfo


def test_mapply():
    def foo(a):
        return "foo with %s" % a

    assert mapply(foo, a=1) == "foo with 1"
    assert mapply(foo, a=1, b=2) == "foo with 1"


def test_mapply_fail():
    def foo(a):
        return "foo with %s" % a

    with pytest.raises(TypeError):
        mapply(foo, b=2)


def test_mapply_args():
    def foo(a):
        return "foo with %s" % a

    assert mapply(foo, 1) == 'foo with 1'


def test_mapply_with_method():
    class Foo(object):
        def method(self, a):
            return "method with %s" % a

    f = Foo()
    assert mapply(f.method, a=1) == "method with 1"
    assert mapply(f.method, a=1, b=2) == "method with 1"


def test_mapply_with_constructor():
    class Foo(object):
        def __init__(self, a):
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_with_old_style_class():
    class Foo:
        def __init__(self, a):
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_callable_object():
    class Foo(object):
        def __call__(self, a):
            return "called with %s" % a

    f = Foo()
    assert mapply(f, a=1) == 'called with 1'
    assert mapply(f, a=1, b=1) == 'called with 1'


def test_mapply_non_function():
    a = 1

    with pytest.raises(Exception):
        assert mapply(a, a=1)


def test_mapply_builtin():
    assert mapply(int, '1') == 1


def test_mapply_kw():
    def foo(**kw):
        return kw
    assert mapply(foo, a=1) == {'a': 1}


def test_mapply_args2():
    def foo(*args):
        return args
    assert mapply(foo, a=1) == ()
    assert mapply(foo, 1) == (1,)


def test_mapply_args_kw():
    def foo(*args, **kw):
        return args, kw
    assert mapply(foo, a=1) == ((), {'a': 1})
    assert mapply(foo, 1) == ((1,), {})
    assert mapply(foo, 1, a=1) == ((1,), {'a': 1})


def test_mapply_all_args_kw():
    def foo(a, *args, **kw):
        return a, args, kw
    assert mapply(foo, 1) == (1, (), {})
    assert mapply(foo, 2, b=1) == (2, (), {'b': 1})
    assert mapply(foo, 2, 3, b=1) == (2, (3,), {'b': 1})


def test_mapply_class():
    class Foo(object):
        def __init__(self):
            pass
    assert isinstance(mapply(Foo), Foo)


def test_mapply_class_too_much():
    class Foo(object):
        def __init__(self):
            pass
    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_classic_class_too_much():
    class Foo:
        def __init__(self):
            pass
    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_class_no_init_too_much():
    class Foo(object):
        pass
    variables = {'base': None}
    assert isinstance(mapply(Foo, **variables), Foo)


def test_mapply_classic_class_no_init_too_much():
    class Foo:
        pass
    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_kw_class():
    class Foo(object):
        def __init__(self, **kw):
            self.kw = kw
    assert mapply(Foo, a=1).kw == {'a': 1}


def test_mapply_args_class():
    class Foo(object):
        def __init__(self, *args):
            self.args = args
    assert mapply(Foo, a=1).args == ()
    assert mapply(Foo, 1).args == (1,)


def test_mapply_args_kw_class():
    class Foo(object):
        def __init__(self, *args, **kw):
            self.args = args
            self.kw = kw
    r = mapply(Foo, a=1)
    assert (r.args, r.kw) == ((), {'a': 1})
    r = mapply(Foo, 1)
    assert (r.args, r.kw) == ((1,), {})
    r = mapply(Foo, 1, a=1)
    assert (r.args, r.kw) == ((1,), {'a': 1})


def test_mapply_all_args_kw_class():
    class Foo(object):
        def __init__(self, a, *args, **kw):
            self.a = a
            self.args = args
            self.kw = kw
    r = mapply(Foo, 1)
    assert (r.a, r.args, r.kw) == (1, (), {})
    r = mapply(Foo, 2, b=1)
    assert (r.a, r.args, r.kw) == (2, (), {'b': 1})
    r = mapply(Foo, 2, 3, b=1)
    assert (r.a, r.args, r.kw) == (2, (3,), {'b': 1})


def func_no_args():
    pass


class ObjNoArgs(object):
    def __call__(self):
        pass


obj_no_args = ObjNoArgs()


class MethodNoArgs(object):
    def method(self):
        pass


method_no_args = MethodNoArgs()


class StaticMethodNoArgs(object):
    @staticmethod
    def method():
        pass


class ClassMethodNoArgs(object):
    @classmethod
    def method(cls):
        pass


class ClassNoInit(object):
    pass


class ClassNoArgs(object):
    def __init__(self):
        pass


class ClassicNoInit:
    pass


class ClassicNoArgs:
    def __init__(self):
        pass


class InheritedNoInit(ClassNoInit):
    pass


class InheritedNoArgs(ClassNoArgs):
    pass


class ClassicInheritedNoInit(ClassicNoInit):
    pass


class ClassicInheritedNoArgs(ClassicNoArgs):
    pass


@pytest.mark.parametrize("callable", [func_no_args, obj_no_args,
                                      method_no_args.method,
                                      StaticMethodNoArgs.method,
                                      ClassMethodNoArgs.method,
                                      ClassNoInit, ClassNoArgs,
                                      ClassicNoInit, ClassicNoArgs,
                                      InheritedNoInit, InheritedNoArgs,
                                      ClassicInheritedNoInit,
                                      ClassicInheritedNoArgs])
def test_arginfo_no_args(callable):
    info = arginfo(callable)
    assert info.args == []
    assert info.varargs is None
    assert info.keywords is None
    assert info.defaults is None


def func_args(a):
    pass


class ObjArgs(object):
    def __call__(self, a):
        pass


obj_args = ObjArgs()


class MethodArgs(object):
    def method(self, a):
        pass


method_args = MethodArgs()


class StaticMethodArgs(object):
    @staticmethod
    def method(a):
        pass


class ClassMethodArgs(object):
    @classmethod
    def method(cls, a):
        pass


class ClassArgs(object):
    def __init__(self, a):
        pass


class ClassicArgs:
    def __init__(self, a):
        pass


class InheritedArgs(ClassArgs):
    pass


class ClassicInheritedArgs(ClassicArgs):
    pass


@pytest.mark.parametrize("callable", [func_args, obj_args, method_args.method,
                                      StaticMethodArgs.method,
                                      ClassMethodArgs.method,
                                      ClassArgs, ClassicArgs, InheritedArgs,
                                      ClassicInheritedArgs])
def test_arginfo_args(callable):
    info = arginfo(callable)
    assert info.args == ['a']
    assert info.varargs is None
    assert info.keywords is None
    assert info.defaults is None


def func_varargs(*args):
    pass


class ObjVarargs(object):
    def __call__(self, *args):
        pass


obj_varargs = ObjVarargs()


class MethodVarargs(object):
    def method(self, *args):
        pass


method_varargs = MethodVarargs()


class ClassVarargs(object):
    def __init__(self, *args):
        pass


class ClassicVarargs:
    def __init__(self, *args):
        pass


class InheritedVarargs(ClassVarargs):
    pass


class ClassicInheritedVarargs(ClassicVarargs):
    pass


@pytest.mark.parametrize("callable", [func_varargs, obj_varargs,
                                      method_varargs.method,
                                      ClassVarargs, ClassicVarargs,
                                      InheritedVarargs,
                                      ClassicInheritedVarargs])
def test_arginfo_varargs(callable):
    info = arginfo(callable)
    assert info.args == []
    assert info.varargs == 'args'
    assert info.keywords is None
    assert info.defaults is None


def func_keywords(**kw):
    pass


class ObjKeywords(object):
    def __call__(self, **kw):
        pass


obj_keywords = ObjKeywords()


class MethodKeywords(object):
    def method(self, **kw):
        pass


method_keywords = MethodKeywords()


class ClassKeywords(object):
    def __init__(self, **kw):
        pass


class ClassicKeywords:
    def __init__(self, **kw):
        pass


class InheritedKeywords(ClassKeywords):
    pass


class ClassicInheritedKeywords(ClassicKeywords):
    pass


@pytest.mark.parametrize("callable", [func_keywords, obj_keywords,
                                      method_keywords.method,
                                      ClassKeywords, ClassicKeywords,
                                      InheritedKeywords,
                                      ClassicInheritedKeywords])
def test_arginfo_keywords(callable):
    info = arginfo(callable)
    assert info.args == []
    assert info.varargs is None
    assert info.keywords == 'kw'
    assert info.defaults is None


def func_defaults(a=1):
    pass


class ObjDefaults(object):
    def __call__(self, a=1):
        pass


obj_defaults = ObjDefaults()


class MethodDefaults(object):
    def method(self, a=1):
        pass


method_defaults = MethodDefaults()


class ClassDefaults(object):
    def __init__(self, a=1):
        pass


class ClassicDefaults:
    def __init__(self, a=1):
        pass


class InheritedDefaults(ClassDefaults):
    pass


class ClassicInheritedDefaults(ClassicDefaults):
    pass


@pytest.mark.parametrize("callable", [func_defaults, obj_defaults,
                                      method_defaults.method,
                                      ClassDefaults, ClassicDefaults,
                                      InheritedDefaults,
                                      ClassicInheritedDefaults])
def test_arginfo_defaults(callable):
    info = arginfo(callable)
    assert info.args == ['a']
    assert info.varargs is None
    assert info.keywords is None
    assert info.defaults == (1,)


# Information on builtin functions is not reported. These can
# still be called with mapply, but only using positional arguments.
def test_arginfo_builtin():
    info = arginfo(int)
    assert info.args == []
    assert info.varargs is None
    assert info.keywords is None
    assert info.defaults is None


def test_arginfo_cache():
    def foo(a):
        pass

    assert not arginfo.is_cached(foo)
    arginfo(foo)
    assert arginfo.is_cached(foo)


def test_arginfo_cache_callable():
    class Foo(object):
        def __call__(self):
            pass

    foo = Foo()
    assert not arginfo.is_cached(foo)
    arginfo(foo)
    assert arginfo.is_cached(foo)
