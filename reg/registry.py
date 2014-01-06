"""Registry where you can register components by function and classes
that you look up the component for."""
from __future__ import unicode_literals

from .mapping import MultiMap, ClassMultiMapKey
from .lookup import Lookup

from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass


class IRegistry(with_metaclass(ABCMeta, object)):
    """A registration API for components.
    """

    @abstractmethod
    def register(self, key, classes, component):
        """Register a component.

        :param key: Register component for this key.
        :type key: hashable object, normally function.
        :param classes: List of classes for which to register component.
        :type classes: list of classes.
        :param component: Any python object, often a function.
                          Can be a :class:`reg.Matcher` instance.
        :type component: object.

        The key is a hashable object, often a function object, by
        which the component can be looked up.

        classes is a list of 0 to n classes that the component is
        registered for. If multiple sources are listed, a registration
        is made for that combination of sources.

        The component is a python object (function, class, instance,
        etc) that is registered. If you're working with multiple dispatch,
        you would register a function that expects instances of the classes
        in ``classes`` as its arguments.
        """

    @abstractmethod
    def clear(self):
        """Clear registry of all registrations.
        """

    @abstractmethod
    def exact(self, key, classes):
        """Get registered component for exactly key and classes.

        :param key: Get component for this key.
        :type key: hashable object, normally function.
        :param classes: List of classes for which to get component.
        :type classes: list of classes.
        :returns: registered component, or ``None``.

        Does not go to base classes, just returns exact registration.

        Returns ``None`` if no registration exists.
        """


class IClassLookup(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def get(self, key, classes):
        """Look up a component, by key and classes of arguments.

        :param key: Get component for this key.
        :type key: hashable object, normally function.
        :param classes: List of classes for which to get component.
        :type classes: list of classes.
        :returns: registered component, or ``None``.

        The key is a hashable object, often a function object, by
        which the component is looked up.

        classes is a list of 0 to n classes that we use to look up the
        component. If multiple classes are listed, the lookup is made
        for that combination of classes.

        In order to find the most matching registered component, a
        Cartesian product is made of all combinations of base classes given,
        sorted by inheritance, first class to last class, most specific to
        least specific.

        This calculation is relatively expensive so you can wrap a
        class lookup in a :class:`reg.CachingClassLookup` proxy to
        speed up subsequent calls.

        If the component can be found, it will be returned. If the
        component cannot be found, ``None`` is returned.
        """

    @abstractmethod
    def all(self, key, classes):
        """Look up all components, by key and classes.

        :param key: Get components for this key.
        :type key: hashable object, normally function.
        :param classes: List of classes for which to get components.
        :type classes: list of classes.
        :returns: iterable of found components.

        The key is a hashable object, often a function object, by
        which the components are looked up.

        classes is a list of 0 to n classes that we use to look up the
        components. If multiple classes are listed, the lookup is made
        for that combination of classes. All registered components for
        combinations of base classes are also returned.

        A Cartesian product is made of all combinations of base
        classes to do this, sorted by inheritance, first class to last
        class, most specific to least specific.

        This calculation is relatively expensive so you can wrap a
        class lookup in a :class:`reg.CachingClassLookup` proxy to
        speed up subsequent calls.

        If no components can be found, the iterable returned will be empty.
        """


class ClassRegistry(IRegistry, IClassLookup):
    def __init__(self):
        self._d = {}

    def register(self, key, classes, component):
        m = self._d.get(key)
        if m is None:
            m = self._d[key] = MultiMap()
        m[ClassMultiMapKey(*classes)] = component

    def clear(self):
        self._d = {}

    def exact(self, key, classes):
        m = self._d.get(key)
        if m is None:
            return None
        return m.exact_get(ClassMultiMapKey(*classes))

    def get(self, key, classes):
        return next(self.all(key, classes), None)

    def all(self, key, classes):
        m = self._d.get(key)
        if m is None:
            return
        for component in m.all(ClassMultiMapKey(*classes)):
            yield component


class Registry(IRegistry, Lookup):
    def __init__(self):
        self.registry = ClassRegistry()
        # the class_lookup is this class itself
        Lookup.__init__(self, self.registry)

    def register(self, key, classes, component):
        return self.registry.register(key, classes, component)

    def clear(self):
        return self.registry.clear()

    def exact(self, key, classes):
        return self.registry.exact(key, classes)
