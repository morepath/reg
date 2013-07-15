from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap
from .interfaces import IRegistry, IClassLookup
from .lookup import Lookup

SENTINEL = object()

class ClassRegistry(IRegistry, IClassLookup):
    def __init__(self):
        self._map = MultiMap()
        
    def register(self, target, sources, discriminator, component):
        key = ClassMultiMapKey(*sources)
        target = ClassMapKey(target)
        im = self._map.exact_get(key)
        if im is None:
            self._map[key] = im = InverseMap()
        discriminator_map = im.exact_get(target)
        if discriminator_map is None:
            im[target] = discriminator_map = {}
        discriminator_map[discriminator] = component

    def get(self, target, sources, discriminator):
        target = ClassMapKey(target)
        key = ClassMultiMapKey(*sources)
        for im in self._map.all(key):
            found = im.get(target)
            if found is not None:
                result = found.get(discriminator)
                break
        else:
            result = None
        return result

class Registry(ClassRegistry, Lookup):
    """A registry that is also a lookup.
    """
    def __init__(self):
        ClassRegistry.__init__(self)
        # the class_lookup is this class itself
        Lookup.__init__(self, self)
