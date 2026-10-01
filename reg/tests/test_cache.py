"""Tests for the caching key lookups in reg.cache.

These tests treat the caches as black boxes: a fake key lookup records every
call it receives, so we can assert how often the underlying functions were
really invoked. Nothing here depends on the cache implementation, only on
caching behavior.

The fake returns ``str`` values, so the lookups under test are typed as
``LruCachingKeyLookup[str]`` / ``DictCachingKeyLookup[str]``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from reg.cache import DictCachingKeyLookup, LruCachingKeyLookup

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


class FakeKeyLookup:
    """Records every call so tests can see what reached the underlying lookup."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Sequence[Any]]] = []

    def component(self, key: Sequence[Any]) -> str | None:
        self.calls.append(("component", key))
        return f"component:{key}"

    def fallback(self, key: Sequence[Any]) -> str | None:
        self.calls.append(("fallback", key))
        return None  # None results must be cached too

    def all(self, key: Sequence[Any]) -> Iterator[str]:
        self.calls.append(("all", key))
        return iter([f"all:{key}"])  # an iterator; the cache must turn it into a list


def make(
    component: int = 10, all: int = 10, fallback: int = 10
) -> tuple[FakeKeyLookup, LruCachingKeyLookup[str]]:
    kl = FakeKeyLookup()
    return kl, LruCachingKeyLookup(kl, component, all, fallback)


# --- LruCachingKeyLookup: component ---------------------------------------


def test_component_result_is_returned() -> None:
    _kl, cached = make()
    assert cached.component(("a",)) == "component:('a',)"


def test_component_is_cached() -> None:
    kl, cached = make()
    cached.component(("a",))
    cached.component(("a",))
    assert kl.calls == [("component", ("a",))]


def test_component_different_keys_are_cached_separately() -> None:
    kl, cached = make()
    cached.component(("a",))
    cached.component(("b",))
    cached.component(("a",))
    cached.component(("b",))
    assert kl.calls == [("component", ("a",)), ("component", ("b",))]


# --- LruCachingKeyLookup: fallback ----------------------------------------


def test_fallback_is_cached() -> None:
    kl, cached = make()
    cached.fallback(("a",))
    cached.fallback(("a",))
    assert kl.calls == [("fallback", ("a",))]


def test_none_result_is_cached() -> None:
    kl, cached = make()
    assert cached.fallback(("a",)) is None
    assert cached.fallback(("a",)) is None
    assert len(kl.calls) == 1


# --- LruCachingKeyLookup: all ---------------------------------------------


def test_all_returns_a_list() -> None:
    _kl, cached = make()
    result = cached.all(("a",))
    assert isinstance(result, list)
    assert result == ["all:('a',)"]


def test_all_is_cached() -> None:
    kl, cached = make()
    first = cached.all(("a",))
    second = cached.all(("a",))
    assert len(kl.calls) == 1
    assert first == second


# --- LruCachingKeyLookup: independence ------------------------------------


def test_same_key_is_cached_per_method() -> None:
    kl, cached = make()
    cached.component(("a",))
    cached.fallback(("a",))
    cached.all(("a",))
    cached.component(("a",))
    cached.fallback(("a",))
    cached.all(("a",))
    assert kl.calls == [
        ("component", ("a",)),
        ("fallback", ("a",)),
        ("all", ("a",)),
    ]


def test_cache_sizes_are_independent() -> None:
    kl, cached = make(component=1, fallback=3)
    cached.component(("a",))
    cached.component(("b",))  # evicts "a" from the component cache only
    for k in ("a", "b", "c"):
        cached.fallback((k,))
    kl.calls.clear()

    cached.component(("a",))
    for k in ("a", "b", "c"):
        cached.fallback((k,))
    assert kl.calls == [("component", ("a",))]


# --- LruCachingKeyLookup: eviction ----------------------------------------


def test_component_least_recently_used_is_evicted() -> None:
    kl, cached = make(component=2)
    cached.component(("a",))
    cached.component(("b",))
    cached.component(("c",))  # evicts "a"
    kl.calls.clear()

    cached.component(("b",))  # still cached
    cached.component(("c",))  # still cached
    assert kl.calls == []

    cached.component(("a",))  # was evicted, recomputed
    assert kl.calls == [("component", ("a",))]


def test_component_recent_use_protects_from_eviction() -> None:
    kl, cached = make(component=2)
    cached.component(("a",))
    cached.component(("b",))
    cached.component(("a",))  # "b" is now the least recently used
    cached.component(("c",))  # evicts "b"
    kl.calls.clear()

    cached.component(("a",))
    assert kl.calls == []
    cached.component(("b",))
    assert kl.calls == [("component", ("b",))]


# --- DictCachingKeyLookup (unbounded) -------------------------------------


def test_dict_component_is_cached() -> None:
    kl = FakeKeyLookup()
    cached: DictCachingKeyLookup[str] = DictCachingKeyLookup(kl)
    assert cached.component(("a",)) == "component:('a',)"
    cached.component(("a",))
    assert kl.calls == [("component", ("a",))]


def test_dict_fallback_caches_none() -> None:
    kl = FakeKeyLookup()
    cached: DictCachingKeyLookup[str] = DictCachingKeyLookup(kl)
    assert cached.fallback(("a",)) is None
    assert cached.fallback(("a",)) is None
    assert kl.calls == [("fallback", ("a",))]


def test_dict_all_returns_list_and_is_cached() -> None:
    kl = FakeKeyLookup()
    cached: DictCachingKeyLookup[str] = DictCachingKeyLookup(kl)
    assert cached.all(("a",)) == ["all:('a',)"]
    cached.all(("a",))
    assert kl.calls == [("all", ("a",))]
