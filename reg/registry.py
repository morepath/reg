from repoze.lru import LRUCache
from .predicate import PredicateRegistry, MultiPredicate, SingleValueRegistry
from .sentinel import NOT_FOUND
from .argextract import ArgExtractor
from .arginfo import arginfo
from .error import RegistrationError, KeyExtractorError
from .mapply import lookup_mapply


class Registry(object):
    """A registry of predicate registries

    The key is an immutable that we perform the lookup for. The
    permutation key is the key to do the lookup with. The value should
    be an immutable as well (or at least hashable).

    The registry can be configured with predicates for a key, and
    the predicates are aware of permutations of keys. This means, among
    others, that a value registered for a base class is also matched
    when you look up a subclass.

    The Registry is designed to be easily cacheable.
    """
    def __init__(self):
        self.clear()

    def clear(self):
        """Clear the registry.
        """
        self.known_keys = set()
        self.arg_extractors = {}
        self.predicate_registries = {}

    def register_predicates(self, key, predicates):
        """Register the predicates to use for a lookup key.

        :param key: an immutable for which to register the predicates.
        :param predicates: a sequence of :class:`reg.Predicate` objects.
        :returns: a :class:`reg.PredicateRegistry`.
        """
        if len(predicates) == 0:
            result = self.predicate_registries[key] = SingleValueRegistry()
            return result
        if len(predicates) == 1:
            # an optimization in case just one predicate in use
            predicate = predicates[0]
        else:
            predicate = MultiPredicate(predicates)
        self.predicate_registries[key] = result = PredicateRegistry(predicate)
        return result

    def register_callable_predicates(self, callable, predicates):
        """Register predicates for a callable key.

        Works as :meth:`register_predicates`, but also
        makes sure a predicate key can be constructed from arguments
        to this callable.

        :param callable: a function from which to extract argument
          information.
        :param predicates: a sequence of :class:`reg.Predicate` objects.
        :returns: a :class:`reg.PredicateRegistry`.

        """
        r = self.register_predicates(callable, predicates)
        self.arg_extractors[callable] = ArgExtractor(callable, r.argnames())
        return r

    def register_dispatch(self, callable):
        """Register a dispatch function.

        Works as :meth:`register_callable_predicates`, but extracts
        predicate information from information registered using the
        :func:`reg.dispatch` decorator.

        :param callable: a dispatch callable.
        :returns: a :class:`reg.PredicateRegistry`.
        """
        return self.register_callable_predicates(callable.wrapped_func,
                                                 callable.predicates)

    def register_value(self, key, predicate_key, value):
        """Register a value for a predicate_key.

        Given a key, register a value for a particular predicate_key
        in the registry. Raises a :exc:`reg.RegistrationError`
        if the predicate_key is already known for this key.

        :param key: an immutable
        :param predicate_key: an immutable predicate key defined by
          the predicates for this key.
        :param value: an immutable value to register.
        """
        if isinstance(predicate_key, list):
            predicate_key = tuple(predicate_key)
        # if we have a 1 tuple, we register the single value inside
        if isinstance(predicate_key, tuple) and len(predicate_key) == 1:
            predicate_key = predicate_key[0]
        self.predicate_registries[key].register(predicate_key, value)

    def register_dispatch_value(self, callable, predicate_key, value):
        """Register a callable for a dispatch function.

        Like :meth:`register_value`, but makes sure that the value is
        a callable with the same signature as the original dispatch callable.
        If not, a :exc:`reg.RegistrationError` is raised.
        """
        value_arginfo = arginfo(value)
        if value_arginfo is None:
            raise RegistrationError(
                "Cannot register non-callable for dispatch "
                "function %r: %r" % (callable, value))
        if not same_signature(arginfo(callable.wrapped_func), value_arginfo):
            raise RegistrationError(
                "Signature of callable dispatched to (%r) "
                "not that of dispatch function (%r)" % (
                    value, callable.wrapped_func))
        self.register_value(callable.wrapped_func, predicate_key, value)

    def predicate_key(self, callable, *args, **kw):
        """Construct predicate_key for function arguments.

        For a callable and its function arguments, construct the
        appropriate predicate_key. This is used by the dispatch
        mechanism to dispatch to the right function.

        If the predicate_key cannot be constructed from args and kw,
        this raises a :exc:`KeyExtractorError`.

        :param callable: the callable for which to extract the predicate_key
        :param args: the varargs given to the callable.
        :param kw: the keyword arguments given to the callable.
        :returns: an immutable predicate_key based on the predicates
          the callable was configured with.
        """
        return self.predicate_registries[callable].key(
            self.arg_extractors[callable](*args, **kw))

    def component(self, key, predicate_key):
        """Lookup value in registry based on predicate_key.

        If value for predicate_key cannot be found, looks up first
        permutation of predicate_key for which there is a value. Permutations
        are made according to the predicates registered for the key.

        :param key: an immutable for which to look up the predicate_key.
        :param predicate_key: an immutable predicate key, constructed
          for predicates given for this key.
        :returns: a registered value, or fallback for predicate if
          nothing could be found. The default fallback for a predicate
          is ``None``.
        """
        return self.predicate_registries[key].component(predicate_key)

    def all(self, key, predicate_key):
        """Lookup iterable of values registered for predicate_key.

        Looks up values registered for all permutations of
        predicate_key, the most specific first.

        :param key: an immutable for which to look up the values.
        :param predicate_key: an immutable predicate key, constructed for
          the predicates given for this key.
        :returns: An iterable of registered values.
        """
        return self.predicate_registries[key].all(predicate_key)

    def lookup(self):
        """A :class:`Lookup` for this registry.
        """
        return Lookup(self)


