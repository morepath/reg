"""Look up components by instance (using their classes) and target class.
"""

from .sentinel import Sentinel

from abc import ABCMeta, abstractmethod

SENTINEL = Sentinel('Sentinel')

class ILookup(object):
    """Look up components by the class of objects.

    The lookup API is separate from the registration API to allow
    composition of lookups from multiple registries.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def component(self, func, args, default=SENTINEL):
        """Look up a component that was registered.

        A component can be any Python object.

        Lookup is for a function (func) and its arguments (args).

        The target is the class that we want to look up. The target is
        used to distinguish components from each other, and to
        establish an inheritance relationship (if I want an Animal a
        registered Elephant will do).

        If what is found is a component instance, then component
        should be an instance of target (or an instance of a subclass
        of target).

        If what is found is a component factory (adapter factory),
        then the result of calling this factory should be an instance
        of target (or an instance of a subclass of target).

        There is no checking of any of such however, and for some
        targets you expect something else entirely. That's fine.

        objs is a list of 0 to n objects that we use to look up the
        component. The classes of the objects are used to do the look
        up. If multiple objs are listed, the lookup is made for that
        combination of objs.

        If the component found has the special interface IMatcher, it
        will be called with objs as parameters (``matcher(*objs)``). If
        an object is returned this will be returned as the real matching
        component. If ``None`` is returned it will look for a match higher
        up the ancestor chain.

        If the component can be found, it will be returned. If the
        component cannot be found, ``None`` is returned.
        """

    @abstractmethod
    def adapt(self, func, args, default=SENTINEL):
        """Look up an adapter for objs. Adapt objs to target abc.

        The behavior of this method is like that of lookup, but it
        performs an extra step: it calls the found component with the
        objs given as arguments. The resulting instance should be a
        subclass of the target class (although no such checking is
        done).
        """

    @abstractmethod
    def all(self, target, objs):
        """Lookup up all components registered for objs.

        Will check whether the found component is an IMatcher, in which
        case it will be called. If non-None is returned, the found value is
        included as a matching component.
        """


class IMatcher(object):
    """Look up by calling and returning value.

    If an IMatcher component is registered, it is called with the objects
    as an argument, and the resulting value is considered to be the looked up
    component. If the resulting value is None, no component is found for
    this matcher.
    """
    __metaclass__ = ABCMeta


class LookupError(Exception):
    pass

class Lookup(ILookup):
    def __init__(self, class_lookup):
        self.class_lookup = class_lookup

    def component(self, func, args, default=SENTINEL):
        result = next(self.all(func, args), None)
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise LookupError(
            "%r: no component found for args %r" % (
                func,
                args))

    def adapt(self, func, args, default=SENTINEL):
        adapter = self.component(func, args, default)
        if adapter is default:
            return default
        result = adapter(*args)
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise LookupError(
            "%r: no function found for args %r" % (
                func, args))

    def all(self, func, args):
        for found in self.class_lookup.all(
                func, [arg.__class__ for arg in args]):
            if isinstance(found, IMatcher):
                found = found(*args)
            if found is not None:
                yield found


