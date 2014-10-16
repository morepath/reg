from .sentinel import Sentinel
import inspect


ANY = Sentinel('ANY')


NOT_FOUND = Sentinel('NOT_FOUND')


class Predicate(object):
    def __init__(self, name, get_key):
        self.name = name
        self.get_key = get_key

    def create_index(self):
        raise NotImplementedError()

    def permutations(self, key):
        raise NotImplementedError()

    def get_id(self, index, key):
        return next(self.all_ids(index, key))

    def all_ids(self, index, key):
        ids = None
        for permutation in self.permutations(key):
            ids = index.get(permutation)
            if not ids:
                continue
            assert len(ids) == 1
            yield ids

class KeyPredicate(Predicate):
    def create_index(self):
        return KeyIndex()

    def permutations(self, key):
        yield key
        yield ANY



class ClassPredicate(Predicate):
    def create_index(self):
        return KeyIndex()

    def permutations(self, key):
        for class_ in inspect.getmro(key):
            yield class_
        yield ANY


class MultiPredicate(Predicate):
    def __init__(self, name, get_key, predicates):
        super(MultiPredicate, self).__init__(name, get_key)
        self.predicates = predicates

    def create_index(self):
        return MultiIndex(self.predicates)

    def permutations(self, key):
        return multipredicate_permutations(self.predicates, key)


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
        self.indexes = {}

    def add(self, keys, value):
        for predicate, key in zip(self.predicates, keys):
            index = self.indexes.get(predicate.name)
            if index is None:
                self.indexes[predicate.name] = index = predicate.create_index()
            index.add(key, value)

    def get(self, keys, default):
        matches = []
        # get all matching indexes first
        for predicate, key in zip(self.predicates, keys):
            index = self.indexes[predicate.name]
            match = index.get(key)
            # bail out early if None or any match has 0 items
            if not match:
                return default
            matches.append(match)
        # sort matches by length.
        # this optimizes for cheaper interaction calls later
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

    def get(self, key, default=None):
        return next(self.all(key), default)

    def all(self, key):
        for p in self.predicate.permutations(key):
            result = self.index.get(p, NOT_FOUND)
            if result is not NOT_FOUND:
                assert len(result) == 1
                yield self.values[list(result)[0]]


# XXX transform to non-recursive version
# use # http://blog.moertel.com/posts/2013-05-14-recursive-to-iterative-2.html
# XXX it's possible that we should never return ANY, <non-ANY> as
# fallbacks are only registered for the higher priority ANY.
def multipredicate_permutations(predicates, keys):
    if not keys:
        yield ()
        return
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
