class MapKey(object):
    """A map key that can have parents.
    """
    def __init__(self, key, parents=()):
        self.key = key
        self.parents = tuple(parents)
        # we need Python's mro, but we don't have classes. We create
        # some with the same structure as our parent structure. then we
        # get the mro
        self._mro_helper = type('fake_type',
                                tuple(parent._mro_helper for
                                      parent in parents),
                                {'mapkey': self})
        # we then store the map keys for the mro (without the last
        # entry, which is always object)
        self.ancestors = [
            base.mapkey for base in self._mro_helper.__mro__[:-1]]

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __repr__(self):
        return "<MapKey: %r>" % self.key

class Map(dict):
    """special map that understands about keys in a dag.
    
    A normal mapping (dictionary) in Python has keys that are
    completely independent from each other. If you look up a
    particular key, either that key is present in the mapping or not
    at all.

    This is a mapping that understands about relations between
    keys. Keys can have zero or more parents; they are in a directed
    acyclic graph. If a key is not found, a value will still be found
    if a parent key can be found.
    """
    # sometimes we want to look up things exactly in the underlying
    # dictionary
    exact_getitem = dict.__getitem__
    exact_get = dict.get
    
    def __getitem__(self, key):
        for mapkey in key.ancestors:
            try:
                return self.exact_getitem(mapkey)
            except KeyError:
                pass
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def all(self, key):
        for mapkey in key.ancestors:
            try:
                yield self.exact_getitem(mapkey)
            except KeyError:
                pass

# XXX create a caching proxy to speed up things after registration is
# frozen
# create a freeze concept that kills registration, so that caching is safe
# freezing after software initialization is safe
class MultiMap(object):
    """map that takes sequences of MapKey objects as key.

    A MultiMap is a map that takes sequences of MapKey objects as its
    key. We call such a sequence of MapKeys a MultiMapKey.

    When looking up a MultiMapKey in a MultiMap, it is compared
    component-wise to the MultiMapKeys registered in the MultiMap.
    Each of the components of a MultiMapKey found must be either equal
    to or a parent of the corresponding component of the MultiMapKey
    being looked up.  If more than one MultiMapKey could be found by a
    lookup, the one whose first component matches most specifically
    wins, the other components being considered as subordinate
    comparison criteria, in order.
    """
    def __init__(self):
        self._by_arity = {}
        
    def __setitem__(self, key, value):
        arity = MapKey(len(key))
        key = [arity] + list(key)
        last_key = key.pop()
        map = self._by_arity
        for k in key:
            # XXX why is the dict() call here?
            submap = dict(map).get(k)
            if submap is None:
                submap = map[k] = Map()
            map = submap
        map[last_key] = value

    def __delitem__(self, key):
        arity = MapKey(len(key))
        key = [arity] + list(key)
        last_key = key.pop()
        map = self._by_arity
        for k in key:
            map = dict(map)[k]
        del map[last_key]

    def __getitem__(self, key):
        arity = MapKey(len(key))
        key = (arity,) + key
        return self._getitem_recursive(self._by_arity, key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def exact_getitem(self, key):
        arity = MapKey(len(key))
        m = self._by_arity[arity]
        for k in key:
            m = m.exact_getitem(k)
        return m

    def exact_get(self, key, default=None):
        try:
            return self.exact_getitem(key)
        except KeyError:
            return default
        
    # XXX should use ancestor_multikeys, but need to turn it
    # into a generator for efficiency
    def _getitem_recursive(self, map, key):
        first = key[0]
        rest = key[1:]
        if not rest:
            return map[first]
        for ancestor in first.ancestors:
            try:
                return self._getitem_recursive(map[ancestor], rest)
            except KeyError, e:
                pass
        # XXX is key informative enough for a key error? probably not
        raise KeyError(key)

    def all(self, key):
        result = []
        for k in ancestor_multikeys(key):
            try:
                result.append(self.exact_getitem(k))
            except KeyError:
                pass
        return result

# convert to generator
def ancestor_multikeys(key):
    first = key[0]
    rest = key[1:]
    if not rest:
        for ancestor in first.ancestors:
            yield (ancestor,)
        return
    for ancestor in first.ancestors:
        for multikey in ancestor_multikeys(rest):
            yield (ancestor,) + multikey

class ClassMapKey(object):
    def __init__(self, class_):
        self.key = class_
        self.parents = tuple(
            [ClassMapKey(base) for base in class_.__bases__])
        self.ancestors = [self] + [ClassMapKey(ancestor) for ancestor in
                          class_.__mro__[1:]]
        
    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __repr__(self):
        return "<ClassMapKey: %r>" % self.key

# XXX if this is a real class, ancestors can be a method
# but it needs to be generic, MultiMapKey, first
def ClassMultiMapKey(classes):
    return tuple([ClassMapKey(class_) for class_ in classes])

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
    
class Registry(object):
    """A component registry.
    
    Objects are looked up based on their class, and the target is
    the class of what we want to look up.

    There is also a discriminator, an immutable object that can be used
    to distinguish one kind of thing we look up from another.
    """

    def __init__(self):
        self._map = MultiMap()

    def register(self, sources, target, discriminator, component):
        key = ClassMultiMapKey(sources)
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
        
    def lookup(self, objs, target, discriminator):
        """look up a component in the registry.
        
        objs is a list of 0 to n objects that we use to look up the
        component.  If multiple objs are listed, the lookup is made
        for that combination of objs. The classes of the objects are
        used to do the look up.

        The target is the class that we want to look up. The component
        found should normally be an instance of that class (or of a
        subclass), although no such checking is done.
        
        The disciminator is an immutable object under which the
        component should be looked up. If the component has not been
        registered under that discriminator, it won't be found.
        
        If the component can be found, it will be returned. If the
        component cannot be found, ``None`` is returned.
        """
        key = ClassMultiMapKey([obj.__class__ for obj in objs])
        for l in self._map.all(key):
            for class_, discriminator_map in l:
                if issubclass(class_, target):
                    return discriminator_map.get(discriminator)
        return None
        
    
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
