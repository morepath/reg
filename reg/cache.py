from __future__ import annotations

from repoze.lru import lru_cache  # type: ignore
from typing import TYPE_CHECKING, Any, Generic

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

    Implements the read-only API of :class:`reg.PredicateRegistry` using
    a cache to speed up access.

    This cache is backed by a simple dictionary so could potentially
    grow large if the dispatch in question can be called with a large
    combination of arguments that result in a large range of different
    predicate keys. If so, you can use
    :class:`reg.LruCachingKeyLookup` instead.

    :param: key_lookup - the :class:`PredicateRegistry` to cache.

    """

    def __init__(self, key_lookup: KeyLookup[_ValueT]) -> None:
        self.key_lookup = key_lookup
        self.component = Cache(key_lookup.component).__getitem__  # type: ignore
        self.fallback = Cache(key_lookup.fallback).__getitem__  # type: ignore

        def _all(key: Sequence[Any]) -> list[_ValueT]:
            return list(key_lookup.all(key))

        self.all = Cache(_all).__getitem__  # type: ignore

    if TYPE_CHECKING:
        # NOTE: For pyright's sake we declare these callable instance attributes
        #       as methods, even though they're not, since pyright does not seem
        #       to be able to match protocols against them. mypy can deal with
        #       it just fine
        def component(self, key: Sequence[Any], /) -> _ValueT | None:
            raise NotImplementedError

        def fallback(self, key: Sequence[Any], /) -> _ValueT | None:
            raise NotImplementedError

        def all(self, key: Sequence[Any], /) -> list[_ValueT]:
            raise NotImplementedError


class LruCachingKeyLookup(Generic[_ValueT]):
    """A key lookup that caches.

    Implements the read-only API of :class:`reg.PredicateRegistry`, using
    a cache to speed up access.

    The cache is LRU so won't grow beyond a certain limit, preserving
    memory. This is only useful if you except the access pattern to
    your function to involve a huge range of different predicate keys.

    :param: key_lookup - the :class:`PredicateRegistry` to cache.
    :param component_cache_size: how many cache entries to store for
      the :meth:`component` method. This is also used by dispatch
      calls.
    :param all_cache_size: how many cache entries to store for the
      the :meth:`all` method.
    :param fallback_cache_size: how many cache entries to store for
      the :meth:`fallback` method.
    """

    def __init__(
        self,
        key_lookup: KeyLookup[_ValueT],
        component_cache_size: int,
        all_cache_size: int,
        fallback_cache_size: int,
    ) -> None:
        self.key_lookup = key_lookup
        self.component = lru_cache(component_cache_size)(key_lookup.component)  # type: ignore
        self.fallback = lru_cache(fallback_cache_size)(key_lookup.fallback)  # type: ignore
        self.all = lru_cache(all_cache_size)(lambda key: list(key_lookup.all(key)))  # type: ignore

    if TYPE_CHECKING:
        # NOTE: For pyright's sake we declare these callable instance attributes
        #       as methods, even though they're not, since pyright does not seem
        #       to be able to match protocols against them. mypy can deal with
        #       it just fine
        def component(self, key: Sequence[Any], /) -> _ValueT | None:
            raise NotImplementedError

        def fallback(self, key: Sequence[Any], /) -> _ValueT | None:
            raise NotImplementedError

        def all(self, key: Sequence[Any], /) -> list[_ValueT]:
            raise NotImplementedError
