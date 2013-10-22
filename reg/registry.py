"""Registry where you can register components by function and classes
that you look up the component for."""

from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap
from .interfaces import IRegistry, IClassLookup
from .lookup import Lookup

SENTINEL = object()


class ClassRegistry(IRegistry, IClassLookup):
    def __init__(self):
        self._d = {}
    
    def register(self, target, sources, component):
        m = self._d.get(target)
        if m is None:
            m = self._d[target] = MultiMap()
        m[ClassMultiMapKey(*sources)] = component

    def clear(self):
        self._d = {}
    
    def exact(self, target, sources):
        m = self._d.get(target)
        if m is None:
            return None
        return m.exact_get(ClassMultiMapKey(*sources))

    def get(self, target, sources):
        return next(self.all(target, sources), None)

    def all(self, target, sources):
        m = self._d.get(target)
        if m is None:
            return
        for component in m.all(ClassMultiMapKey(*sources)):
            yield component

class Registry(IRegistry, Lookup):
    """A registry that is also a lookup.
    """
    def __init__(self):
        self.registry = ClassRegistry()
        # the class_lookup is this class itself
        Lookup.__init__(self, self.registry)

    def register(self, target, sources, component):
        return self.registry.register(target, sources, component)

    def clear(self):
        return self.registry.clear()

    def exact(self, target, sources):
        return self.registry.exact(target, sources)
