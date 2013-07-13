from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap
from .abcs import IRegistry, ILookup

class Registry(IRegistry, ILookup):
    """A component registry.
    
    Objects are looked up based on their class, and the target is
    the class of what we want to look up.

    There is also a discriminator, an immutable object that can be used
    to distinguish one kind of thing we look up from another.
    """

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
        
    def lookup(self, target, objs, discriminator):
        target = ClassMapKey(target)
        key = ClassMultiMapKey(*[obj.__class__ for obj in objs])
        for im in self._map.all(key):
            found = im.get(target)
            if found is not None:
                break
        else:
            return None
        return found.get(discriminator)

    def adapt(self, target, objs, discriminator):
        # self-adaptation
        if len(objs) == 1 and isinstance(objs[0], target):
            return objs[0]
        adapter = self.lookup(target, objs, name)
        if adapter is None:
            return None
        try:
            return adapter(*objs)
        except TypeError, e:
            raise TypeError(str(e) + " (%s)" % adapter)
    
