from collections.abc import Callable
from typing import Any, TypeVar, overload

_F = TypeVar("_F", bound=Callable[..., Any])
_T = TypeVar("_T")

class CacheSizeMustBeGreaterThanZero(ValueError):
    def __init__(self, size: int) -> None: ...

class CacheMaxsizeRequired(ValueError):
    def __init__(self) -> None: ...

class CacheAlreadyInUse(KeyError):
    def __init__(self, name: str) -> None: ...

class Cache:
    def clear(self) -> None: ...
    @overload
    def get(self, key: Any) -> Any | None: ...
    @overload
    def get(self, key: Any, default: _T) -> Any | _T: ...
    def put(self, key: Any, val: Any) -> None: ...
    def invalidate(self, key: Any) -> None: ...

class UnboundedCache(Cache):
    def __init__(self) -> None: ...

class LRUCache(Cache):
    size: int
    evictions: int
    hits: int
    misses: int
    lookups: int
    def __init__(self, size: int) -> None: ...

class ExpiringLRUCache(Cache):
    size: int
    default_timeout: float
    evictions: int
    hits: int
    misses: int
    lookups: int
    def __init__(self, size: int, default_timeout: float = ...) -> None: ...
    def put(self, key: Any, val: Any, timeout: float | None = None) -> None: ...

class lru_cache:
    cache: Cache
    def __init__(
        self,
        maxsize: int | None,
        cache: Cache | None = None,
        timeout: float | None = None,
        ignore_unhashable_args: bool = False,
    ) -> None: ...
    def __call__(self, func: _F) -> _F: ...

class CacheMaker:
    def __init__(self, maxsize: int | None = None, timeout: float = ...) -> None: ...
    def memoized(self, name: str | None = None) -> lru_cache: ...
    def lrucache(
        self, name: str | None = None, maxsize: int | None = None
    ) -> lru_cache: ...
    def expiring_lrucache(
        self,
        name: str | None = None,
        maxsize: int | None = None,
        timeout: float | None = None,
    ) -> lru_cache: ...
    def clear(self, *names: str) -> None: ...