class CachingKeyLookup(object):
    """A key lookup that caches.

    Implements the read-only API of :class:`Registry`, using
    a cache to speed up access.

    The cache is LRU.
    """
    def __init__(self, key_lookup, component_cache_size, all_cache_size):
        """
        :param: key_lookup - the :class:`Registry` to cache.
        :component_cache_size: how many cache entries to store for
          the :meth:`component` method. This is also used by dispatch
          calls.
        :all_cache_size: how many cache entries to store for the
          the :all:`all` method.
        """
        self.key_lookup = key_lookup
        self.component_cache = LRUCache(component_cache_size)
        self.all_cache = LRUCache(all_cache_size)

    def predicate_key(self, callable, *args, **kw):
        """Construct predicate_key for function arguments.

        For a callable and its function arguments, construct the
        appropriate predicate_key. This is used by the dispatch
        mechanism to dispatch to the right function.

        If the predicate_key cannot be constructed from args and kw,
        this raises a :exc:`KeyExtractorError`.

        :param callable: the callable for which to extract the predicate_key
        :param args: the varargs given to the callable.
        :param kw: the keyword arguments given to the callable.
        :returns: an immutable predicate_key based on the predicates
          the callable was configured with.
        """
        return self.key_lookup.predicate_key(callable, *args, **kw)

    def component(self, key, predicate_key):
        """Lookup value in registry based on predicate_key.

        If value for predicate_key cannot be found, looks up first
        permutation of predicate_key for which there is a value. Permutations
        are made according to the predicates registered for the key.

        :param key: an immutable for which to look up the predicate_key.
        :param predicate_key: an immutable predicate key, constructed
          for predicates given for this key.
        :returns: a registered value, or fallback for predicate if
          nothing could be found. The default fallback for a predicate
          is ``None``.
        """
        result = self.component_cache.get((key, predicate_key), NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = self.key_lookup.component(key, predicate_key)
        self.component_cache.put((key, predicate_key), result)
        return result

    def all(self, key, predicate_key):
        """Lookup iterable of values registered for predicate_key.

        Looks up values registered for all permutations of
        predicate_key, the most specific first.

        :param key: an immutable for which to look up the values.
        :param predicate_key: an immutable predicate key, constructed for
          the predicates given for this key.
        :returns: An iterable of registered values.
        """
        result = self.all_cache.get((key, predicate_key), NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = list(self.key_lookup.all(key, predicate_key))
        self.all_cache.put((key, predicate_key), result)
        return result

    def lookup(self):
        """A :class:`Lookup` for this registry.
        """
        return Lookup(self)


class Lookup(object):
    """The lookup is used for generic dispatch.

    The arguments to the lookup functions are those of the dispatch
    function being called. The lookup extract the predicate_key from
    these arguments and then looks up the actual function to call. This
    function is then called with the original arguments.
    """
    def __init__(self, key_lookup):
        self.key_lookup = key_lookup

    def call(self, callable, *args, **kw):
        """Call callable with args and kw.

        Do a dispatch call for callable. If nothing more specific is
        registered, call the dispatch function as a fallback.

        :param callable: the dispatch function to call.
        :args: varargs for the call. Is also used to extract
           dispatch information to construct predicate_key.
        :kw: keyword arguments for the call. Is also used to extract
           dispatch information to construct predicate_key.
        :returns: the result of the call.
        """
        try:
            key = self.key_lookup.predicate_key(callable, *args, **kw)
            component = self.key_lookup.component(callable, key)
        except KeyExtractorError:
            # if we cannot extract the key we cannot find the component
            # later on this will result in a TypeError as we try to
            # call the callable with the wrong arguments, which is what
            # we want
            component = None
        # if we cannot find the component, use the original
        # callable as a fallback.
        if component is None:
            component = callable
        return lookup_mapply(component, self, *args, **kw)

    def component(self, callable, *args, **kw):
        """Lookup function dispatched to with args and kw.

        Looks up the function to dispatch to using args and
        kw. Returns the fallback value (default: ``None``) if nothing
        could be found.

        :param callable: the dispatch function.
        :args: varargs. Used to extract dispatch information to
           construct predicate_key.
        :kw: keyword arguments. Used to extract
           dispatch information to construct predicate_key.
        :returns: the function being dispatched to, or fallback.
        """
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        return self.key_lookup.component(callable, key)

    def all(self, callable, *args, **kw):
        """Lookup all functions dispatched to with args and kw.

        Looks up functions for all permutations based on predicate_key,
        where predicate_key is constructed from args and kw.

        :param callable: the dispatch function.
        :args: varargs. Used to extract dispatch information to
           construct predicate_key.
        :kw: keyword arguments. Used to extract
           dispatch information to construct predicate_key.
        :returns: an iterable of functions.
        """
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        return self.key_lookup.all(callable, key)


def same_signature(a, b):
    """Check whether a arginfo and b arginfo are the same signature.

    Signature may have an extra 'lookup' argument. Default arguments may
    be different.
    """
    a_args = set(a.args)
    b_args = set(b.args)
    a_args.discard('lookup')
    b_args.discard('lookup')
    return (a_args == b_args and
            a.varargs == b.varargs and
            a.keywords == b.keywords)
