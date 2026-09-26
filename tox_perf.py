from __future__ import annotations

import timeit
from typing import TYPE_CHECKING, Any

from reg import DictCachingKeyLookup, dispatch

if TYPE_CHECKING:
    from reg.predicate import PredicateRegistry


def get_key_lookup(r: PredicateRegistry[Any]) -> DictCachingKeyLookup[Any]:
    return DictCachingKeyLookup(r)


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


def docall0() -> None:
    args0()


def docall1() -> None:
    args1(Foo())


def docall2() -> None:
    args2(Foo(), Foo())


def docall3() -> None:
    args3(Foo(), Foo(), Foo())


def docall4() -> None:
    args4(Foo(), Foo(), Foo(), Foo())


def plain_docall0() -> None:
    myargs0()


def plain_docall4() -> None:
    myargs4(Foo(), Foo(), Foo(), Foo())


plain_zero_time = timeit.timeit(
    "plain_docall0()", setup="from __main__ import plain_docall0"
)

print("\nPerformance test")
print("================")

print("dispatch 0 args")
print(
    "{:.2f}".format(
        timeit.timeit("docall0()", setup="from __main__ import docall0")
        / plain_zero_time
    )
    + "x"
)

print("dispatch 1 args")
print(
    "{:.2f}".format(
        timeit.timeit("docall1()", setup="from __main__ import docall1")
        / plain_zero_time
    )
    + "x"
)

print("dispatch 2 args")
print(
    "{:.2f}".format(
        timeit.timeit("docall2()", setup="from __main__ import docall2")
        / plain_zero_time
    )
    + "x"
)

print("dispatch 3 args")
print(
    "{:.2f}".format(
        timeit.timeit("docall3()", setup="from __main__ import docall3")
        / plain_zero_time
    )
    + "x"
)

print("dispatch 4 args")
print(
    "{:.2f}".format(
        timeit.timeit("docall4()", setup="from __main__ import docall4")
        / plain_zero_time
    )
    + "x"
)

print("Plain func 0 args")
print("1.00x (base duration)")

print("Plain func 4 args")
print(
    "{:.2f}".format(
        timeit.timeit("plain_docall4()", setup="from __main__ import plain_docall4")
        / plain_zero_time
    )
    + "x"
)
