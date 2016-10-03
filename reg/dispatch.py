from __future__ import unicode_literals
from functools import partial, wraps
from .predicate import match_instance
from .compat import string_types
from .predicate import create_predicates_registry
from .arginfo import arginfo
from .error import RegistrationError


class dispatch(object):
    """Decorator to make a function dispatch based on its arguments.

    This takes the predicates to dispatch on as zero or more
    parameters.

    :param predicates: sequence of :class:`reg.Predicate` instances to
      do the dispatch on. You create predicates using
      :func:`reg.match_instance`, :func:`reg.match_key`,
      :func:`reg.match_class`, or with a custom predicate class. You
      can also pass in plain string argument, which is turned into a
      :func:`reg.match_instance` predicate.
    :param get_key_lookup: a function that gets a
      :class:`PredicateRegistry` instance and returns a key lookup. A
      :class:`PredicateRegistry` instance is itself a key lookup, but
      you can return a caching key lookup (such as
      :class:`reg.DictCachingKeyLookup` or
      :class:`reg.LruCachingKeyLookup`) to make it more efficient.
    :returns: a function that you can use as if it were a
      :class:`reg.Dispatch` instance.

    """
    def __init__(self, *predicates, **kw):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]
        self.get_key_lookup = kw.pop('get_key_lookup', identity)

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_instance(predicate)
        return predicate

    def __call__(self, callable):
        return Dispatch(self.predicates, callable, self.get_key_lookup).call


def identity(registry):
    return registry


