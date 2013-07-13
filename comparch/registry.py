from .mapping import MultiMap, ClassMultiMapKey

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
        # XXX implement setdefault might be nice
        l = self._map.exact_get(key, [])
        self._map[key] = l
        for class_, discriminator_map in l:
            if class_ is target:
                break
        else:
            discriminator_map = {}
            l.append((target, discriminator_map))
            l.sort(key=_inheritance_sortkey)
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
        key = ClassMultiMapKey(*[obj.__class__ for obj in objs])
        for l in self._map.all(key):
            for class_, discriminator_map in l:
                if issubclass(class_, target):
                    return discriminator_map.get(discriminator)
        return None
        

def _inheritance_sortkey(target_tuple):
    class_, discriminator_map = target_tuple
    return tuple(reversed(map(ClassSortable, class_.__mro__)))

# what are the rules for sorting classes in Python? I can't
# find them. So we'll just implement our own
# we could instead implement a topological sort, which may
# be more efficient
class ClassSortable(object):
    def __init__(self, class_):
        self.class_ = class_

    def __repr__(self):
        return "<ClassSortable for %r>" % self.class_
    
    # lt is used by sort
    def __lt__(self, other):
        if self.class_ is other.class_:
            return False
        return issubclass(other.class_, self.class_)

    def __eq__(self, other):
        return self.class_ is other.class_
 
# if I register an elephant and I want an animal, I want to find elephant

# if we find multiple targets, one elephant and one animal, and I want an
# animal, which one do I find? if I want an elephant it's clear; the elephant
# is the only option
# we can keep track of the targets registered and sort them so that the
# base classes come before the subclasses. this way we'll always find
# the closest subclass



# if register a object and I want an ancestor, I want to find it too

# so look for all registrations for key, then find the first one (?)
# that matches.

# this means that if I have a Zoo and a SpecialZoo, and I've registered
# Animal for Zoo and Elephant for SpecialZoo, and I look up an animal for
# special zoo, I'd find the elephant first.
