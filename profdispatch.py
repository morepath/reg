from __future__ import annotations

from cProfile import run
from typing import TYPE_CHECKING, Any

from reg import LruCachingKeyLookup, dispatch

if TYPE_CHECKING:
    from reg.predicate import PredicateRegistry


def get_key_lookup(r: PredicateRegistry[Any]) -> LruCachingKeyLookup[Any]:
    return LruCachingKeyLookup(
        r,
        component_cache_size=5000,
        all_cache_size=5000,
        fallback_cache_size=5000,
    )


@dispatch(get_key_lookup=get_key_lookup)
def args0() -> str:
    raise NotImplementedError()


@dispatch("a", get_key_lookup=get_key_lookup)
def args1(a: Foo) -> str:
    raise NotImplementedError()


@dispatch("a", "b", get_key_lookup=get_key_lookup)
def args2(a: Foo, b: Foo) -> str:
    raise NotImplementedError()


@dispatch("a", "b", "c", get_key_lookup=get_key_lookup)
def args3(a: Foo, b: Foo, c: Foo) -> str:
    raise NotImplementedError()


@dispatch("a", "b", "c", "d", get_key_lookup=get_key_lookup)
def args4(a: Foo, b: Foo, c: Foo, d: Foo) -> str:
    raise NotImplementedError()


class Foo:
    pass


def myargs0() -> str:
    return "args0"


def myargs1(a: Foo) -> str:
    return "args1"


def myargs2(a: Foo, b: Foo) -> str:
    return "args2"


def myargs3(a: Foo, b: Foo, c: Foo) -> str:
    return "args3"


def myargs4(a: Foo, b: Foo, c: Foo, d: Foo) -> str:
    return "args4"


args0.register(myargs0)
args1.register(myargs1, a=Foo)
args2.register(myargs2, a=Foo, b=Foo)
args3.register(myargs3, a=Foo, b=Foo, c=Foo)
args4.register(myargs4, a=Foo, b=Foo, c=Foo, d=Foo)


def repeat_args4() -> None:
    for _ in range(10000):
        args4(Foo(), Foo(), Foo(), Foo())


run("repeat_args4()", sort="tottime")
