from repoze.lru import LRUCache

from .sentinel import NOT_FOUND


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
        self.key_dict_to_predicate_key = key_lookup.key_dict_to_predicate_key
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
        self.key_dict_to_predicate_key = key_lookup.key_dict_to_predicate_key
        self.component_cache = LRUCache(component_cache_size)
        self.all_cache = LRUCache(all_cache_size)
        self.fallback_cache = LRUCache(fallback_cache_size)

    def component(self, predicate_key):
        """Lookup value in registry based on predicate_key.

        If value for predicate_key cannot be found, looks up first
        permutation of predicate_key for which there is a value. Permutations
        are made according to the predicates registered for the key.

        :param predicate_key: an immutable predicate key, constructed
          for predicates given for this key.
        :returns: a registered value, or ``None``.
        """
        result = self.component_cache.get(predicate_key, NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = self.key_lookup.component(predicate_key)
        self.component_cache.put(predicate_key, result)
        return result

    def fallback(self, predicate_key):
        """Lookup fallback based on predicate_key.

        This finds the fallback for the most specific predicate
        that fails to match.

        :param predicate_key: an immutable predicate key, constructed
          for predicates given for this key.
        :returns: the fallback value for the most specific predicate
          the failed to match.
        """
        result = self.fallback_cache.get(predicate_key, NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = self.key_lookup.fallback(predicate_key)
        self.fallback_cache.put(predicate_key, result)
        return result

    def all(self, predicate_key):
        """Lookup iterable of values registered for predicate_key.

        Looks up values registered for all permutations of
        predicate_key, the most specific first.

        :param predicate_key: an immutable predicate key, constructed for
          the predicates given for this key.
        :returns: An iterable of registered values.
        """
        result = self.all_cache.get(predicate_key, NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = list(self.key_lookup.all(predicate_key))
        self.all_cache.put(predicate_key, result)
        return result
