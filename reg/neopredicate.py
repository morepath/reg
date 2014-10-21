from .sentinel import Sentinel
import inspect
from .argextract import KeyExtractor
from reg.lookup import ComponentLookupError


NOT_FOUND = Sentinel('NOT_FOUND')


class Predicate(object):
    def __init__(self, create_index, permutations,
                 get_key=None,
                 fallback=None):
        self.create_index = create_index
        self.permutations = permutations
        self.get_key = get_key
        self._fallback = fallback

    def fallback(self, index, key):
        for k in self.permutations(key):
            if index.get(k, NOT_FOUND) is not NOT_FOUND:
                return NOT_FOUND
        return self._fallback


def key_predicate(get_key=None, fallback=None):
    return Predicate(KeyIndex, key_permutations, get_key, fallback)


def key_permutations(key):
    yield key


def class_predicate(get_key=None, fallback=None):
    return Predicate(KeyIndex, class_permutations, get_key, fallback)


def class_permutations(key):
    for class_ in inspect.getmro(key):
        yield class_


def component_lookup_error(*args, **kw):
    raise ComponentLookupError()


def match_key(func, fallback=None):
    if fallback is None:
        fallback = component_lookup_error
    return key_predicate(KeyExtractor(func), fallback)


def match_instance(func, fallback=None):
    extract = KeyExtractor(func)
    def get_class(d):
        return extract(d).__class__
    if fallback is None:
        fallback = component_lookup_error
    return class_predicate(get_class, fallback)


def match_class(func, fallback=None):
    if fallback is None:
        fallback = component_lookup_error
    return class_predicate(KeyExtractor(func), fallback)


class MultiPredicate(object):
    def __init__(self, predicates):
        self.predicates = predicates

    def create_index(self):
        return MultiIndex(self.predicates)

    def permutations(self, key):
        return multipredicate_permutations(self.predicates, key)

    def get_key(self, d):
        return tuple([predicate.get_key(d) for predicate in self.predicates])

    def fallback(self, multi_index, key):
        for index, k, predicate in zip(multi_index.indexes,
                                       key, self.predicates):
            result = predicate.fallback(index, k)
            if result is not NOT_FOUND:
                return result
        return NOT_FOUND


class KeyIndex(object):
    def __init__(self):
        self.d = {}

    def add(self, key, value):
        self.d.setdefault(key, set()).add(value)

    def get(self, key, default=None):
        return self.d.get(key, default)


class MultiIndex(object):
    def __init__(self, predicates):
        self.predicates = predicates
        self.indexes = [predicate.create_index() for predicate in predicates]

    def add(self, keys, value):
        for index, key in zip(self.indexes, keys):
            index.add(key, value)

    def get(self, keys, default):
        matches = []
        # get all matching indexes first
        for index, key in zip(self.indexes, keys):
            match = index.get(key)
            # bail out early if None or any match has 0 items
            if not match:
                return default
            matches.append(match)
        # sort matches by length.
        # this allows cheaper intersection calls later
        matches.sort(key=lambda match: len(match))

        result = None
        for match in matches:
            if result is None:
                result = match
            else:
                result = result.intersection(match)
            # bail out early if there is nothing left
            if not result:
                return default
        return result


class Registry(object):
    def __init__(self, predicate):
        self.values = {}
        self.counter = 0
        self.predicate = predicate
        self.index = self.predicate.create_index()

    def register(self, key, value):
        # XXX not sure that value_id trick is right. instead we could
        # simply make sure value is hashable. though getting lots of
        # hashes might slow down the intersections... since we're only
        # supposed to register a value once per index, we can get away
        # with the value_id trick
        value_id = self.counter
        self.values[value_id] = value
        self.counter += 1
        self.index.add(key, value_id)

    def key(self, d):
        return self.predicate.get_key(d)

    def component(self, key):
        result = next(self.all(key), NOT_FOUND)
        if result is NOT_FOUND:
            return self.fallback(key)
        return result

    def fallback(self, key):
        return self.predicate.fallback(self.index, key)

    def all(self, key):
        for p in self.predicate.permutations(key):
            result = self.index.get(p, NOT_FOUND)
            if result is not NOT_FOUND:
                assert len(result) == 1
                yield self.values[list(result)[0]]


# XXX transform to non-recursive version
# use # http://blog.moertel.com/posts/2013-05-14-recursive-to-iterative-2.html
def multipredicate_permutations(predicates, keys):
    first = keys[0]
    rest = keys[1:]
    first_predicate = predicates[0]
    rest_predicates = predicates[1:]
    if not rest:
        for permutation in first_predicate.permutations(first):
            yield (permutation,)
        return
    for permutation in first_predicate.permutations(first):
        for rest_permutation in multipredicate_permutations(
                rest_predicates, rest):
            yield (permutation,) + rest_permutation
