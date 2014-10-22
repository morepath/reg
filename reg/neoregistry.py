from .neopredicate import (Registry as PredicateRegistry,
                           MultiPredicate, NOT_FOUND)
from .argextract import ArgDict, KeyExtractor
from .sentinel import Sentinel


class SingleValueRegistry(object):
    def __init__(self):
        self.value = None

    def register(self, key, value):
        self.value = value

    def key(self, d):
        return ()

    def component(self, key):
        return self.value

    def all(self, key):
        yield self.value


class Registry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.argdicts = {}
        self.predicate_registries = {}

    def register_predicates(self, key, predicates):
        if len(predicates) == 0:
            self.predicate_registries[key] = SingleValueRegistry()
            return
        if len(predicates) == 1:
            # an optimization in case just one predicate in use
            predicate = predicates[0]
        else:
            predicate = MultiPredicate(predicates)
        self.predicate_registries[key] = PredicateRegistry(
            predicate)

    def register_callable_predicates(self, callable, predicates):
        self.argdicts[callable] = ArgDict(callable)
        self.register_predicates(callable, predicates)

    def register_dispatch(self, callable):
        self.register_callable_predicates(callable.wrapped_func,
                                          callable.predicates)

    def register_value(self, key, predicate_key, value):
        # if we have a 1 tuple, we register the single value inside
        if isinstance(predicate_key, tuple) and len(predicate_key) == 1:
            predicate_key = predicate_key[0]
        self.predicate_registries[key].register(predicate_key, value)

    def register_dispatch_value(self, callable, predicate_key, value):
        # XXX we should check whether func signature of value matches that of
        # callable.wrapped_func
        self.register_value(callable.wrapped_func, predicate_key, value)

    def predicate_key(self, callable, *args, **kw):
        return self.predicate_registries[callable].key(
            self.argdicts[callable](*args, **kw))

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
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        component = self.key_lookup.component(callable, key)
        if component is None:
            return callable(*args, **kw)
        return component(*args, **kw)

    def component(self, callable, *args, **kw):
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        return self.key_lookup.component(callable, key)

    def all(self, callable, *args, **kw):
        key = self.key_lookup.predicate_key(callable, *args, **kw)
        return self.key_lookup.all(callable, key)
