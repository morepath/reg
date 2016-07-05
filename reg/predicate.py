from .sentinel import NOT_FOUND
import inspect
from .argextract import KeyExtractor, ClassKeyExtractor, NameKeyExtractor
from .error import RegistrationError


class Predicate(object):
    """A dispatch predicate.
    """
    def __init__(self, name, index, get_key=None, fallback=None,
                 default=None):
        """
        :param name: predicate name. This is used by
          :meth:`reg.Registry.register_function_by_name`.
        :param index: a function that constructs an index given
          a fallback argument; typically you supply either a :class:`KeyIndex`
          or :class:`ClassIndex`.
        :param get_key: optional :class:`KeyExtractor`.
        :param fallback: optional fallback value. The fallback of the
          the most generic index for which no values could be
          found is used.
        :param default: optional predicate default. This is used by
          :meth:`.reg.Registry.register_function_by_name`, and supplies
          the value if it is not given explicitly.
        """
        self.name = name
        self.index = index
        self.fallback = fallback
        self.get_key = get_key
        self.default = default

    def create_index(self):
        return self.index(self.fallback)

    def argnames(self):
        """argnames that this predicate needs to dispatch on.
        """
        if self.get_key is None:
            return set()
        return set(self.get_key.names)

    def key_by_predicate_name(self, d):
        return d.get(self.name, self.default)


def key_predicate(name, get_key=None, fallback=None, default=None):
    """Construct predicate indexed on any immutable value.

    :name: predicate name.
    :get_key: a :class:`KeyExtractor`. Should return key to dispatch on.
    :fallback: a fallback value. By default is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.
    """
    return Predicate(name, KeyIndex, get_key, fallback, default)


def class_predicate(name, get_key=None, fallback=None, default=None):
    """Construct predicate indexed on class.

    :name: predicate name.
    :get_key: a :class:`KeyExtractor`. Should return class to dispatch on.
    :fallback: a fallback value. By default is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.
    """
    return Predicate(name, ClassIndex, get_key, fallback, default)


def match_key(name, func, fallback=None, default=None):
    """Predicate that extracts immutable key according to func.

    :name: predicate name.
    :func: argument that takes arguments. These arguments are
      extracted from the arguments given to the dispatch function.
      This function should return what to dispatch on.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.
    """
    return key_predicate(name, KeyExtractor(func), fallback, default)


def match_instance(name, func, fallback=None, default=None):
    """Predicate that extracts class of instance returned by func.

    :name: predicate name.
    :func: argument that takes arguments. These arguments are
      extracted from the arguments given to the dispatch function.
      This function should return an instance; dispatching is done
      on the class of that instance.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.
    """
    return class_predicate(name, ClassKeyExtractor(func), fallback, default)


def match_argname(argname, fallback=None, default=None):
    """Predicate that extracts class of specified argument.

    :name: predicate name.
    :argname: name of the argument to dispatch on - its class will
      be used for the dispatch.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.
    """
    return class_predicate(argname, NameKeyExtractor(argname),
                           fallback, default)


def match_class(name, func, fallback=None, default=None):
    """Predicate that extracts class returned by func.

    :name: predicate name.
    :func: argument that takes arguments. These arguments are
      extracted from the arguments given to the dispatch function.
      This function should return a class; dispatching is done
      on this class.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.
    """
    return class_predicate(name, KeyExtractor(func), fallback, default)


class MultiPredicate(object):
    def __init__(self, predicates):
        self.predicates = predicates
        self.predicate_names = set(
            [predicate.name for predicate in predicates])

    def create_index(self):
        return MultiIndex(self.predicates)

    def get_key(self, d):
        return tuple([predicate.get_key(d) for predicate in self.predicates])

    def argnames(self):
        result = set()
        for predicate in self.predicates:
            result.update(predicate.argnames())
        return result

    def key_by_predicate_name(self, d):
        result = []
        for predicate in self.predicates:
            result.append(predicate.key_by_predicate_name(d))
        return tuple(result)


