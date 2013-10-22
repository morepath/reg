class PredicateRegistryError(Exception):
    pass


class Sentinel(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s>' % self.name

ANY = Sentinel('ANY')
SENTINEL = Sentinel('SENTINEL')


class Predicate(object):
    def __init__(self, name, index_factory):
        self.name = name
        self.index_factory = index_factory

    def create_index(self):
        return self.index_factory()


class KeyIndex(object):
    def __init__(self):
        self.d = {}

    def add(self, key, value):
        self.d.setdefault(key, set()).add(value)

    def get(self, key):
        return self.d.get(key, set())


class PredicateRegistry(object):
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


def key_permutations(names, d):
    if len(names) == 0:
        yield {}
        return

    first = names[0]
    rest = names[1:]

    d = d.copy()
    try:
        value = d.pop(first)
    except KeyError:
        raise PredicateRegistryError("no required key: %s" % first)

    for p in key_permutations(rest, d):
        r = p.copy()
        r[first] = value
        yield r
    for p in key_permutations(rest, d):
        r = p.copy()
        r[first] = ANY
        yield r
