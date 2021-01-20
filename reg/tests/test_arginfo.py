import pytest
from ..arginfo import arginfo


def func_no_args():
    pass


class ObjNoArgs:
    def __call__(self):
        pass


obj_no_args = ObjNoArgs()


class MethodNoArgs:
    def method(self):
        pass


method_no_args = MethodNoArgs()


class StaticMethodNoArgs:
    @staticmethod
    def method():
        pass


class ClassMethodNoArgs:
    @classmethod
    def method(cls):
        pass


class ClassNoInit:
    pass


class ClassNoArgs:
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


@pytest.mark.parametrize(
    "callable",
    [
        func_no_args,
        obj_no_args,
        method_no_args.method,
        StaticMethodNoArgs.method,
        ClassMethodNoArgs.method,
        ClassNoInit,
        ClassNoArgs,
        ClassicNoInit,
        ClassicNoArgs,
        InheritedNoInit,
        InheritedNoArgs,
        ClassicInheritedNoInit,
        ClassicInheritedNoArgs,
    ],
)
def test_arginfo_no_args(callable):
    info = arginfo(callable)
    assert info.args == []
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None


def func_args(a):
    pass


class ObjArgs:
    def __call__(self, a):
        pass


obj_args = ObjArgs()


class MethodArgs:
    def method(self, a):
        pass


method_args = MethodArgs()


class StaticMethodArgs:
    @staticmethod
    def method(a):
        pass


class ClassMethodArgs:
    @classmethod
    def method(cls, a):
        pass


class ClassArgs:
    def __init__(self, a):
        pass


class ClassicArgs:
    def __init__(self, a):
        pass


class InheritedArgs(ClassArgs):
    pass


class ClassicInheritedArgs(ClassicArgs):
    pass


@pytest.mark.parametrize(
    "callable",
    [
        func_args,
        obj_args,
        method_args.method,
        StaticMethodArgs.method,
        ClassMethodArgs.method,
        ClassArgs,
        ClassicArgs,
        InheritedArgs,
        ClassicInheritedArgs,
    ],
)
def test_arginfo_args(callable):
    info = arginfo(callable)
    assert info.args == ["a"]
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None


def func_varargs(*args):
    pass


class ObjVarargs:
    def __call__(self, *args):
        pass


obj_varargs = ObjVarargs()


class MethodVarargs:
    def method(self, *args):
        pass


method_varargs = MethodVarargs()


class ClassVarargs:
    def __init__(self, *args):
        pass


class ClassicVarargs:
    def __init__(self, *args):
        pass


class InheritedVarargs(ClassVarargs):
    pass


class ClassicInheritedVarargs(ClassicVarargs):
    pass


@pytest.mark.parametrize(
    "callable",
    [
        func_varargs,
        obj_varargs,
        method_varargs.method,
        ClassVarargs,
        ClassicVarargs,
        InheritedVarargs,
        ClassicInheritedVarargs,
    ],
)
def test_arginfo_varargs(callable):
    info = arginfo(callable)
    assert info.args == []
    assert info.varargs == "args"
    assert info.varkw is None
    assert info.defaults is None


def func_keywords(**kw):
    pass


class ObjKeywords:
    def __call__(self, **kw):
        pass


obj_keywords = ObjKeywords()


class MethodKeywords:
    def method(self, **kw):
        pass


method_keywords = MethodKeywords()


class ClassKeywords:
    def __init__(self, **kw):
        pass


class ClassicKeywords:
    def __init__(self, **kw):
        pass


class InheritedKeywords(ClassKeywords):
    pass


class ClassicInheritedKeywords(ClassicKeywords):
    pass


@pytest.mark.parametrize(
    "callable",
    [
        func_keywords,
        obj_keywords,
        method_keywords.method,
        ClassKeywords,
        ClassicKeywords,
        InheritedKeywords,
        ClassicInheritedKeywords,
    ],
)
def test_arginfo_keywords(callable):
    info = arginfo(callable)
    assert info.args == []
    assert info.varargs is None
    assert info.varkw == "kw"
    assert info.defaults is None


def func_defaults(a=1):
    pass


class ObjDefaults:
    def __call__(self, a=1):
        pass


obj_defaults = ObjDefaults()


class MethodDefaults:
    def method(self, a=1):
        pass


method_defaults = MethodDefaults()


class ClassDefaults:
    def __init__(self, a=1):
        pass


class ClassicDefaults:
    def __init__(self, a=1):
        pass


class InheritedDefaults(ClassDefaults):
    pass


class ClassicInheritedDefaults(ClassicDefaults):
    pass


@pytest.mark.parametrize(
    "callable",
    [
        func_defaults,
        obj_defaults,
        method_defaults.method,
        ClassDefaults,
        ClassicDefaults,
        InheritedDefaults,
        ClassicInheritedDefaults,
    ],
)
def test_arginfo_defaults(callable):
    info = arginfo(callable)
    assert info.args == ["a"]
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults == (1,)


# Information on builtin functions is not reported. These can
# still be called with mapply, but only using positional arguments.
def test_arginfo_builtin():
    info = arginfo(int)
    assert info.args == []
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None


def test_arginfo_cache():
    def foo(a):
        pass

    assert not arginfo.is_cached(foo)
    arginfo(foo)
    assert arginfo.is_cached(foo)


def test_arginfo_cache_callable():
    class Foo:
        def __call__(self):
            pass

    foo = Foo()
    assert not arginfo.is_cached(foo)
    arginfo(foo)
    assert arginfo.is_cached(foo)
