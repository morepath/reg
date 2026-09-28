from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from repoze.lru import lru_cache

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing_extensions import TypeVar

    from .types import KeyLookup

    _ValueT = TypeVar("_ValueT", default=Callable[..., Any])
else:
    from typing import TypeVar

    _ValueT = TypeVar("_ValueT")

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class Cache(dict[_KT, _VT]):
    """A dict to cache a function."""

    def __init__(self, func: Callable[[_KT], _VT]) -> None:
        self.func = func

    def __missing__(self, key: _KT) -> _VT:
        self[key] = result = self.func(key)
        return result


class DictCachingKeyLookup(Generic[_ValueT]):
    """A key lookup that caches.

    Implements the read-only API of :class:`reg.predicate.PredicateRegistry`
    using a cache to speed up access.

    This cache is backed by a simple dictionary so could potentially
    grow large if the dispatch in question can be called with a large
    combination of arguments that result in a large range of different
    predicate keys. If so, you can use
    :class:`reg.LruCachingKeyLookup` instead.

    :param: key_lookup - the :class:`reg.predicate.PredicateRegistry` to cache.

    """

    def __init__(self, key_lookup: KeyLookup[_ValueT]) -> None:
        self.key_lookup = key_lookup
        self.component = Cache(key_lookup.component).__getitem__
        self.fallback = Cache(key_lookup.fallback).__getitem__

        def _all(key: Sequence[Any]) -> list[_ValueT]:
            return list(key_lookup.all(key))

        self.all = Cache(_all).__getitem__


class LruCachingKeyLookup(Generic[_ValueT]):
    """A key lookup that caches.

    Implements the read-only API of :class:`reg.predicate.PredicateRegistry`,
    using a cache to speed up access.

    The cache is LRU so won't grow beyond a certain limit, preserving
    memory. This is only useful if you except the access pattern to
    your function to involve a huge range of different predicate keys.

    :param: key_lookup - the :class:`reg.predicate.PredicateRegistry` to cache.
    :param component_cache_size: how many cache entries to store for
      the ``component`` method. This is also used by dispatch
      calls.
    :param all_cache_size: how many cache entries to store for the
      the ``all`` method.
    :param fallback_cache_size: how many cache entries to store for
      the ``fallback`` method.
    """

    def __init__(
        self,
        key_lookup: KeyLookup[_ValueT],
        component_cache_size: int,
        all_cache_size: int,
        fallback_cache_size: int,
    ) -> None:
        self.key_lookup = key_lookup
        self.component = lru_cache(component_cache_size)(key_lookup.component)
        self.fallback = lru_cache(fallback_cache_size)(key_lookup.fallback)

        def _all(key: Sequence[Any]) -> list[_ValueT]:
            return list(key_lookup.all(key))

        self.all = lru_cache(all_cache_size)(_all)
