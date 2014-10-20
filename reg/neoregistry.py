from .neopredicate import (Registry as PredicateRegistry,
                           KeyPredicate, ClassPredicate,
                           MultiPredicate, NOT_FOUND)
from .argextract import ArgDict, KeyExtractor
from .sentinel import Sentinel

MISSING_VALUE = Sentinel('MISSING_VALUE')


class SingleValueRegistry(object):
    def __init__(self):
        self.value = MISSING_VALUE

    def register(self, predicate_key, value):
        self.value = value

    def all(self, predicate_key):
        if self.value is not MISSING_VALUE:
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

    def register_value(self, key, predicate_key, value):
        # XXX if registering for callable we can check whether
        # func signature matches that of key
        self.predicate_registries[key].register(predicate_key, value)

    def predicate_key(self, callable, *args, **kw):
        return self.predicate_registries[callable].key(
            self.argdicts[callable](*args, **kw))

    def component(self, key, predicate_key):
        return self.predicate_registries[key].component(predicate_key)

    def all(self, key, predicate_key):
        return self.predicate_registries[key].all(predicate_key)


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
        return component(*args, **kw)
