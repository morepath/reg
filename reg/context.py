from __future__ import unicode_literals
from functools import update_wrapper
from types import MethodType
from .compat import create_method_for_class
from .dispatch import (dispatch, Dispatch,
                       format_signature, execute)
from .arginfo import arginfo


class dispatch_method(dispatch):
    """Decorator to make a method on a context class dispatch.

    This takes the predicates to dispatch on as zero or more parameters.

    :param predicates: sequence of :class:`Predicate` instances
      to do the dispatch on. You create predicates using
      :func:`reg.match_instance`, :func:`reg.match_key`,
      :func:`reg.match_class`, or :func:`reg.match_argname`, or with a
      custom predicate class.

      You can also pass in plain string argument, which is turned into
      a :func:`reg.match_instance` predicate.
    :param get_key_lookup: a function that gets a :class:`PredicateRegistry`
      instance and returns a key lookup. A :class:`PredicateRegistry` instance
      is itself a key lookup, but you can return :class:`reg.CachingKeyLookup`
      to make it more efficient.
    :param first_invocation_hook: a callable that accepts an instance of the
      class in which this decorator is used. It is invoked the first
      time the method is invoked.
    :returns: a :class:`reg.DispatchMethod` instance.
    """
    def __init__(self, *predicates, **kw):
        self.first_invocation_hook = kw.pop(
            'first_invocation_hook', lambda x: None)
        super(dispatch_method, self).__init__(*predicates, **kw)

    def __call__(self, callable):
        return DispatchMethodDescriptor(callable,
                                        self.predicates,
                                        self.get_key_lookup,
                                        self.first_invocation_hook)


class DispatchMethod(Dispatch):
    def __init__(self, predicates, callable, get_key_lookup):
        super(DispatchMethod, self).__init__(
            predicates, callable, get_key_lookup)

    def component(self, *args, **kw):
        # pass in a None as the first argument
        # this matches up the bound self that is passed automatically
        # into __call__
        return super(DispatchMethod, self).component(None, *args, **kw)

    def fallback(self, *args, **kw):
        return super(DispatchMethod, self).fallback(None, *args, **kw)

    def all(self, *args, **kw):
        return super(DispatchMethod, self).all(None, *args, **kw)


class DispatchMethodDescriptor(object):
    def __init__(self, callable, predicates, get_key_lookup,
                 first_invocation_hook, cache_bound_method=True):
        self.callable = callable
        self.name = self.callable.__name__
        self.predicates = predicates
        self.get_key_lookup = get_key_lookup
        self.cache_bound_method = cache_bound_method
        self._cache = {}
        self.first_invocation_hook = first_invocation_hook

    def __get__(self, obj, type=None):
        # we get the method from the cache
        # this guarantees that we distinguish between dispatches
        # on a per class basis, and on the name of the method

        dispatch = self._cache.get(type)

        if dispatch is None:
            # if this is the first time we access the dispatch method,
            # we create it and store it in the cache
            dispatch = DispatchMethod(self.predicates,
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

        self.first_invocation_hook(obj)

        # if we access the instance, we simulate binding it
        bound = MethodType(dispatch, obj)
        # we store it on the instance, so that next time we
        # access this, we do not hit the descriptor anymore
        # but return the bound dispatch function directly
        if self.cache_bound_method:
            setattr(obj, self.name, bound)
        return bound


def _wrap(func, prefix_signature=''):
    """Wrap a function potentially with some additional prefix arguments.

    :param func: the function to turn into method.
    :param prefix_signature: extra text to prepend to signature.
    :returns: wrapped function.
    """
    args = arginfo(func)
    code_template = """\
def wrapper({prefix_signature} {signature}):
    return _wrapped({signature})
"""

    code_source = code_template.format(signature=format_signature(args),
                                       prefix_signature=prefix_signature)

    wrapper = execute(
        code_source,
        _wrapped=func)['wrapper']
    wrapper._wrapped_func = func
    update_wrapper(wrapper, func)
    return wrapper


def methodify(func, auto_argument='app'):
    """Turn a function into a method only if it isn't one already.

    Wraps the function so that it takes a first argument like
    a method, and ignores it. The return value can be attached to
    a class as a method. It can also be turned back into the original
    function using :func:`reg.unmethodify`.

    If the name of the first argument is ``auto_argument``, func is
    returned. If it isn't, then the function is wrapped so that it
    takes a first argument like a method (and ignores it).

    The return value has a ``value`` attribute which is the original
    function that was wrapped. This way the application can access it.

    :param func: the function to install as a method. If its first
      argument name is *not* ``auto_argument``, it is first wrapped
      into an object that does take a first argument, so that it can
      be installed as a method.
    :param auto_argument: the name of the first argument that indicates
      we want to install this directly as a method. If the first argument
      does not have this name, wrap the callable so that it does take
      that argument before installing it.
    :returns: function that can be attached to a class as a method.
    """
    info = arginfo(func)
    if info is None:
        raise TypeError("methodify must take a callable")
    # if we already have the proper first argument
    if info.args and info.args[0] == auto_argument:
        # we still need to wrap it if it's an instance method
        if isinstance(func, MethodType):
            return _wrap(func)
        return func
    return _wrap(func, '_self, ')


def unmethodify(func):
    """Reverses methodify operation.

    Given an object that is returned from a call to
    :func:`reg.methodify` return the original object. This can be used to
    discover the original object that was registered. You can apply
    this to a function after it was attached as a method.

    :param func: the methodified function.
    :returns: the original function.
    """
    wrapped_func = getattr(func, '_wrapped_func', None)
    if wrapped_func is not None:
        return wrapped_func
    return getattr(func, '__func__', func)


def clean_dispatch_methods(cls):
    """For a given class clean all dispatch methods.

    This resets their registry to the original state using
    :meth:`reg.DispatchMethod.clean`.

    :param cls: a class that has :class:`reg.DispatchMethod` methods on it.
    """
    for name in dir(cls):
        attr = getattr(cls, name)
        im_func = getattr(attr, '__func__', None)
        if im_func is None:
            continue
        if isinstance(im_func, DispatchMethod):
            attr.clean()
