from __future__ import unicode_literals
from functools import update_wrapper
from reg.implicit import implicit, NoImplicitLookupError
from reg.mapply import lookup_mapply
from reg.predicate import match_argname


class dispatch(object):
    def __init__(self, *predicates):
        self.predicates = [self.make_predicate(predicate)
                           for predicate in predicates]

    def make_predicate(self, predicate):
        if isinstance(predicate, basestring):
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
