from __future__ import annotations

import pytest

from typing import TYPE_CHECKING, Any
from typing_extensions import assert_type
from ..predicate import match_instance, match_key, match_class
from ..dispatch import dispatch
from ..error import RegistrationError

if TYPE_CHECKING:
    from ..types import DispatchCall  # noqa: F401


class IAlpha:
    pass


class Alpha(IAlpha):
    pass


class IBeta:
    pass


class Beta(IBeta):
    pass


def test_dispatch_typing() -> None:
    @dispatch()
    def foo() -> str | None:
        pass

    @dispatch()
    def bar(x: str, /) -> None:
        pass

    @dispatch()
    def baz(a: str, b: int, /) -> Any:
        pass

    assert_type(foo, "DispatchCall[[], str | None]")
    assert_type(bar, "DispatchCall[[str], None]")
    assert_type(baz, "DispatchCall[[str, int], Any]")


def test_dispatch_argname() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> str | None:
        pass

    def for_bar(obj: Bar) -> str:
        return obj.method()

    def for_qux(obj: Qux) -> str:
        return obj.method()

    class Bar:
        def method(self) -> str:
            return "bar's method"

    class Qux:
        def method(self) -> str:
            return "qux's method"

    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"


def test_dispatch_match_instance() -> None:
    @dispatch(match_instance("obj"))
    def foo(obj: Any) -> str | None:
        pass

    def for_bar(obj: Bar) -> str:
        return obj.method()

    def for_qux(obj: Qux) -> str:
        return obj.method()

    class Bar:
        def method(self) -> str:
            return "bar's method"

    class Qux:
        def method(self) -> str:
            return "qux's method"

    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"


def test_dispatch_no_arguments() -> None:
    @dispatch()
    def foo() -> str | None:
        pass

    def special_foo() -> str:
        return "special"

    foo.register(special_foo)

    assert foo.by_args().component is special_foo
    assert foo.by_args().all_matches == [special_foo]
    assert foo() == "special"
    assert foo.by_args().fallback is None


def test_all() -> None:
    class Base:
        pass

    class Sub(Base):
        pass

    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    def registered_for_sub(obj: Sub) -> None:
        pass

    def registered_for_base(obj: Base) -> None:
        pass

    target.register(registered_for_sub, obj=Sub)
    target.register(registered_for_base, obj=Base)

    base = Base()
    sub = Sub()

    assert target.by_args(sub).all_matches == [
        registered_for_sub,
        registered_for_base,
    ]
    assert target.by_args(base).all_matches == [registered_for_base]


def test_all_by_keys() -> None:
    class Base:
        pass

    class Sub(Base):
        pass

    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    def registered_for_sub(obj: Sub) -> None:
        pass

    def registered_for_base(obj: Base) -> None:
        pass

    target.register(registered_for_sub, obj=Sub)
    target.register(registered_for_base, obj=Base)

    assert target.by_predicates(obj=Sub).all_matches == [
        registered_for_sub,
        registered_for_base,
    ]
    assert target.by_predicates(obj=Base).all_matches == [registered_for_base]


def test_component_no_source() -> None:
    @dispatch()
    def target() -> None:
        pass

    def foo() -> None:
        pass

    target.register(foo)
    assert target.by_args().component is foo


def test_component_no_source_key_dict() -> None:
    @dispatch()
    def target() -> None:
        pass

    def foo() -> None:
        pass

    target.register(foo)
    assert target.by_predicates().component is foo


def test_component_one_source() -> None:
    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    def foo(obj: Alpha) -> None:
        pass

    target.register(foo, obj=Alpha)

    alpha = Alpha()
    assert target.by_args(alpha).component is foo


def test_component_one_source_key_dict() -> None:
    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    def foo(obj: Alpha) -> None:
        pass

    target.register(foo, obj=Alpha)

    assert target.by_predicates(obj=Alpha).component is foo


def test_component_two_sources() -> None:
    @dispatch("a", "b")
    def target(a: Any, b: Any) -> None:
        pass

    def foo(a: IAlpha, b: IBeta) -> None:
        pass

    target.register(foo, a=IAlpha, b=IBeta)

    alpha = Alpha()
    beta = Beta()
    assert target.by_args(alpha, beta).component is foo


