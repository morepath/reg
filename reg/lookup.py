"""Look up components by instance (using their classes) and target class.
"""

from .sentinel import Sentinel

SENTINEL = Sentinel('Sentinel')


class Matcher(object):
    """Look up by calling and returning value.

    If a component that subclasses Matcher is registered, it
    it is called with args, i.e. ``matcher(*args)``. The resulting value
    is considered to be the looked up component. If the resulting value is
    ``None``, no component is found for this matcher.
    """


class ComponentLookupError(LookupError):
    """Error raised when a component cannot be found.

    Will only be raised if nod ``default`` argument was supplied
    during lookup.
    """


class Lookup(object):
    """Look up objects for a key.

    The lookup API is also available directly on a function decorated
    with :func:`reg.generic`. The ``call`` method stands in for the actual
    function call. If the call method is in use from ``reg.generic``,
    :exc:`ComponentLookupError` is never raised, and instead the fall
    back is to the function being decorated.
    """
    def __init__(self, class_lookup):
        self.class_lookup = class_lookup

    def component(self, key, args, default=SENTINEL):
        """Look up a component.

        :param key: Look up component for this key.
        :type key: hashable object, normally function.
        :param args: Look up component for these arguments.
        :type args: list of objects.
        :param default: default value to return if lookup fails.
        :type default: object.
        :returns: registered component.
        :raises: ComponentLookupError

        A component can be any Python object.

        key is a hashable object that is used to determine what to
        look up. Normally it is a Python function.

        args is a list of 0 to n objects that we use to look up the
        component. The classes of the args are used to do the look
        up. If multiple args are listed, the lookup is made for that
        combination of args.

        If the component found is an instance of class:`Matcher`, it
        will be called with args as parameters
        (``matcher(*args)``). The matcher can return an object, in
        which case will be returned as the real matching component. If
        the matcher returns ``None`` it will look for a match higher
        up the ancestor chain of args.

        If a component can be found, it will be returned. If the
        component cannot be found, a :class:`ComponentLookupError`
        will be raised, unless a default argument is specified, in
        which case it will be returned.
        """
        result = next(self.all(key, args), None)
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise ComponentLookupError(
            "%r: no component found for args %r" % (
                key, args))

    def call(self, key, args, default=SENTINEL, **kw):
        """Call function based on multiple dispatch on args.

        :param key: Call function for this key.
        :type key: hashable object, normally function.
        :param args: Call function with these arguments.
        :type args: list of objects.
        :param default: default value to return if lookup fails.
        :type default: object.
        :param kw: extra keyword arguments passed to the function called.
        :returns: result of function call.
        :raises: ComponentLookupError

        The behavior of this method is like that of component, but it
        performs an extra step: it calls the found component with the
        args given as arguments.

        This amounts to an implementation of multiple dispatch: zero
        or more arguments can be used to dispatch the function on.
        """
        adapter = self.component(key, args, default)
        if adapter is default:
            return default
        result = adapter(*args, **kw)
        if result is not None:
            return result
        if default is not SENTINEL:
            return default
        raise ComponentLookupError(
            "%r: no function found for args %r" % (
                key, args))

    def all(self, key, args):
        """Lookup up all components registered for args.

        :param key: Look up components for this key.
        :type key: hashable object, normally function.
        :param args: Look up components for these arguments.
        :type args: list of objects.
        :returns: iterable of registered components.

        The behavior of this method is like that of component, but it
        looks up *all* the matching components for the arguments. This
        means that if one component is registered for a class and
        another for its base class, ``all()`` with an instance of the
        class as its argument will return both components.

        Will check whether the found component is an Matcher, in
        which case it will be called with args. If non-None is
        returned, the found value is included as a matching component.

        If no components can be found, the iterable will be empty.
        """
        for found in self.class_lookup.all(
                key, [arg.__class__ for arg in args]):
            if isinstance(found, Matcher):
                found = found(*args)
            if found is not None:
                yield found
