from .neopredicate import (Registry as PredicateRegistry,
                           MultiPredicate)
from .sentinel import NOT_FOUND
from .argextract import ArgExtractor, KeyExtractor
from .sentinel import Sentinel
from .arginfo import arginfo
from .error import RegError, KeyExtractorError
from .mapply import lookup_mapply


class KeyRegistry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.known_keys = set()
        self.arg_extractors = {}
        self.predicate_registries = {}

    def register_predicates(self, key, predicates):
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
        r = self.register_predicates(callable, predicates)
        self.arg_extractors[callable] = ArgExtractor(callable, r.argnames())

    def register_dispatch(self, callable):
        self.register_callable_predicates(callable.wrapped_func,
                                          callable.predicates)

    def register_value(self, key, predicate_key, value):
        if isinstance(predicate_key, list):
            predicate_key = tuple(predicate_key)
        # if we have a 1 tuple, we register the single value inside
        if isinstance(predicate_key, tuple) and len(predicate_key) == 1:
            predicate_key = predicate_key[0]
        if self.predicate_registries[key].knows_key(predicate_key):
            raise RegError("Already have registration for key: %s" % (
                predicate_key,))
        self.predicate_registries[key].register(predicate_key, value)

    def register_dispatch_value(self, callable, predicate_key, value):
        value_arginfo = arginfo(value)
        if value_arginfo is None:
            raise RegError("Cannot register non-callable for dispatch "
                           "function %r: %r" % (callable, value))
        if not same_signature(arginfo(callable.wrapped_func), value_arginfo):
            raise RegError("Signature of callable dispatched to (%r) "
                           "not that of dispatch function (%r)" % (
                               value, callable.wrapped_func))
        self.register_value(callable.wrapped_func, predicate_key, value)

    def predicate_key(self, callable, *args, **kw):
        return self.predicate_registries[callable].key(
            self.arg_extractors[callable](*args, **kw))

    def component(self, key, predicate_key):
        return self.predicate_registries[key].component(predicate_key)

    def all(self, key, predicate_key):
        return self.predicate_registries[key].all(predicate_key)

    def lookup(self):
        return Lookup(self)


class CachingKeyLookup(object):
    def __init__(self, key_lookup, component_cache_size, all_cache_size):
        self.key_lookup = key_lookup
        self.component_cache = LRUCache(component_cache_size)
        self.all_cache = LRUCache(all_cache_size)

    def predicate_key(self, callable, *args, **kw):
        return self.key_lookup.predicate_key(callable, *args, **kw)

    def component(self, key, predicate_key, default=None):
        result = self.component_cache.get((key, predicate_key), NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = self.key_lookup.component(key, predicate_key, NOT_FOUND)
        if result is NOT_FOUND:
            return default
        self.component_cache.put((key, predicate_key), result)
        return result

    def all(self, key, predicate_key):
        result = self.all_cache.get((key, predicate_key), NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = list(self.key_lookup.all(key, predicate_key))
        self.component_cache.put((key, predicate_key), result)
        return result


class Lookup(object):
    def __init__(self, key_lookup):
        self.key_lookup = key_lookup

    def call(self, callable, *args, **kw):
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
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        return self.key_lookup.component(callable, key)

    def all(self, callable, *args, **kw):
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        return self.key_lookup.all(callable, key)


class SingleValueRegistry(object):
    def __init__(self):
        self.value = None

    def register(self, key, value):
        self.value = value

    def knows_key(self, key):
        return self.value is not None

    def key(self, d):
        return ()

    def argnames(self):
        return set()

    def component(self, key):
        return self.value

    def all(self, key):
        yield self.value


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
