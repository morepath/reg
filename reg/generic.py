from __future__ import unicode_literals
from functools import update_wrapper
from reg.implicit import implicit, NoImplicitLookupError
from reg.lookup import ComponentLookupError
from reg.mapply import mapply


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

    def wrapper(*args, **kw):
        lookup = get_lookup(kw)
        try:
            return lookup.call(wrapper, args, **kw)
        except ComponentLookupError:
            return mapply(func, *args, lookup=lookup, **kw)

    def component(*args, **kw):
        """Look up registered component for function and arguments.

        Does a dynamic lookup based on the classes of the arguments and
        returns whatever was registered (not calling it).
        """
        return get_lookup(kw).component(wrapper, args, **kw)

    def all(*args, **kw):
        """Look up all registered components for function and arguments.

        For all combinations of argument classes, returns an iterable of
        whatever was registered for this function.
        """
        return get_lookup(kw).all(wrapper, args, **kw)

    wrapper.component = component
    wrapper.all = all
    update_wrapper(wrapper, func)
    return wrapper
