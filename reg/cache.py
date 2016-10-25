from repoze.lru import lru_cache


class Cache(dict):
    """A dict to cache a function."""

    def __init__(self, func):
        self.func = func

    def __missing__(self, key):
        self[key] = result = self.func(key)
        return result


class DictCachingKeyLookup(object):
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
    def __init__(self, key_lookup):
        self.key_lookup = key_lookup
        self.component = Cache(key_lookup.component).__getitem__
        self.fallback = Cache(key_lookup.fallback).__getitem__
        self.all = Cache(lambda key: list(key_lookup.all(key))).__getitem__


class LruCachingKeyLookup(object):
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
    def __init__(self, key_lookup, component_cache_size, all_cache_size,
                 fallback_cache_size):
        self.key_lookup = key_lookup
        self.component = lru_cache(component_cache_size)(key_lookup.component)
        self.fallback = lru_cache(fallback_cache_size)(key_lookup.fallback)
        self.all = lru_cache(all_cache_size)(
            lambda key: list(key_lookup.all(key)))
