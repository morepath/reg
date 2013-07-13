from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap

class Registry(object):
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
        """look up a component in the registry.
        
        The target is the class that we want to look up. The component
        found should normally be an instance of that class (or of a
        subclass), although no such checking is done and you are free
        to register any object as a component. In this case the
        target is just a way to have a handy way to identify the
        component you want.
        
        objs is a list of 0 to n objects that we use to look up the
        component.  If multiple objs are listed, the lookup is made
        for that combination of objs. The classes of the objects are
        used to do the look up.
        
        The disciminator is an immutable object under which the
        component should be looked up. If the component has not been
        registered under that discriminator, it won't be found.
        
        If the component can be found, it will be returned. If the
        component cannot be found, ``None`` is returned.
        """
        target = ClassMapKey(target)
        key = ClassMultiMapKey(*[obj.__class__ for obj in objs])
        for im in self._map.all(key):
            found = im.get(target)
            if found is not None:
                break
        else:
            return None
        return found.get(discriminator)
