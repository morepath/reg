from __future__ import unicode_literals
from .sentinel import Sentinel
from .lookup import Matcher
from repoze.lru import lru_cache

# XXX needs a lot more documentation


class PredicateRegistryError(Exception):
    """An error using the predicate registry.
    """


ANY = Sentinel('ANY')


class Predicate(object):
    """A predicate.
    """
    def __init__(self, name, index_factory, calc=None, default=None):
        self.name = name
        self.index_factory = index_factory
        self.calc = calc
        self.default = default

    def create_index(self):
        return self.index_factory()


class KeyIndex(object):
    """An index for matching predicates by key.
    """
    def __init__(self):
        self.d = {}

    def add(self, key, value):
        self.d.setdefault(key, set()).add(value)

    def get(self, key):
        return self.d.get(key, set())


class PredicateRegistry(object):
    """A registry that can be used to index items by predicate.
    """
    def __init__(self, predicates):
        self.predicates = predicates
        self.names = [predicate.name for predicate in predicates]
        self.indexes = {}
        self.values = {}
        self.counter = 0

    def register(self, key, value):
        value_id = self.counter
        self.values[value_id] = value
        self.counter += 1

        for predicate in self.predicates:
            index = self.indexes.get(predicate.name)
            if index is None:
                self.indexes[predicate.name] = index = predicate.create_index()
            k = key.get(predicate.name, ANY)
            index.add(k, value_id)

    def get_specific(self, key):
        result_ids = None
        for predicate in self.predicates:
            index = self.indexes[predicate.name]
            matches = index.get(key[predicate.name])
            if result_ids is None:
                result_ids = matches
            else:
                result_ids = result_ids.intersection(matches)
            if not result_ids:
                return None
        if len(result_ids) != 1:
            raise PredicateRegistryError(
                "Multiple matches for: %r" % key)
        return self.values[result_ids.pop()]

    def get(self, key, default=None):
        for p in key_permutations(self.names, key):
            result = self.get_specific(p)
            if result is not None:
                return result
        return default


class PredicateMatcher(Matcher):
    def __init__(self, predicates):
        self._predicates = predicates
        self.defaults = {}
        for predicate in predicates:
            self.defaults[predicate.name] = predicate.default
        self.reg = PredicateRegistry(predicates)

    def register(self, predicates, value):
        self.reg.register(predicates, value)

    def predicates(self, *args):
        result = {}
        for predicate in self._predicates:
            result[predicate.name] = predicate.calc(*args)
        return result

    def __call__(self, *args, **kw):
        k = self.defaults.copy()
        k.update(kw)
        return self.reg.get(k)


# not currently in use, see key_permutations
def key_permutations_recursive(names, d):
    if len(names) == 0:
        yield {}
        return

    first = names[0]
    rest = names[1:]

    d = d.copy()
    value = d.pop(first)

    for p in key_permutations(rest, d):
        r = p.copy()
        r[first] = value
        yield r
    for p in key_permutations(rest, d):
        r = p.copy()
        r[first] = ANY
        yield r


def key_permutations(names, d):
    for p in key_permutations_names(tuple(names)):
        v = p.copy()
        for key, value in list(v.items()):
            if value is None:
                v[key] = d[key]
        yield v


# this helped enormously to make this iterative
# http://blog.moertel.com/posts/2013-05-14-recursive-to-iterative-2.html
# also introduced caching using repoze.lru. this cache should be big
# enough to comfortably fit 10 predicates before having to evict
@lru_cache(1024)
def key_permutations_names(names):
    permutations = [{}]
    for name in reversed(names):
        l = []
        for p in permutations:
            r = p.copy()
            r[name] = None
            l.append(r)
        for p in permutations:
            r = p.copy()
            r[name] = ANY
            l.append(r)
        permutations = l
    return permutations
