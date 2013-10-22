"""Registry where you can register components by function and classes
that you look up the component for."""

from .mapping import MultiMap, ClassMapKey, ClassMultiMapKey, InverseMap
from .lookup import Lookup

from abc import ABCMeta, abstractmethod

class IRegistry(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def register(self, func, args, component):
        """Register a component with the registry.

        The target is a class by which the component can be
        looked up.  The registered object should either be an instance
        of that class, or in the case of an adapter, return a such an
        instance.

        sources is a list of 0 to n classes that
        the component is registered for. If multiple sources are listed,
        a registration is made for that combination of sources.

        The component is a python object (function, class, instance) that is
        registered.

        Typically what you would register would be either components
        that are an instance of target or factory functions that
        produce an instance of target. But you could register anything,
        and that's fine; it's not checked.
        """

    @abstractmethod
    def clear(self):
        """Clear registry of all registrations.
        """

    @abstractmethod
    def exact(self, func, args):
        """Get registration for target and sources.

        Does not go to base classes, just returns exact registration.

        None if no registration exists.
        """

class IClassLookup(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, func, args):
        """Look up a component, by class.

        The target is the class that we want to look up. The component
        found should normally be an instance that class, or in the
        case of an adapter, have it result be an instance of that class,
        but no such checking is done and you can register anything.

        sources is a list of 0 to n classes that we use to look up the
        component.  If multiple classes are listed, the lookup is made
        for that combination of classes.

        If the component can be found, it will be returned. If the
        component cannot be found, ``None`` is returned.
        """

    @abstractmethod
    def all(self, func, args):
        """Lookup up all components, by class.

        The target is a class by which the component can be
        looked up.

        sources is a list of 0 to n classes that the component is
        registered for. If multiple sources are listed, a registration
        is made for that combination of sources.

        Yields all matching components.
        """

class ClassRegistry(IRegistry, IClassLookup):
    def __init__(self):
        self._d = {}

    def register(self, func, args, component):
        m = self._d.get(func)
        if m is None:
            m = self._d[func] = MultiMap()
        m[ClassMultiMapKey(*args)] = component

    def clear(self):
        self._d = {}

    def exact(self, func, args):
        m = self._d.get(func)
        if m is None:
            return None
        return m.exact_get(ClassMultiMapKey(*args))

    def get(self, func, args):
        return next(self.all(func, args), None)

    def all(self, func, args):
        m = self._d.get(func)
        if m is None:
            return
        for component in m.all(ClassMultiMapKey(*args)):
            yield component

class Registry(IRegistry, Lookup):
    """A registry that is also a lookup.
    """
    def __init__(self):
        self.registry = ClassRegistry()
        # the class_lookup is this class itself
        Lookup.__init__(self, self.registry)

    def register(self, func, args, component):
        return self.registry.register(func, args, component)

    def clear(self):
        return self.registry.clear()

    def exact(self, func, args):
        return self.registry.exact(func, args)
