"""Interface meta class, which is like an abc but with additional component
lookup methods.
"""

from abc import ABCMeta, abstractmethod, abstractproperty
# these really need to be here, pyflakes
assert abstractmethod, abstractproperty

SENTINEL = object()


class InterfaceMeta(ABCMeta):
    def component(cls, *args, **kw):
        lookup, default = process_kw(kw)
        return lookup.component(cls, args, default)

    def adapt(cls, *args, **kw):
        # shortcut rule to make sure self-adaptation works even without lookup
        if len(args) == 1 and isinstance(args[0], cls):
            return args[0]
        lookup, default = process_kw(kw)
        return lookup.adapt(cls, args, default)

    def all(cls, *args, **kw):
        lookup = find_lookup(kw)
        if kw:
            raise TypeError("Illegal extra keyword arguments: %s" %
                            ', '.join(kw.keys()))
        return lookup.all(cls, args)


class Interface(object):
    __metaclass__ = InterfaceMeta


def process_kw(kw):
    default = kw.pop('default', SENTINEL)
    lookup = find_lookup(kw)
    if kw:
        raise TypeError("Illegal extra keyword arguments: %s" %
                        ', '.join(kw.keys()))
    return lookup, default


class NoImplicitLookupError(Exception):
    pass


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
