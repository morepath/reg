from __future__ import unicode_literals
from functools import update_wrapper
import types
import inspect
from .predicate import match_argname
from .compat import (string_types, create_method_for_class,
                     create_method_for_instance)
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
        self._original_predicates = predicates
        self._register_predicates(predicates)

    def _register_predicates(self, predicates):
        self.registry = create_predicates_registry(predicates)
        self.predicates = predicates
        # (re)initialize the lookup and the cache
        self.lookup = Lookup(self.wrapped_func,
                             self.get_key_lookup(self.registry))

    def clean(self):
        self._register_predicates(self._original_predicates)

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


class dispatch_method(dispatch):
    def __init__(self, *predicates, **kw):
        super(dispatch_method, self).__init__(*predicates, **kw)

    def __call__(self, callable):
        return MethodDispatchDescriptor(callable,
                                        self.predicates,
                                        self.get_key_lookup)


class MethodDispatch(Dispatch):
    def __init__(self, predicates, callable, get_key_lookup,
                 auto_argument='app'):
        super(MethodDispatch, self).__init__(
            predicates, callable, get_key_lookup)
        self.auto_argument = auto_argument

    def register_function(self, value, **key_dict):
        validate_signature_without_first_arg(value, self.wrapped_func)
        predicate_key = self.registry.key_dict_to_predicate_key(key_dict)
        self.register_value(predicate_key, methodify(value))

    def register_auto(self, value, **key_dict):
        if is_auto_method(value, self.auto_argument):
            # for symmetry as register_function with a wrapped version
            # is possible, we also set the value
            value.value = value
            self.register(value, **key_dict)
        else:
            self.register_function(value, **key_dict)

    def component(self, *args, **kw):
        return self.lookup.component(None, *args, **kw)

    def fallback(self, *args, **kw):
        return self.lookup.fallback(None, *args, **kw)

    def all(self, *args, **kw):
        return self.lookup.all(None, *args, **kw)


class MethodDispatchDescriptor(object):
    def __init__(self, callable, predicates, get_key_lookup,
                 cache_bound_method=True):
        self.callable = callable
        self.name = self.callable.__name__
        self.predicates = predicates
        self.get_key_lookup = get_key_lookup
        self.cache_bound_method = cache_bound_method
        self._cache = {}

    def __get__(self, obj, type=None):
        # we get the method from the cache
        # this guarantees that we distinguish between dispatches
        # on a per class basis, and on the name of the method
        dispatch = self._cache.get(type)

        if dispatch is None:
            # if this is the first time we access the dispatch method,
            # we create it and store it in the cache
            dispatch = MethodDispatch(self.predicates,
                                      self.callable,
                                      self.get_key_lookup)
            self._cache[type] = dispatch

        # we cannot attach the dispatch method to the class
        # directly (skipping the descriptor during next access) here,
        # because we need to return a distinct dispatch for each
        # class, including subclasses.
        if obj is None:
            # we access it through the class directly, so unbound
            return create_method_for_class(dispatch, type)

        # if we access the instance, we simulate binding it
        bound = create_method_for_instance(dispatch, obj)
        # we store it on the instance, so that next time we
        # access this, we do not hit the descriptor anymore
        # but return the bound dispatch function directly
        if self.cache_bound_method:
            setattr(obj, self.name, bound)
        return bound


def validate_signature(f, dispatch):
    f_arginfo = arginfo(f)
    if f_arginfo is None:
        raise RegistrationError(
            "Cannot register non-callable for dispatch "
            "%r: %r" % (dispatch, f))
    if not same_signature(arginfo(dispatch), f_arginfo):
        raise RegistrationError(
            "Signature of callable dispatched to (%r) "
            "not that of dispatch (%r)" % (
                f, dispatch))


def validate_signature_without_first_arg(f, dispatch):
    f_arginfo = arginfo(f)
    if f_arginfo is None:
        raise RegistrationError(
            "Cannot register non-callable for dispatch "
            "%r: %r" % (dispatch, f))

    dispatch_arginfo = arginfo(dispatch)
    # strip off first argument (as this is self or cls)
    dispatch_arginfo = inspect.ArgInfo(
        dispatch_arginfo.args[1:],
        dispatch_arginfo.varargs,
        dispatch_arginfo.keywords,
        dispatch_arginfo.defaults)
    if not same_signature(dispatch_arginfo, f_arginfo):
        raise RegistrationError(
            "Signature of callable dispatched to (%r) "
            "not that of dispatch (without self) (%r)" % (
                f, dispatch))


def same_signature(a, b):
    """Check whether a arginfo and b arginfo are the same signature.

    Actual names of arguments may differ. Default arguments may be
    different.
    """
    a_args = set(a.args)
    b_args = set(b.args)
    return (len(a_args) == len(b_args) and
            a.varargs == b.varargs and
            a.keywords == b.keywords)


def methodify(func):
    """Turn a function into a method.

    Wraps the function so that it takes a first argument like
    a method, and ignores it.

    The return value has a ``value`` attribute which is the original
    function that was wrapped. This way the application can access it.
    """
    def wrapped(self, *args, **kw):
        return func(*args, **kw)
    wrapped.value = func
    return wrapped


def is_auto_method(func, auto_argument="app"):
    """Check whether a function is already a method
    """
    info = arginfo(func)
    return info.args and info.args[0] == auto_argument


def auto_methodify(func, auto_argument="app"):
    """Turn a function into a method if needed.

    A function is identified to be a method if its first
    argument name is ``auto_argument``.

    Otherwise it is assumed to be a plain function, and a wrapper
    function is created which takes a first argument and ignores it.

    The return value has a ``value`` attribute which is the original
    function that was wrapped. This way the application can access it.
    """
    if is_auto_method(func, auto_argument):
        # for symmetry make sure value is set
        if not isinstance(func, types.FunctionType):
            f = func.__func__
        else:
            f = func
        f.value = func
        return func
    else:
        return methodify(func)


def clean_dispatch_methods(cls):
    """For a given class clean all dispatch methods.

    This resets their registry to the original state.
    """
    for name in dir(cls):
        attr = getattr(cls, name)
        im_func = getattr(attr, '__func__', None)
        if im_func is None:
            continue
        if isinstance(im_func, MethodDispatch):
            attr.clean()