def test_component_inheritance() -> None:
    class Gamma:
        pass

    class Delta(Gamma):
        pass

    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    def foo(obj: Gamma) -> None:
        pass

    target.register(foo, obj=Gamma)

    delta = Delta()

    assert target.by_args(delta).component is foo


def test_component_inheritance_old_style_class() -> None:
    class Gamma:
        pass

    class Delta(Gamma):
        pass

    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    def foo(obj: Gamma) -> None:
        pass

    target.register(foo, obj=Gamma)

    gamma = Gamma()
    delta = Delta()

    assert target.by_args(gamma).component is foo

    # inheritance case
    assert target.by_args(delta).component is foo


def test_call_no_source() -> None:
    foo = object()

    @dispatch()
    def target() -> object:
        pass

    def factory() -> object:
        return foo

    target.register(factory)

    assert target() is foo


def test_call_one_source() -> None:
    @dispatch("obj")
    def target(obj: Any) -> str | None:
        pass

    def foo(obj: IAlpha) -> str:
        return "foo"

    def bar(obj: IBeta) -> str:
        return "bar"

    target.register(foo, obj=IAlpha)
    target.register(bar, obj=IBeta)

    assert target(Alpha()) == "foo"
    assert target(Beta()) == "bar"


def test_call_two_sources() -> None:
    @dispatch("a", "b")
    def target(a: Any, b: Any) -> str | None:
        pass

    def foo(a: IAlpha, b: IBeta) -> str:
        return "foo"

    def bar(a: IBeta, b: IAlpha) -> str:
        return "bar"

    target.register(foo, a=IAlpha, b=IBeta)
    target.register(bar, a=IBeta, b=IAlpha)
    alpha = Alpha()
    beta = Beta()

    assert target(alpha, beta) == "foo"
    assert target(beta, alpha) == "bar"


def test_component_not_found_no_sources() -> None:
    @dispatch()
    def target() -> None:
        pass

    assert target.by_args().component is None


def test_call_not_found_no_sources() -> None:
    @dispatch()
    def target() -> str:
        return "default"

    assert target() == "default"


def test_component_not_found_one_source() -> None:
    @dispatch("obj")
    def target(obj: str) -> None:
        pass

    assert target.by_args("dummy").component is None


def test_call_not_found_one_source() -> None:
    @dispatch("obj")
    def target(obj: str) -> str:
        return "default: %s" % obj

    assert target("dummy") == "default: dummy"


def test_component_not_found_two_sources() -> None:
    @dispatch("a", "b")
    def target(a: str, b: str) -> None:
        pass

    assert target.by_args("dummy", "dummy").component is None


def test_call_not_found_two_sources() -> None:
    @dispatch("a", "b")
    def target(a: str, b: str) -> str:
        return f"a: {a} b: {b}"

    assert target("dummy1", "dummy2") == "a: dummy1 b: dummy2"


def test_wrong_callable_registered() -> None:
    @dispatch("obj")
    def target(obj: Any) -> Any:
        pass

    def callable(a: Any, b: Any) -> Any:
        pass

    with pytest.raises(RegistrationError):
        target.register(callable, a=Alpha)  # type: ignore


def test_non_callable_registered() -> None:
    @dispatch("obj")
    def target(obj: Any) -> None:
        pass

    non_callable = 42

    with pytest.raises(RegistrationError):
        target.register(non_callable, a=Alpha)  # type: ignore


def test_call_with_no_args_while_arg_expected() -> None:
    @dispatch("obj")
    def target(obj: Any) -> str | None:
        pass

    def specific(obj: Alpha) -> str:
        return "specific"

    target.register(specific, obj=Alpha)

    # we are not allowed to call target without arguments
    with pytest.raises(TypeError):
        target()  # type: ignore

    with pytest.raises(TypeError):
        target.by_args().component  # type: ignore


def test_call_with_wrong_args() -> None:
    @dispatch("obj")
    def target(obj: Any) -> str | None:
        pass

    def specific(obj: Alpha) -> str:
        return "specific"

    target.register(specific, obj=Alpha)

    # we are not allowed to call target without arguments
    with pytest.raises(TypeError):
        target(wrong=1)  # type: ignore

    with pytest.raises(TypeError):
        target.by_args(wrong=1)  # type: ignore


