from .interfaces import ILookup, ComponentLookupError
from .compose import CachedClassLookup
from .interface import SENTINEL

class Lookup(ILookup):
    """A component lookup.
    
    Objects are looked up based on their class, and the target is
    the class of what we want to look up.

    There is also a discriminator, an immutable object that can be used
    to distinguish one kind of thing we look up from another.
    """

    def __init__(self, class_lookup):
        self.class_lookup = class_lookup
    
    def component(self, target, objs, discriminator, default=SENTINEL):
        result = self.class_lookup.get(
            target, [obj.__class__ for obj in objs], discriminator)
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise ComponentLookupError(
            "Could not find component for target %r from objs %r "
            "with discriminator %r" % (
                target,
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

class CachedLookup(Lookup, CachedClassLookup):
    def __init__(self, class_lookup):
        CachedClassLookup.__init__(self, class_lookup)
        # the class_lookup is this class itself
        Lookup._init__(self, self)
