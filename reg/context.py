from __future__ import unicode_literals
import inspect
from types import MethodType
from .dispatch import dispatch, Dispatch, format_signature, execute
from .arginfo import arginfo


class dispatch_method(dispatch):
    """Decorator to make a method on a context class dispatch.

    This takes the predicates to dispatch on as zero or more parameters.

    :param predicates: sequence of :class:`Predicate` instances to do
      the dispatch on. You create predicates using
      :func:`reg.match_instance`, :func:`reg.match_key`,
      :func:`reg.match_class`, or with a custom predicate class.

      You can also pass in plain string argument, which is turned into
      a :func:`reg.match_instance` predicate.
    :param get_key_lookup: a function that gets a
      :class:`PredicateRegistry` instance and returns a key lookup. A
      :class:`PredicateRegistry` instance is itself a key lookup, but
      you can return a caching key lookup (such as
      :class:`reg.DictCachingKeyLookup` or
      :class:`reg.LruCachingKeyLookup`) to make it more efficient.
    :param first_invocation_hook: a callable that accepts an instance of the
      class in which this decorator is used. It is invoked the first
      time the method is invoked.

    """
    def __init__(self, *predicates, **kw):
        self.first_invocation_hook = kw.pop(
            'first_invocation_hook', lambda x: None)
        super(dispatch_method, self).__init__(*predicates, **kw)
        self._cache = {}

    def __call__(self, callable):
        self.callable = callable
        return self

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
                                      self.get_key_lookup).call
            self._cache[type] = dispatch

        # we cannot attach the dispatch method to the class
        # directly (skipping the descriptor during next access) here,
        # because we need to return a distinct dispatch for each
        # class, including subclasses.
        if obj is None:
            # we access it through the class directly, so unbound
            return dispatch

        self.first_invocation_hook(obj)

        # if we access the instance, we simulate binding it
        bound = MethodType(dispatch, obj)
        # we store it on the instance, so that next time we
        # access this, we do not hit the descriptor anymore
        # but return the bound dispatch function directly
        setattr(obj, self.callable.__name__, bound)
        return bound


class DispatchMethod(Dispatch):

    def by_args(self, *args, **kw):
        """Lookup an implementation by invocation arguments.

        :param args: positional arguments used in invocation.
        :param kw: named arguments used in invocation.
        :returns: a :class:`reg.LookupEntry`.
        """
        return super(DispatchMethod, self).by_args(None, *args, **kw)


def methodify(func, selfname=None):
    """Turn a function into a method, if needed.

    If ``selfname`` is not specified, wrap the function so that it
    takes an additional first argument, like a method.

    If ``selfname`` is specified, check whether it is the same as the
    name of the first argument of ``func``. If itsn't, wrap the
    function so that it takes an additional first argument, with the
    name specified by ``selfname``.

    If it is, the signature of ``func`` needn't be amended, but
    wrapping might still be necessary.

    In all cases, :func:`inspect_methodified` lets you retrieve the wrapped
    function.

    :param func: the function to turn into method.

    :param selfname: if specified, the name of the argument
      referencing the class instance.  Typically, ``"self"``.

    :returns: function that can be used as a method when assigned to a
      class.

    """
    args = arginfo(func)
    if args is None:
        raise TypeError("methodify must take a callable")
    if args.args[:1] != [selfname]:
        # Add missing self to the signature:
        code_template = (
            "def wrapper({selfname}, {signature}): return _func({signature})")
    elif inspect.ismethod(func):
        # Bound method: must be wrapped despite same signature:
        code_template = (
            "def wrapper({signature}): return _func({signature})")
    else:
        # No wrapping needed:
        return func
    code_source = code_template.format(
        signature=format_signature(args),
        selfname=selfname or '_')
    return execute(code_source, _func=func)['wrapper']


def clean_dispatch_methods(cls):
    """For a given class clean all dispatch methods.

    This resets their registry to the original state using
    :meth:`reg.DispatchMethod.clean`.

    :param cls: a class that has :class:`reg.DispatchMethod` methods on it.
    """
    for name in dir(cls):
        attr = getattr(cls, name)
        if inspect.isfunction(attr) and hasattr(attr, 'clean'):
            attr.clean()
