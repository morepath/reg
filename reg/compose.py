"""
Compose ClassLookups. ListClassLookup and ChainClassLookup are different
ways to compose ClassLookups together into a single one. CachingClassLookup
is a caching version of ClassLookup.
"""
from __future__ import unicode_literals

from .registry import IClassLookup
from .sentinel import Sentinel

CACHED_SENTINEL = Sentinel('CACHED_SENTINEL')


class ListClassLookup(IClassLookup):
    """A simple list of class lookups functioning as a single IClassLookup.

    Go through all items in the list, starting at the beginning and
    try to find the component. If found in a lookup, return it right away.
    """

    def __init__(self, lookups):
        self.lookups = lookups

    def get(self, key, classes):
        for lookup in self.lookups:
            result = lookup.get(key, classes)
            if result is not None:
                return result
        return None

    def all(self, key, classes):
        for lookup in self.lookups:
            for component in lookup.all(key, classes):
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

    def get(self, key, classes):
        result = self.lookup.get(key, classes)
        if result is not None:
            return result
        return self.next.get(key, classes)

    def all(self, key, classes):
        for component in self.lookup.all(key, classes):
            yield component
        for component in self.next.all(key, classes):
            yield component


class CachingClassLookup(IClassLookup):
    """Cache an existing class lookup.

    All previous accesses to class lookup are cached.
    """

    def __init__(self, class_lookup):
        self.class_lookup = class_lookup
        self._cache = {}
        self._all_cache = {}

    def get(self, key, classes):
        classes = tuple(classes)
        component = self._cache.get((key, classes), CACHED_SENTINEL)
        if component is not CACHED_SENTINEL:
            return component
        component = self.class_lookup.get(key, classes)
        self._cache[(key, classes)] = component
        return component

    def all(self, key, classes):
        classes = tuple(classes)
        result = self._all_cache.get((key, classes))
        if result is not None:
            return result
        result = list(self.class_lookup.all(key, classes))
        self._all_cache[(key, classes)] = result
        return result