def test_extra_arg_for_call() -> None:
    @dispatch("obj")
    def target(obj: Any, extra: str) -> str:
        return "General: %s" % extra

    def specific(obj: Alpha, extra: str) -> str:
        return "Specific: %s" % extra

    target.register(specific, obj=Alpha)

    alpha = Alpha()
    beta = Beta()

    assert target(alpha, extra="allowed") == "Specific: allowed"
    assert target(beta, extra="allowed") == "General: allowed"
    assert target(alpha, "allowed") == "Specific: allowed"
    assert target(beta, "allowed") == "General: allowed"


def test_fallback_to_fallback() -> None:
    def fallback(obj: Any) -> str:
        return "fallback!"

    @dispatch(match_instance("obj", fallback=fallback))
    def target(obj: Any) -> str:
        return "not the fallback we want"

    def specific_target(obj: Alpha) -> str:
        return "specific"

    target.register(specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta) == "fallback!"
    # this is *not* a registered fallback so won't be returned here
    assert target.by_args(beta).fallback is fallback
    # we cannot find a fallback for alpha, as it doesn't hit the fallback
    assert target(Alpha()) == "specific"
    assert target.by_args(Alpha()).fallback is None


def test_fallback_to_dispatch() -> None:
    @dispatch("obj")
    def target(obj: Any) -> str:
        return "fallback"

    def specific_target(obj: Alpha) -> str:
        return "specific"

    target.register(specific_target, obj=Alpha)

    beta = Beta()
    assert target(beta) == "fallback"
    # this is *not* a registered fallback so won't be returned here
    assert target.by_args(beta).fallback is None


def test_calling_twice() -> None:
    @dispatch("obj")
    def target(obj: Any) -> str:
        return "fallback"

    def a(obj: Alpha) -> str:
        return "a"

    def b(obj: Beta) -> str:
        return "b"

    target.register(a, obj=Alpha)
    target.register(b, obj=Beta)

    assert target(Alpha()) == "a"
    assert target(Beta()) == "b"


def test_different_defaults_in_specific_non_dispatch_arg() -> None:
    @dispatch("obj")
    def target(obj: Any, blah: str = "default") -> str:
        return "fallback: %s" % blah

    def a(obj: Any, blah: str = "default 2") -> str:
        return "a: %s" % blah

    target.register(a, obj=Alpha)

    assert target(Alpha()) == "a: default"


def test_different_defaults_in_specific_dispatch_arg() -> None:
    @dispatch(match_key("key"))
    def target(key: str = "default") -> str:
        return "fallback: %s" % key

    def a(key: str = "default 2") -> str:
        return "a: %s" % key

    target.register(a, key="foo")

    assert target("foo") == "a: foo"
    assert target("bar") == "fallback: bar"
    assert target() == "fallback: default"


def test_different_defaults_in_specific_dispatch_arg_causes_dispatch() -> None:
    @dispatch(match_key("key"))
    def target(key: str = "foo") -> str:
        return "fallback: %s" % key

    def a(key: str = "default 2") -> str:
        return "a: %s" % key

    target.register(a, key="foo")

    assert target("foo") == "a: foo"
    assert target("bar") == "fallback: bar"
    assert target() == "a: foo"


def test_add_predicates_no_defaults() -> None:
    class Foo:
        pass

    class FooSub(Foo):
        pass

    class Request:
        def __init__(self, name: str, request_method: str) -> None:
            self.name = name
            self.request_method = request_method

    @dispatch()
    def view(self: Any, request: Request) -> str:
        raise NotImplementedError()

    def get_model(self: Any, request: Request) -> Any:
        return self

    def get_name(self: Any, request: Request) -> str:
        return request.name

    def get_request_method(self: Any, request: Request) -> str:
        return request.request_method

    def model_fallback(self: Any, request: Request) -> Any:
        return "Model fallback"

    def name_fallback(self: Any, request: Request) -> str:
        return "Name fallback"

    def request_method_fallback(self: Any, request: Request) -> str:
        return "Request method fallback"

    view.add_predicates(
        [
            match_instance("model", get_model, model_fallback),
            match_key("name", get_name, name_fallback),
            match_key("request_method", get_request_method, request_method_fallback),
        ]
    )

    def foo_default(self: Foo, request: Request) -> str:
        return "foo default"

    def foo_post(self: Foo, request: Request) -> str:
        return "foo default post"

    def foo_edit(self: Foo, request: Request) -> str:
        return "foo edit"

    view.register(foo_default, model=Foo, name="", request_method="GET")
    view.register(foo_post, model=Foo, name="", request_method="POST")
    view.register(foo_edit, model=Foo, name="edit", request_method="POST")

    assert view(Foo(), Request("", "GET")) == "foo default"
    assert view(FooSub(), Request("", "GET")) == "foo default"
    assert view(FooSub(), Request("edit", "POST")) == "foo edit"

    class Bar:
        pass

    assert view(Bar(), Request("", "GET")) == "Model fallback"
    assert view(Foo(), Request("dummy", "GET")) == "Name fallback"
    assert view(Foo(), Request("", "PUT")) == "Request method fallback"
    assert view(FooSub(), Request("dummy", "GET")) == "Name fallback"


