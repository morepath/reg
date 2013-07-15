"""
This module contains ClassLookups that can be used to compose
lookups together.
"""
from .interfaces import IClassLookup

CACHED_SENTINEL = object()

def ListClassLookup(object):
    """A simple list of class lookups functioning as an IClassLookup.

    Go through all items in the list, starting at the beginning and
    try to find the component. If found in a lookup, return it right away.
    """
    
    def __init__(self, lookups):
        self.lookups = lookups

    def get(self, target, sources, discriminator):
        for lookup in self.lookups:
            result = lookup.get(target, sources, discriminator)
            if result is not None:
                return result
        return None
    
class ChainClassLookup(IClassLookup):
    """Chain a class lookup on top of another class lookup.

    Look in the supplied IClassLookup object first, and if not found, look
    in the next IClassLookup object. This way multiple IClassLookup objects
    can be chained together.
    """
    
    def __init__(self, lookup, next):
        self.lookup = lookup
        self.next = next

    def get(self, target, sources, discriminator):
        result = self.lookup.get(target, sources, discriminator)
        if result is not None:
            return result
        return self.next.get(target, sources,  discriminator)

class CachedClassLookup(IClassLookup):
    def __init__(self, class_lookup):
        self.class_lookup = class_lookup
        self._cache = {}
        
    def get(self, target, sources, discriminator):
        sources = tuple(sources)
        component = self._cache.get((target, sources, discriminator),
                                    CACHED_SENTINEL)
        if component is not CACHED_SENTINEL:
            return component
        component = self.class_lookup.get(target, sources, discriminator)
        self._cache[(target, sources, discriminator)] = component
        return component
 