class Index(object):
    def add(self, key, value):
        raise NotImplementedError  # pragma: nocoverage

    def get(self, key, default=None):
        raise NotImplementedError  # pragma: nocoverage

    def permutations(self, key):
        raise NotImplementedError  # pragma: nocoverage

    def fallback(self, key):
        raise NotImplementedError  # pragma: nocoverage


class KeyIndex(object):
    def __init__(self, fallback=None):
        self.d = {}
        self._fallback = fallback

    def add(self, key, value):
        self.d.setdefault(key, set()).add(value)

    def get(self, key, default=None):
        return self.d.get(key, default)

    def permutations(self, key):
        """Permutations for a simple immutable key.

        There is only a single permutation: the key itself.
        """
        yield key

    def fallback(self, key):
        """Return fallback if this index does not contain key.

        If index contains permutations of key, then ``NOT_FOUND``
        is returned.
        """
        for k in self.permutations(key):
            if k in self.d:
                return NOT_FOUND
        return self._fallback


class ClassIndex(KeyIndex):
    def permutations(self, key):
        """Permutations for class key.

        Returns class and its base classes in mro order. If a classic
        class in Python 2, smuggle in ``object`` as the base class
        anyway to make lookups consistent.
        """
        for class_ in inspect.getmro(key):
            yield class_
        if class_ is not object:
            yield object  # pragma: no cover


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

    def permutations(self, key):
        return multipredicate_permutations(self.indexes, key)

    def fallback(self, keys):
        result = None
        for index, key in zip(self.indexes, keys):
            for k in index.permutations(key):
                match = index.get(k)
                if match:
                    break
            else:
                # no matching permutation for this key, so this is the fallback
                return index._fallback
            if result is None:
                result = match
            else:
                result = result.intersection(match)
            # as soon as the intersection becomes empty, we have a failed
            # match
            if not result:
                return index._fallback
        # if all predicates match, then we don't find a fallback
        return NOT_FOUND


class PredicateRegistry(object):
    def __init__(self, predicate):
        self.known_keys = set()
        self.predicate = predicate
        self.index = self.predicate.create_index()

    def register(self, key, value):
        if key in self.known_keys:
            raise RegistrationError(
                "Already have registration for key: %s" % (key,))
        self.index.add(key, value)
        self.known_keys.add(key)

    def key(self, d):
        return self.predicate.get_key(d)

    def key_by_predicate_name(self, d):
        return self.predicate.key_by_predicate_name(d)

    def argnames(self):
        return self.predicate.argnames()

    def component(self, key):
        return next(self.all(key), None)

    def fallback(self, key):
        return self.index.fallback(key)

    def all(self, key):
        for p in self.index.permutations(key):
            result = self.index.get(p, NOT_FOUND)
            if result is not NOT_FOUND:
                yield tuple(result)[0]


class SingleValueRegistry(object):
    def __init__(self):
        self.value = None

    def register(self, key, value):
        if self.value is not None:
            raise RegistrationError(
                "Already have registration for key: %s" % (key,))
        self.value = value

    def key(self, d):
        return ()

    def key_by_predicate_name(self, d):
        return ()

    def argnames(self):
        return set()

    def component(self, key):
        return self.value

    def fallback(self, key):
        return None

    def all(self, key):
        yield self.value


# XXX transform to non-recursive version
# use # http://blog.moertel.com/posts/2013-05-14-recursive-to-iterative-2.html
def multipredicate_permutations(indexes, keys):
    first = keys[0]
    rest = keys[1:]
    first_index = indexes[0]
    rest_indexes = indexes[1:]
    if not rest:
        for permutation in first_index.permutations(first):
            yield (permutation,)
        return
    for permutation in first_index.permutations(first):
        for rest_permutation in multipredicate_permutations(
                rest_indexes, rest):
            yield (permutation,) + rest_permutation