def test_dispatch_external_predicates() -> None:
    class Foo:
        pass

    class FooSub(Foo):
        pass

    class Request:
        def __init__(self, name: str, request_method: str) -> None:
            self.name = name
            self.request_method = request_method

    @dispatch()
    def view(self: Any, request: Request) -> str:
        raise NotImplementedError()

    def get_model(self: Any, request: Request) -> Any:
        return self

    def get_name(self: Any, request: Request) -> str:
        return request.name

    def get_request_method(self: Any, request: Request) -> str:
        return request.request_method

    def model_fallback(self: Any, request: Request) -> str:
        return "Model fallback"

    def name_fallback(self: Any, request: Request) -> str:
        return "Name fallback"

    def request_method_fallback(self: Any, request: Request) -> str:
        return "Request method fallback"

    view.add_predicates(
        [
            match_instance("model", get_model, model_fallback),
            match_key("name", get_name, name_fallback),
            match_key("request_method", get_request_method, request_method_fallback),
        ]
    )

    def foo_default(self: Foo, request: Request) -> str:
        return "foo default"

    def foo_post(self: Foo, request: Request) -> str:
        return "foo default post"

    def foo_edit(self: Foo, request: Request) -> str:
        return "foo edit"

    view.register(foo_default, model=Foo, name="", request_method="GET")
    view.register(foo_post, model=Foo, name="", request_method="POST")
    view.register(foo_edit, model=Foo, name="edit", request_method="POST")

    assert view(Foo(), Request("", "GET")) == "foo default"
    assert view(FooSub(), Request("", "GET")) == "foo default"
    assert view(FooSub(), Request("edit", "POST")) == "foo edit"

    class Bar:
        pass

    assert view(Bar(), Request("", "GET")) == "Model fallback"
    assert view(Foo(), Request("dummy", "GET")) == "Name fallback"
    assert view(Foo(), Request("", "PUT")) == "Request method fallback"
    assert view(FooSub(), Request("dummy", "GET")) == "Name fallback"
    assert view.by_args(Bar(), Request("", "GET")).fallback is model_fallback


def test_dispatch_predicates_register_defaults() -> None:
    class Foo:
        pass

    class FooSub(Foo):
        pass

    class Request:
        def __init__(self, name: str, request_method: str) -> None:
            self.name = name
            self.request_method = request_method

    @dispatch()
    def view(self: Any, request: Request) -> str:
        raise NotImplementedError()

    def get_model(self: Any, request: Request) -> Any:
        return self

    def get_name(self: Any, request: Request) -> str:
        return request.name

    def get_request_method(self: Any, request: Request) -> str:
        return request.request_method

    def model_fallback(self: Any, request: Request) -> Any:
        return "Model fallback"

    def name_fallback(self: Any, request: Request) -> str:
        return "Name fallback"

    def request_method_fallback(self: Any, request: Request) -> str:
        return "Request method fallback"

    view.add_predicates(
        [
            match_instance("model", get_model, model_fallback, default=None),
            match_key("name", get_name, name_fallback, default=""),
            match_key(
                "request_method",
                get_request_method,
                request_method_fallback,
                default="GET",
            ),
        ]
    )

    def foo_default(self: Foo, request: Request) -> str:
        return "foo default"

    def foo_post(self: Foo, request: Request) -> str:
        return "foo default post"

    def foo_edit(self: Foo, request: Request) -> str:
        return "foo edit"

    view.register(foo_default, model=Foo)
    view.register(foo_post, model=Foo, request_method="POST")
    view.register(foo_edit, model=Foo, name="edit", request_method="POST")

    assert view(Foo(), Request("", "GET")) == "foo default"
    assert view(FooSub(), Request("", "GET")) == "foo default"
    assert view(FooSub(), Request("edit", "POST")) == "foo edit"

    class Bar:
        pass

    assert view(Bar(), Request("", "GET")) == "Model fallback"
    assert view(Foo(), Request("dummy", "GET")) == "Name fallback"
    assert view(Foo(), Request("", "PUT")) == "Request method fallback"
    assert view(FooSub(), Request("dummy", "GET")) == "Name fallback"