class Dispatch(object):
    """Dispatch function.

    You can register implementations based on particular predicates. The
    dispatch function dispatches to these implementations based on its
    arguments.

    :param predicates: a list of predicates.
    :param callable: the Python function object to register dispatch
      implementations for. The signature of an implementation needs to
      match that of this function. This function is used as a fallback
      implementation that is called if no specific implementations match.
    :param get_key_lookup: a function that gets a
      :class:`PredicateRegistry` instance and returns a key lookup. A
      :class:`PredicateRegistry` instance is itself a key lookup, but
      you can return a caching key lookup (such as
      :class:`reg.DictCachingKeyLookup` or
      :class:`reg.LruCachingKeyLookup`) to make it more efficient.
    """
    def __init__(self, predicates, callable, get_key_lookup):
        self.wrapped_func = callable
        self.get_key_lookup = get_key_lookup
        self._original_predicates = predicates
        self._define_call()
        self._register_predicates(predicates)

    def _register_predicates(self, predicates):
        self.registry = create_predicates_registry(predicates)
        self.predicates = predicates
        self.call.key_lookup = self.key_lookup = \
            self.get_key_lookup(self.registry)
        self.call.__globals__.update(
            _registry_key=self.registry.key,
            _component_lookup=self.key_lookup.component,
            _fallback_lookup=self.key_lookup.fallback,
        )
        self._predicate_key.__globals__.update(
            _registry_key=self.registry.key,
        )

    def _define_call(self):
        # We build the generic function on the fly. Its definition
        # requires the signature of the wrapped function and the
        # arguments needed by the registered predicates
        # (predicate_args):
        code_template = """\
def call({signature}):
    _key = _registry_key({predicate_args})
    return (_component_lookup(_key) or
            _fallback_lookup(_key) or
            _fallback)({signature})
"""

        args = arginfo(self.wrapped_func)
        signature = format_signature(args)
        predicate_args = ', '.join('{0}={0}'.format(x) for x in args.args)
        code_source = code_template.format(
            signature=signature,
            predicate_args=predicate_args)

        # We now compile call to byte-code:
        self.call = call = wraps(self.wrapped_func)(execute(
            code_source,
            _registry_key=None,
            _component_lookup=None,
            _fallback_lookup=None,
            _fallback=self.wrapped_func)['call'])

        # We copy over the defaults from the wrapped function.
        call.__defaults__ = args.defaults

        # Make the methods available as attributes of call
        for k in dir(type(self)):
            if not k.startswith('_'):
                setattr(call, k, getattr(self, k))
        call.wrapped_func = self.wrapped_func

        # We now build the implementation for the predicate_key method
        self._predicate_key = execute(
            "def predicate_key({signature}):\n"
            "    return _registry_key({predicate_args})".format(
                signature=format_signature(args),
                predicate_args=predicate_args),
            _registry_key=None)['predicate_key']

    def clean(self):
        """Clean up implementations and added predicates.

        This restores the dispatch function to its original state,
        removing registered implementations and predicates added
        using :meth:`reg.Dispatch.add_predicates`.
        """
        self._register_predicates(self._original_predicates)

    def add_predicates(self, predicates):
        """Add new predicates.

        Extend the predicates used by this predicates. This can be
        used to add predicates that are configured during startup time.

        Note that this clears up any registered implementations.

        :param predicates: a list of predicates to add.
        """
        self._register_predicates(self.predicates + predicates)

    def register(self, func=None, **key_dict):
        """Register an implementation.

        If ``func`` is not specified, this method can be used as a
        decorator and the decorated function will be used as the
        actual ``func`` argument.

        :param func: a function that implements behavior for this
          dispatch function. It needs to have the same signature as
          the original dispatch function. If this is a
          :class:`reg.DispatchMethod`, then this means it needs to
          take a first context argument.
        :param key_dict: keyword arguments describing the registration,
          with as keys predicate name and as values predicate values.
        :returns: ``func``.
        """
        if func is None:
            return partial(self.register, **key_dict)
        validate_signature(func, self.wrapped_func)
        predicate_key = self.registry.key_dict_to_predicate_key(key_dict)
        self.registry.register(predicate_key, func)
        return func

    def predicate_key(self, *args, **kw):
        """Construct predicate_key for function arguments.

        For function arguments, construct the appropriate
        ``predicate_key``. This is used by the dispatch mechanism to
        dispatch to the right function.

        If the ``predicate_key`` cannot be constructed from ``args``
        and ``kw``, this raises a :exc:`TypeError`.

        :param args: the varargs given to the callable.
        :param kw: the keyword arguments given to the callable.
        :returns: an immutable ``predicate_key`` based on the predicates
          the callable was configured with.
        """
        return self._predicate_key(*args, **kw)

    def component(self, *args, **kw):
        """Lookup function dispatched to with args and kw.

        Looks up the function to dispatch to using args and
        kw. Returns the fallback value (default: ``None``) if nothing
        could be found.

        :args: varargs. Used to extract dispatch information to
           construct ``predicate_key``.
        :kw: keyword arguments. Used to extract
           dispatch information to construct ``predicate_key``.
        :returns: the function being dispatched to, or None.
        """
        key = self.predicate_key(*args, **kw)
        return self.key_lookup.component(key)

    def fallback(self, *args, **kw):
        """Lookup fallback for args and kw.

        :args: varargs. Used to extract dispatch information to
           construct ``predicate_key``.
        :kw: keyword arguments. Used to extract
           dispatch information to construct ``predicate_key``.
        :returns: the function being dispatched to, or fallback.
        """
        key = self.predicate_key(*args, **kw)
        return self.key_lookup.fallback(key)

    def component_by_keys(self, **kw):
        """Look up function based on key_dict.

        Looks up the function to dispatch to using a key_dict,
        mapping predicate name to predicate value. Returns the fallback
        value (default: ``None``) if nothing could be found.

        :kw: key is predicate name, value is
          predicate value under which it was registered.
          If omitted, predicate default is used.
        :returns: the function being dispatched to, or fallback.
        """
        key = self.key_lookup.key_dict_to_predicate_key(kw)
        return self.key_lookup.component(key)

    def all(self, *args, **kw):
        """Lookup all functions dispatched to with args and kw.

        Looks up functions for all permutations based on predicate_key,
        where predicate_key is constructed from args and kw.

        :args: varargs. Used to extract dispatch information to
           construct predicate_key.
        :kw: keyword arguments. Used to extract
           dispatch information to construct predicate_key.
        :returns: an iterable of functions.
        """
        key = self.predicate_key(*args, **kw)
        return self.key_lookup.all(key)

    def all_by_keys(self, **kw):
        """Look up all functions dispatched to using keyword arguments.

        Looks up the function to dispatch to using a ``key_dict``,
        mapping predicate name to predicate value. Returns the fallback
        value (default: ``None``) if nothing could be found.

        :kw: a dictionary. key is predicate name, value is
          predicate value. If omitted, predicate default is used.
        :returns: iterable of functions being dispatched to.
        """
        key = self.key_lookup.key_dict_to_predicate_key(kw)
        return self.key_lookup.all(key)

    def key_dict_to_predicate_key(self, key_dict):
        """Turn a key dict into a predicate key.

        Given a key dict under which an implementation function is
        registered, return an immutable predicate key.

        :param key_dict: dict with registration information
        :returns: an immutable predicate key
        """
        return self.registry.key_dict_to_predicate_key(key_dict)


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


def format_signature(args):
    return ', '.join(
        args.args +
        (['*' + args.varargs] if args.varargs else []) +
        (['**' + args.keywords] if args.keywords else []))


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


def execute(code_source, **namespace):
    """Execute code in a namespace, returning the namespace."""
    code_object = compile(
        code_source, '<generated code: {}>'.format(code_source), 'exec')
    exec(code_object, namespace)
    return namespace
