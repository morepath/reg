from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap
from .abcs import IRegistry, ILookup, ComponentLookupError

SENTINEL = object()

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
        
    def component(self, target, objs, discriminator, default=SENTINEL):
        target = ClassMapKey(target)
        key = ClassMultiMapKey(*[obj.__class__ for obj in objs])
        for im in self._map.all(key):
            found = im.get(target)
            if found is not None:
                result = found.get(discriminator)
                break
        else:
            result = None
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise ComponentLookupError(
            "Could not find component for target %r from objs %r "
            "with discriminator %r" % (
                target.key,
                objs,
                discriminator))
    
    def adapt(self, target, objs, discriminator, default=SENTINEL):
        # self-adaptation
        if len(objs) == 1 and isinstance(objs[0], target):
            return objs[0]
        adapter = self.component(target, objs, discriminator, default)
        if adapter is default:
            return default
        try:
            return adapter(*objs)
        except TypeError, e:
            raise TypeError(str(e) + " (%s)" % adapter)