def test_key_dict_to_predicate_key() -> None:
    @dispatch(
        match_key("foo", default="default foo"),
        match_key("bar", default="default bar"),
    )
    def view(self: Any, request: Any) -> Any:
        raise NotImplementedError()

    assert view.by_predicates(foo="FOO", bar="BAR").key == ("FOO", "BAR")
    assert view.by_predicates().key == ("default foo", "default bar")


def test_key_dict_to_predicate_key_unknown_keys() -> None:
    @dispatch(
        match_key("foo", default="default foo"),
        match_key("bar", default="default bar"),
    )
    def view(self: Any, request: Any) -> Any:
        raise NotImplementedError()

    # unknown keys are just ignored
    assert view.by_predicates(unknown="blah").key == (
        "default foo",
        "default bar",
    )


def test_register_dispatch_key_dict() -> None:
    class Foo:
        pass

    class FooSub(Foo):
        pass

    @dispatch()
    def view(self: Any, request: Any) -> Any:
        raise NotImplementedError()

    def get_model(self: Any, request: Any) -> Any:
        return self

    def get_name(self: Any, request: Any) -> Any:
        return request.name

    def get_request_method(self: Any, request: Any) -> Any:
        return request.request_method

    def model_fallback(self: Any, request: Any) -> Any:
        return "Model fallback"

    def name_fallback(self: Any, request: Any) -> Any:
        return "Name fallback"

    def request_method_fallback(self: Any, request: Any) -> Any:
        return "Request method fallback"

    view.add_predicates(
        [
            match_instance("model", get_model, model_fallback, default=None),
            match_key("name", get_name, name_fallback, default=""),
            match_key(
                "request_method",
                get_request_method,
                request_method_fallback,
                default="GET",
            ),
        ]
    )

    assert view.by_predicates().key == (None, "", "GET")


def test_fallback_should_already_use_subset() -> None:
    class Request:
        def __init__(self, name: str, request_method: str, body_obj: Any) -> None:
            self.name = name
            self.request_method = request_method
            self.body_obj = body_obj

    def get_model(self: Any, request: Request) -> Any:
        return self

    def get_name(self: Any, request: Request) -> str:
        return request.name

    def get_request_method(self: Any, request: Request) -> str:
        return request.request_method

    def get_body_model(self: Any, request: Request) -> Any:
        return request.body_obj.__class__

    def model_fallback(self: Any, request: Request) -> Any:
        return "Model fallback"

    def name_fallback(self: Any, request: Request) -> str:
        return "Name fallback"

    def request_method_fallback(self: Any, request: Request) -> str:
        return "Request method fallback"

    def body_model_fallback(self: Any, request: Request) -> Any:
        return "Body model fallback"

    @dispatch(
        match_instance("model", get_model, model_fallback, default=None),
        match_key("name", get_name, name_fallback, default=""),
        match_key(
            "request_method",
            get_request_method,
            request_method_fallback,
            default="GET",
        ),
        match_class("body_model", get_body_model, body_model_fallback, default=object),
    )
    def view(self: Any, request: Request) -> str:
        return "view fallback"

    def exception_view(self: Exception, request: Request) -> str:
        return "exception view"

    view.register(exception_view, model=Exception)

    class Collection:
        pass

    class Item:
        pass

    class Item2:
        pass

    def collection_add(self: Collection, request: Request) -> str:
        return "collection add"

    view.register(
        collection_add, model=Collection, request_method="POST", body_model=Item
    )

    assert (
        view.by_args(
            Collection(),
            Request("", "POST", Item2()),
        ).fallback
        is body_model_fallback
    )
    assert (
        view(
            Collection(),
            Request("", "POST", Item2()),
        )
        == "Body model fallback"
    )


