from __future__ import unicode_literals
from functools import update_wrapper
from reg.implicit import implicit, NoImplicitLookupError
from reg.lookup import ComponentLookupError
from reg.mapply import lookup_mapply
from reg.neopredicate import match_argname


def generic(func):
    """Turn a function into a generic function.

    :param func: Function to turn into a multiple dispatch function.
    :type func: function.
    :returns: multiple dispatch version of function.

    When someone calls the wrapped function, the arguments determine
    what actual function will be called. In particular the classes of
    the arguments are inspected. For each combination of arguments a
    different function can be registered.

    The function itself provides a default implementation in case no
    more specific registered function can be found for its arguments.

    Can be used as a decorator::

      @reg.generic
      def my_function(...):
          ...
    """

    def wrapper(*args, **kw):
        lookup = get_lookup(kw)
        try:
            return lookup.call(func, *args, **kw)
        except ComponentLookupError:
            return lookup_mapply(func, lookup, *args, **kw)

    def component(*args, **kw):
        """Look up registered component for function and arguments.

        Does a dynamic lookup based on the classes of the arguments and
        returns whatever was registered (not calling it).
        """
        return get_lookup(kw).component(func, *args, **kw)

    def all(*args, **kw):
        """Look up all registered components for function and arguments.

        For all combinations of argument classes, returns an iterable of
        whatever was registered for this function.
        """
        return get_lookup(kw).all(func, *args, **kw)

    wrapper.wrapped_func = func
    wrapper.component = component
    wrapper.all = all
    update_wrapper(wrapper, func)
    return wrapper


class dispatch(object):
    def __init__(self, *predicates):
        self.predicates = [self.make_predicate(predicate)
                           for predicate in predicates]

    def make_predicate(self, predicate):
        if isinstance(predicate, basestring):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        return Dispatch(self.predicates, callable)


class Dispatch(object):
    def __init__(self, predicates, callable):
        self.predicates = predicates
        self.wrapped_func = callable

    def __call__(self, *args, **kw):
        lookup = get_lookup(kw)
        try:
            return lookup.call(self.wrapped_func, *args, **kw)
        except ComponentLookupError:
            return lookup_mapply(self.wrapped_func, lookup, *args, **kw)

    def component(self, *args, **kw):
        return get_lookup(kw).component(self.wrapped_func, *args, **kw)

    def all(self, *args, **kw):
        return get_lookup(kw).all(self.wrapped_func, *args, **kw)


def classgeneric(func):
    """Turn a function into a generic class function, like @classmethod.

    :param func: Function to turn into a multiple dispatch function.
    :type func: function.
    :returns: multiple dispatch version of function.

    When someone calls the wrapped function, the arguments determine
    what actual function will be called. In case of the first
    argument, the argument should be a class. For the other arguments,
    the classes of the arguments are used instead. For each
    combination of arguments a different function can be registered.

    The function itself provides a default implementation in case no
    more specific registered function can be found for its arguments.

    Can be used as a decorator::

      @reg.classgeneric
      def my_function(...):
          ...
    """
    def wrapper(*args, **kw):
        lookup = get_lookup(kw)
        try:
            return lookup.call(wrapper, args, class_method=True, **kw)
        except ComponentLookupError:
            return lookup_mapply(func, lookup, *args, **kw)

    def component(*args, **kw):
        """Look up registered component for function and arguments.

        Does a dynamic lookup based on the classes of the arguments and
        returns whatever was registered (not calling it).
        """
        return get_lookup(kw).component(wrapper, args, class_method=True, **kw)

    def all(*args, **kw):
        """Look up all registered components for function and arguments.

        For all combinations of argument classes, returns an iterable of
        whatever was registered for this function.
        """
        return get_lookup(kw).all(wrapper, args, class_method=True, **kw)

    wrapper.component = component
    wrapper.all = all
    update_wrapper(wrapper, func)
    return wrapper


def get_lookup(kw):
    """Find ILookup to use.

    First inspects ``kw``, a dictionary of keyword arguments given for
    an argument called ``lookup``. If that cannot be found, fall back
    on a global ``implicit.lookup``. If no such lookup is available,
    raise a ``NoImplicitLookupError``.
    """
    lookup = kw.pop('lookup', implicit.lookup)
    if lookup is None:
        raise NoImplicitLookupError(
            "Cannot lookup without explicit lookup argument "
            "because no implicit lookup was configured.")
    return lookup
