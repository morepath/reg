from abc import ABCMeta, abstractmethod, abstractproperty

SENTINEL = object()

class InterfaceMeta(ABCMeta):        
    def component(cls, *args, **kw):
        lookup, discriminator, default = process_kw(kw)
        return lookup.component(cls, args, discriminator, default)
    
    def adapt(cls, *args, **kw):
        # shortcut rule to make sure self-adaptation works even without lookup
        if len(args) == 1 and isinstance(args[0], cls):
            return args[0]
        lookup, discriminator, default = process_kw(kw)
        return lookup.adapt(cls, args, discriminator, default)

class Interface(object):
    __metaclass__ = InterfaceMeta

def process_kw(kw):
    discriminator = kw.pop('discriminator', None)
    name = kw.pop('name', None)
    if name is not None:
        if discriminator is not None:
            raise TypeError("Cannot give both name and discriminator")
        discriminator = name
    default = kw.pop('default', SENTINEL)
    lookup = find_lookup(kw)
    if kw:
        raise TypeError("Illegal extra keyword arguments: %s" %
                        ', '.join(kw.keys()))
    return lookup, discriminator, default

def find_lookup(kw):
    lookup = kw.pop('lookup', None)
    if lookup is None:
        # import here to break
        from .implicit import implicit
        lookup = implicit.lookup
        if lookup is None:
            raise NoImplicitLookupError(
                "Cannot lookup without explicit lookup argument "
                "because no implicit lookup was configured.")
    return lookup
