from __future__ import unicode_literals
from functools import update_wrapper
from .predicate import match_argname
from .compat import string_types
from .registry import Registry
from .reify import reify


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
        self.registry = Registry()
        self.predicates = predicates
        self.wrapped_func = callable
        self.external_predicates = external_predicates
        # self.registry.register_dispatch(self)

    def register(self, value, **key_dict):
        self.registry.register_function(self, value, **key_dict)

    def register_external_predicates(self, predicates):
        self.registry.register_external_predicates(self, predicates)

    def register_dispatch_predicates(self, predicates):
        self.registry.register_dispatch_predicates(self, predicates)

    def __repr__(self):
        return repr(self.wrapped_func)

    @reify
    def _lookup(self):
        self.registry.register_dispatch(self)
        return self.registry.lookup

    def __call__(self, *args, **kw):
        return self._lookup().call(self.wrapped_func, *args, **kw)

    def component(self, *args, **kw):
        return self._lookup().component(self.wrapped_func, *args, **kw)

    def fallback(self, *args, **kw):
        return self._lookup().fallback(self.wrapped_func, *args, **kw)

    def component_key_dict(self, **kw):
        return self._lookup().component_key_dict(self.wrapped_func, kw)

    def all(self, *args, **kw):
        return self._lookup().all(self.wrapped_func, *args, **kw)

    def all_key_dict(self, **kw):
        return self._lookup().all_key_dict(self.wrapped_func, kw)

    def key_dict_to_predicate_key(self, key_dict):
        self.registry.register_dispatch(self)
        return self.registry.key_dict_to_predicate_key(
            self.wrapped_func, key_dict)
