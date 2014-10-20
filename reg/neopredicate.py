from .sentinel import Sentinel
import inspect
from .argextract import KeyExtractor


NOT_FOUND = Sentinel('NOT_FOUND')


class Predicate(object):
    def __init__(self, get_key=None, fallback=None):
        self.get_key = KeyExtractor(get_key)
        self._fallback = fallback

    def create_index(self):
        raise NotImplementedError()  # pragma: nocoverage

    def permutations(self, key):
        raise NotImplementedError()  # pragma: nocoverage

    def fallback(self, index, key):
        for k in self.permutations(key):
            if index.get(k, NOT_FOUND) is not NOT_FOUND:
                return NOT_FOUND
        return self._fallback


class KeyPredicate(Predicate):
    def create_index(self):
        return KeyIndex()

    def permutations(self, key):
        yield key



class ClassPredicate(Predicate):
    def create_index(self):
        return KeyIndex()

    def permutations(self, key):
        for class_ in inspect.getmro(key):
            yield class_


class MultiPredicate(object):
    def __init__(self, predicates):
        self.predicates = predicates

    def get_key(self, d):
        return tuple([predicate.get_key(d) for predicate in self.predicates])

    def create_index(self):
        return MultiIndex(self.predicates)

    def permutations(self, key):
        return multipredicate_permutations(self.predicates, key)

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

    def get(self, key, default=None):
        return next(self.all(key), default)

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
