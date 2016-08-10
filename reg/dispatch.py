from __future__ import unicode_literals
from functools import update_wrapper, partial
from .predicate import match_argname
from .compat import string_types
from .predicate import create_predicates_registry, Lookup
from .arginfo import arginfo
from .error import RegistrationError


class dispatch(object):
    """Decorator to make a function dispatch based on its arguments.

    This takes the predicates to dispatch on as zero or more parameters.

    :param predicates: sequence of :class:`Predicate` instances
      to do the dispatch on.
    """
    def __init__(self, *predicates, **kw):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]
        self.get_key_lookup = kw.pop('get_key_lookup', identity)

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        result = Dispatch(self.predicates, callable, self.get_key_lookup)
        update_wrapper(result, callable)
        return result


def identity(registry):
    return registry


class Dispatch(object):
    def __init__(self, predicates, callable, get_key_lookup):
        self.wrapped_func = callable
        self.get_key_lookup = get_key_lookup
        self._register_predicates(predicates)

    def _register_predicates(self, predicates):
        self.registry = create_predicates_registry(predicates)
        self.predicates = predicates
        # (re)initialize the lookup and the cache
        self.lookup = Lookup(self.wrapped_func,
                             self.get_key_lookup(self.registry))

    def add_predicates(self, predicates):
        self._register_predicates(self.predicates + predicates)

    def register(self, value, **key_dict):
        validate_signature(value, self.wrapped_func)
        predicate_key = self.registry.key_dict_to_predicate_key(key_dict)
        self.register_value(predicate_key, value)

    def register_value(self, predicate_key, value):
        if isinstance(predicate_key, list):
            predicate_key = tuple(predicate_key)
        # if we have a 1 tuple, we register the single value inside
        if isinstance(predicate_key, tuple) and len(predicate_key) == 1:
            predicate_key = predicate_key[0]
        self.registry.register(predicate_key, value)

    def __repr__(self):
        return repr(self.wrapped_func)

    def __call__(self, *args, **kw):
        return self.lookup.call(*args, **kw)

    def component(self, *args, **kw):
        return self.lookup.component(*args, **kw)

    def fallback(self, *args, **kw):
        return self.lookup.fallback(*args, **kw)

    def component_key_dict(self, **kw):
        return self.lookup.component_key_dict(kw)

    def all(self, *args, **kw):
        return self.lookup.all(*args, **kw)

    def all_key_dict(self, **kw):
        return self.lookup.all_key_dict(kw)

    def key_dict_to_predicate_key(self, key_dict):
        return self.registry.key_dict_to_predicate_key(key_dict)


class dispatch_method(object):
    def __init__(self, *predicates, **kw):
        self.predicates = predicates
        self.get_key_lookup = kw.pop('get_key_lookup', identity)

    def __call__(self, callable):
        return MethodDispatchDescriptor(callable,
                                        self.predicates,
                                        self.get_key_lookup)



class MethodDispatchDescriptor(object):
    def __init__(self, callable, predicates, get_key_lookup):
        self.callable = callable
        self.name = self.callable.__name__
        self.predicates = predicates
        self.get_key_lookup = get_key_lookup
        self._cache = {}

    def __get__(self, obj, type=None):
        # we get the method from the cache
        # this guarantees that we distinguish between dispatches
        # on a per class basis, and on the name of the method
        method = self._cache.get(type)

        if method is None:
            # if this is the first time we access the dispatch method,
            # we create it and store it in the cache
            method = Dispatch(self.predicates,
                              self.callable,
                              self.get_key_lookup)
            self._cache[type] = method

        # we cannot attach the dispatch method to the class
        # directly (skipping the descriptor during next access) here,
        # because we need to return a distinct dispatch for each
        # class, including subclasses.
        if obj is None:
            # we access it through the class directly, so unbound
            return method
        else:
            # if we access the instance, we simulate binding it
            bound = partial(method, obj)
            # we store it on the instance, so that next time we
            # access this, we do not hit the descriptor anymore
            # but return the bound dispatch function directly
            setattr(obj, self.name, bound)
            return bound


def validate_signature(f, dispatch):
    f_arginfo = arginfo(f)
    if f_arginfo is None:
        raise RegistrationError(
            "Cannot register non-callable for dispatch "
            "method %r: %r" % (dispatch, f))
    if not same_signature(arginfo(dispatch), f_arginfo):
        raise RegistrationError(
            "Signature of callable dispatched to (%r) "
            "not that of dispatch method (%r)" % (
                f, dispatch))


def same_signature(a, b):
    """Check whether a arginfo and b arginfo are the same signature.

    Signature may have an extra 'lookup' argument. Actual names of
    argument may differ. Default arguments may be different.
    """
    a_args = set(a.args)
    b_args = set(b.args)
    a_args.discard('lookup')
    b_args.discard('lookup')
    return (len(a_args) == len(b_args) and
            a.varargs == b.varargs and
            a.keywords == b.keywords)
