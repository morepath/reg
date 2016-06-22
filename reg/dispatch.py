from __future__ import unicode_literals
from functools import update_wrapper
from .implicit import implicit
from .error import NoImplicitLookupError
from .predicate import match_argname
from .compat import string_types


class dispatch(object):
    """Decorator to make a function dispatch based on its arguments.

    This takes the predicates to dispatch on as zero or more parameters.

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


class dispatch_external_predicates(object):
    """Decorator to make function dispatch based on external predicates.

    The predicates to dispatch on are defined in the :class:`Registry`
    object using :class:`register_external_predicates`. If no
    external predicates were registered then this is an error.
    """
    def __call__(self, callable):
        result = Dispatch([], callable, external_predicates=True)
        update_wrapper(result, callable)
        return result


class Dispatch(object):
    def __init__(self, predicates, callable, external_predicates=False):
        self.predicates = predicates
        self.wrapped_func = callable
        self.external_predicates = external_predicates

    def __repr__(self):
        return repr(self.wrapped_func)

    def __call__(self, *args, **kw):
        lookup = get_lookup(kw)
        return lookup.call(self.wrapped_func, *args, **kw)

    def component(self, *args, **kw):
        return get_lookup(kw).component(self.wrapped_func, *args, **kw)

    def fallback(self, *args, **kw):
        return get_lookup(kw).fallback(self.wrapped_func, *args, **kw)

    def component_key_dict(self, **kw):
        return get_lookup(kw).component_key_dict(self.wrapped_func, kw)

    def all(self, *args, **kw):
        return get_lookup(kw).all(self.wrapped_func, *args, **kw)

    def all_key_dict(self, **kw):
        return get_lookup(kw).all_key_dict(self.wrapped_func, kw)


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
