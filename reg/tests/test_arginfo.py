from __future__ import annotations

import pytest
from typing import TYPE_CHECKING, Any
from typing_extensions import assert_type
from ..arginfo import arginfo

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import FullArgSpec  # noqa: F401
    from ..types import ArgInfo  # noqa: F401


def test_arginfo_typing() -> None:
    assert_type(arginfo, "ArgInfo")
    assert_type(arginfo(lambda: None), "FullArgSpec | None")


def func_no_args() -> None:
    pass


class ObjNoArgs:
    def __call__(self) -> None:
        pass


obj_no_args = ObjNoArgs()


class MethodNoArgs:
    def method(self) -> None:
        pass


method_no_args = MethodNoArgs()


class StaticMethodNoArgs:
    @staticmethod
    def method() -> None:
        pass


class ClassMethodNoArgs:
    @classmethod
    def method(cls) -> None:
        pass


class ClassNoInit:
    pass


class ClassNoArgs:
    def __init__(self) -> None:
        pass


class ClassicNoInit:
    pass


class ClassicNoArgs:
    def __init__(self) -> None:
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
def test_arginfo_no_args(callable: Callable[[], Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert info.args == []
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None


def func_args(a: int) -> None:
    pass


class ObjArgs:
    def __call__(self, a: int) -> None:
        pass


obj_args = ObjArgs()


class MethodArgs:
    def method(self, a: int) -> None:
        pass


method_args = MethodArgs()


class StaticMethodArgs:
    @staticmethod
    def method(a: int) -> None:
        pass


class ClassMethodArgs:
    @classmethod
    def method(cls, a: int) -> None:
        pass


class ClassArgs:
    def __init__(self, a: int) -> None:
        pass


class ClassicArgs:
    def __init__(self, a: int) -> None:
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
def test_arginfo_args(callable: Callable[[int], Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert info.args == ["a"]
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None


def func_varargs(*args: int) -> None:
    pass


class ObjVarargs:
    def __call__(self, *args: int) -> None:
        pass


obj_varargs = ObjVarargs()


class MethodVarargs:
    def method(self, *args: int) -> None:
        pass


method_varargs = MethodVarargs()


class ClassVarargs:
    def __init__(self, *args: int) -> None:
        pass


class ClassicVarargs:
    def __init__(self, *args: int) -> None:
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
def test_arginfo_varargs(callable: Callable[..., Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert info.args == []
    assert info.varargs == "args"
    assert info.varkw is None
    assert info.defaults is None


def func_keywords(**kw: int) -> None:
    pass


class ObjKeywords:
    def __call__(self, **kw: int) -> None:
        pass


obj_keywords = ObjKeywords()


class MethodKeywords:
    def method(self, **kw: int) -> None:
        pass


method_keywords = MethodKeywords()


class ClassKeywords:
    def __init__(self, **kw: int) -> None:
        pass


class ClassicKeywords:
    def __init__(self, **kw: int) -> None:
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
def test_arginfo_keywords(callable: Callable[..., Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert info.args == []
    assert info.varargs is None
    assert info.varkw == "kw"
    assert info.defaults is None


def func_defaults(a: int = 1) -> None:
    pass


class ObjDefaults:
    def __call__(self, a: int = 1) -> None:
        pass


obj_defaults = ObjDefaults()


class MethodDefaults:
    def method(self, a: int = 1) -> None:
        pass


method_defaults = MethodDefaults()


class ClassDefaults:
    def __init__(self, a: int = 1) -> None:
        pass


class ClassicDefaults:
    def __init__(self, a: int = 1) -> None:
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
def test_arginfo_defaults(callable: Callable[[int], Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert info.args == ["a"]
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults == (1,)


def func_kwonlydefaults(*, a: int = 1) -> None:
    pass


class ObjKwOnlyDefaults:
    def __call__(self, *, a: int = 1) -> None:
        pass


obj_kwonlydefaults = ObjKwOnlyDefaults()


class MethodKwOnlyDefaults:
    def method(self, *, a: int = 1) -> None:
        pass


method_kwonlydefaults = MethodKwOnlyDefaults()


class ClassKwOnlyDefaults:
    def __init__(self, *, a: int = 1) -> None:
        pass


class InheritedKwOnlyDefaults(ClassKwOnlyDefaults):
    pass


@pytest.mark.parametrize(
    "callable",
    [
        func_kwonlydefaults,
        obj_kwonlydefaults,
        method_kwonlydefaults.method,
        ClassKwOnlyDefaults,
        InheritedKwOnlyDefaults,
    ],
)
def test_arginfo_kwonlydefaults(callable: Callable[..., Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert not info.args
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None
    assert info.kwonlyargs == ["a"]
    assert info.kwonlydefaults == {"a": 1}


def func_annotations(a: int) -> None:
    pass


class ObjAnnotations:
    def __call__(self, a: int) -> None:
        pass


obj_annotations = ObjAnnotations()


class MethodAnnotations:
    def method(self, a: int) -> None:
        pass


method_annotations = MethodAnnotations()


class ClassAnnotations:
    def __init__(self, a: int) -> None:
        pass


class InheritedAnnotations(ClassAnnotations):
    pass


@pytest.mark.parametrize(
    "callable",
    [
        func_annotations,
        obj_annotations,
        method_annotations.method,
        ClassAnnotations,
        InheritedAnnotations,
    ],
)
def test_arginfo_annotations(callable: Callable[[int], Any]) -> None:
    info = arginfo(callable)
    assert info is not None
    assert info.args == ["a"]
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None
    assert info.annotations == {"a": "int", "return": "None"}


# Information on builtin functions is not reported. These can
# still be called with mapply, but only using positional arguments.
def test_arginfo_builtin() -> None:
    info = arginfo(int)
    assert info is not None
    assert info.args == []
    assert info.varargs is None
    assert info.varkw is None
    assert info.defaults is None


def test_arginfo_cache() -> None:
    def foo(a: object) -> None:
        pass

    assert not arginfo.is_cached(foo)
    arginfo(foo)
    assert arginfo.is_cached(foo)


def test_arginfo_cache_callable() -> None:
    class Foo:
        def __call__(self) -> None:
            pass

    foo = Foo()
    assert not arginfo.is_cached(foo)
    arginfo(foo)
    assert arginfo.is_cached(foo)
