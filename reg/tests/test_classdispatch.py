from __future__ import annotations

from typing import Any
from ..dispatch import dispatch
from ..predicate import match_class


class DemoClass:
    pass


class SpecialClass:
    pass


class Foo:
    def __repr__(self) -> str:
        return "<instance of Foo>"


class Bar:
    def __repr__(self) -> str:
        return "<instance of Bar>"


def test_dispatch_basic() -> None:
    @dispatch(match_class("cls"))
    def something(cls: type[Any]) -> str:
        raise NotImplementedError()

    def something_for_object(cls: type[object]) -> str:
        return "Something for %s" % cls

    something.register(something_for_object, cls=object)

    assert something(DemoClass) == (f"Something for <class '{__name__}.DemoClass'>")

    assert something.by_args(DemoClass).component is something_for_object
    assert something.by_args(DemoClass).all_matches == [something_for_object]


def test_classdispatch_multidispatch() -> None:
    @dispatch(match_class("cls"), "other")
    def something(cls: type[Any], other: Any) -> str:
        raise NotImplementedError()

    def something_for_object_and_object(cls: type[object], other: object) -> str:
        return "Something, other is object: %s" % other

    def something_for_object_and_foo(cls: type[object], other: Foo) -> str:
        return "Something, other is Foo: %s" % other

    something.register(something_for_object_and_object, cls=object, other=object)

    something.register(something_for_object_and_foo, cls=object, other=Foo)

    assert something(DemoClass, Bar()) == (
        "Something, other is object: <instance of Bar>"
    )
    assert something(DemoClass, Foo()) == ("Something, other is Foo: <instance of Foo>")


def test_classdispatch_extra_arguments() -> None:
    @dispatch(match_class("cls"))
    def something(cls: type[Any], extra: str) -> str:
        raise NotImplementedError()

    def something_for_object(cls: type[object], extra: str) -> str:
        return "Extra: %s" % extra

    something.register(something_for_object, cls=object)

    assert something(DemoClass, "foo") == "Extra: foo"


def test_classdispatch_no_arguments() -> None:
    @dispatch()
    def something() -> str:
        raise NotImplementedError()

    def something_impl() -> str:
        return "Something!"

    something.register(something_impl)

    assert something() == "Something!"


def test_classdispatch_override() -> None:
    @dispatch(match_class("cls"))
    def something(cls: type[Any]) -> str:
        raise NotImplementedError()

    def something_for_object(cls: type[object]) -> str:
        return "Something for %s" % cls

    def something_for_special(cls: type[SpecialClass]) -> str:
        return "Special for %s" % cls

    something.register(something_for_object, cls=object)
    something.register(something_for_special, cls=SpecialClass)

    assert something(SpecialClass) == (f"Special for <class '{__name__}.SpecialClass'>")


def test_classdispatch_fallback() -> None:
    @dispatch()
    def something(cls: type[Any]) -> str:
        return "Fallback"

    assert something(DemoClass) == "Fallback"
