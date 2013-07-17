from .interfaces import ILookup, ComponentLookupError
from .compose import CachedClassLookup
from .interface import SENTINEL

class Lookup(ILookup):
    def __init__(self, class_lookup):
        self.class_lookup = class_lookup
    
    def component(self, target, objs, default=SENTINEL):
        result = self.class_lookup.get(
            target, [obj.__class__ for obj in objs])
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise ComponentLookupError(
            "Could not find component for target %r from objs %r" % (
                target,
                objs))
    
    def adapt(self, target, objs, default=SENTINEL):
        # self-adaptation
        if len(objs) == 1 and isinstance(objs[0], target):
            return objs[0]
        adapter = self.component(target, objs, default)
        if adapter is default:
            return default
        try:
            result = adapter(*objs)
        except TypeError, e:
            raise TypeError(str(e) + " (%s)" % adapter)
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise ComponentLookupError(
            "Could not adapt %r to target %r; adapter is None" % (
                objs, target))
    
    def all(self, target, objs):
        for found in self.class_lookup.get_all(
            target, [obj.__class__ for obj in objs]):
            yield found
    
class CachedLookup(Lookup, CachedClassLookup):
    def __init__(self, class_lookup):
        CachedClassLookup.__init__(self, class_lookup)
        # the class_lookup is this class itself
        Lookup.__init__(self, self)
