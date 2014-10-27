from __future__ import unicode_literals
from functools import update_wrapper
from .implicit import implicit, NoImplicitLookupError
from .predicate import match_argname
from .compat import string_types


class dispatch(object):
    """Decorator to make a function dispatch based on its arguments.

    :param predicates: sequence of :class:`Predicate` instances
      to do the dispatch on.
    """
    def __init__(self, *predicates):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        result = Dispatch(self.predicates, callable)
        update_wrapper(result, callable)
        return result


class Dispatch(object):
    def __init__(self, predicates, callable):
        self.predicates = predicates
        self.wrapped_func = callable

    def __call__(self, *args, **kw):
        lookup = get_lookup(kw)
        return lookup.call(self.wrapped_func, *args, **kw)

    def component(self, *args, **kw):
        return get_lookup(kw).component(self.wrapped_func, *args, **kw)

    def all(self, *args, **kw):
        return get_lookup(kw).all(self.wrapped_func, *args, **kw)


def get_lookup(kw):
    """Find lookup to use.

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