def test_dispatch_missing_argument() -> None:
    @dispatch("obj")
    def foo(obj: object) -> Any:
        pass

    def for_bar(obj: object) -> Any:
        return "for bar"

    class Bar:
        pass

    foo.register(for_bar, obj=Bar)

    with pytest.raises(TypeError):
        assert foo()  # type: ignore


def test_register_dispatch_predicates_twice() -> None:
    @dispatch()
    def foo(a: Any, b: Any) -> Any:
        pass

    def for_bar(a: Any, b: Any) -> Any:
        return "for bar"

    def for_qux(a: Any, b: Any) -> Any:
        return "for qux"

    class Bar:
        pass

    class Qux:
        pass

    foo.add_predicates([match_instance("a")])
    # second time adds another one
    foo.add_predicates([match_instance("b")])
    foo.register(for_bar, a=Bar, b=Bar)
    foo.register(for_qux, a=Qux, b=Qux)
    assert foo(Bar(), Bar()) == "for bar"
    assert foo(Qux(), Qux()) == "for qux"


def test_dict_to_predicate_key_for_no_dispatch() -> None:
    @dispatch()
    def foo() -> None:
        pass

    assert foo.by_predicates().key == ()


def test_dispatch_clean() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> str:
        return "default"

    def for_bar(obj: Bar) -> str:
        return obj.method()

    def for_qux(obj: Qux) -> str:
        return obj.method()

    class Bar:
        def method(self) -> str:
            return "bar's method"

    class Qux:
        def method(self) -> str:
            return "qux's method"

    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"

    foo.clean()

    assert foo(Bar()) == "default"
    assert foo(Qux()) == "default"


def test_dispatch_clean_add_predicates() -> None:
    @dispatch()
    def foo(obj: Any) -> str:
        return "default"

    def for_bar(obj: Bar) -> str:
        return obj.method()

    def for_qux(obj: Qux) -> str:
        return obj.method()

    class Bar:
        def method(self) -> str:
            return "bar's method"

    class Qux:
        def method(self) -> str:
            return "qux's method"

    foo.add_predicates([match_instance("obj")])
    foo.register(for_bar, obj=Bar)
    foo.register(for_qux, obj=Qux)

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"

    foo.clean()

    foo.register(for_bar)

    # cannot register it for Qux, as this now has no predicates
    with pytest.raises(RegistrationError):
        foo.register(for_qux)


def test_dispatch_introspection() -> None:
    @dispatch("obj")
    def foo(obj: object) -> str:
        "return the foo of an object."
        return "default"

    assert foo.__name__ == "foo"
    assert foo.__doc__ == "return the foo of an object."
    assert foo.__module__ == __name__


def test_dispatch_argname_with_decorator() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> Any:
        pass

    class Bar:
        def method(self) -> str:
            return "bar's method"

    class Qux:
        def method(self) -> str:
            return "qux's method"

    @foo.register(obj=Bar)
    def for_bar(obj: Bar) -> str:
        return obj.method()

    @foo.register(obj=Qux)
    def for_qux(obj: Qux) -> str:
        return obj.method()

    assert foo(Bar()) == "bar's method"
    assert foo(Qux()) == "qux's method"

    assert foo(Bar()) == for_bar(Bar())
    assert foo(Qux()) == for_qux(Qux())


def test_component_lookup_before_call_and_no_registrations() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> Any:
        pass

    class Bar:
        pass

    assert foo.by_args(Bar()).component is None


def test_predicate_key_too_few_arguments_gives_typeerror() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> Any:
        pass

    def for_bar(obj: Any) -> Any:
        return obj.method()

    def for_qux(obj: Any) -> Any:
        return obj.method()

    with pytest.raises(TypeError):
        assert foo.by_args()  # type: ignore


def test_predicate_key_too_many_arguments_gives_typeerror() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> Any:
        pass

    def for_bar(obj: Any) -> Any:
        return obj.method()

    def for_qux(obj: Any) -> Any:
        return obj.method()

    with pytest.raises(TypeError):
        assert foo.by_args(1, 2)  # type: ignore


def test_predicate_key_wrong_keyword_argument_gives_typeerror() -> None:
    @dispatch("obj")
    def foo(obj: Any) -> Any:
        pass

    def for_bar(obj: Any) -> Any:
        return obj.method()

    def for_qux(obj: Any) -> Any:
        return obj.method()

    with pytest.raises(TypeError):
        assert foo.by_args(wrong=1)  # type: ignore
