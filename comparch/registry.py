"""Registry where you can register components by target class and classes
that you look up the component for."""

from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap
from .interfaces import IRegistry, IClassLookup
from .lookup import Lookup

SENTINEL = object()

class ClassRegistry(IRegistry, IClassLookup):
    def __init__(self):
        self._map = MultiMap()
        
    def register(self, target, sources, component):
        key = ClassMultiMapKey(*sources)
        target = ClassMapKey(target)
        im = self._map.exact_get(key)
        if im is None:
            self._map[key] = im = InverseMap()
        im[target] = component

    def clear(self):
        self._map = MultiMap()
        
    def exact_get(self, target, sources):
        key = ClassMultiMapKey(*sources)
        target = ClassMapKey(target)
        im = self._map.exact_get(key)
        if im is None:
            return None
        return im.exact_get(target)
    
    def get(self, target, sources):
        try:
            return next(self.get_all(target, sources))
        except StopIteration:
            return None

    def get_all(self, target, sources):
        target = ClassMapKey(target)
        key = ClassMultiMapKey(*sources)
        for im in self._map.all(key):
            found = im.get(target)
            if found is not None:
                yield found

class Registry(ClassRegistry, Lookup):
    """A registry that is also a lookup.
    """
    def __init__(self):
        ClassRegistry.__init__(self)
        # the class_lookup is this class itself
        Lookup.__init__(self, self)
