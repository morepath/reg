"""
Compose ClassLookups. ListClassLookup and ChainClassLookup are different
ways to compose ClassLookups together into a single one. CachedClassLookup
is a caching version of ClassLookup.
"""

from .interfaces import IClassLookup

CACHED_SENTINEL = object()


class ListClassLookup(IClassLookup):
    """A simple list of class lookups functioning as an IClassLookup.

    Go through all items in the list, starting at the beginning and
    try to find the component. If found in a lookup, return it right away.
    """

    def __init__(self, lookups):
        self.lookups = lookups

    def get(self, target, sources):
        for lookup in self.lookups:
            result = lookup.get(target, sources)
            if result is not None:
                return result
        return None

    def get_all(self, target, sources):
        for lookup in self.lookups:
            for component in lookup.get_all(target, sources):
                if component is not None:
                    yield component


class ChainClassLookup(IClassLookup):
    """Chain a class lookup on top of another class lookup.

    Look in the supplied IClassLookup object first, and if not found, look
    in the next IClassLookup object. This way multiple IClassLookup objects
    can be chained together.
    """

    def __init__(self, lookup, next):
        self.lookup = lookup
        self.next = next

    def get(self, target, sources):
        result = self.lookup.get(target, sources)
        if result is not None:
            return result
        return self.next.get(target, sources)

    def get_all(self, target, sources):
        for component in self.lookup.get_all(target, sources):
            yield component
        for component in self.next.get_all(target, sources):
            yield component


class CachedClassLookup(IClassLookup):
    def __init__(self, class_lookup):
        self.class_lookup = class_lookup
        self._cache = {}
        self._all_cache = {}

    def get(self, target, sources):
        sources = tuple(sources)
        component = self._cache.get((target, sources), CACHED_SENTINEL)
        if component is not CACHED_SENTINEL:
            return component
        component = self.class_lookup.get(target, sources)
        self._cache[(target, sources)] = component
        return component

    def get_all(self, target, sources):
        sources = tuple(sources)
        result = self._all_cache.get((target, sources))
        if result is not None:
            return result
        result = list(self.class_lookup.get_all(target, sources))
        self._all_cache[(target, sources)] = result
        return result
