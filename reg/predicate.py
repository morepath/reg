import inspect
from operator import itemgetter
from itertools import product

from .sentinel import NOT_FOUND
from .error import RegistrationError


class Predicate(object):
    """A dispatch predicate.

    :param name: name used to identify the predicate when specifying
      its expected value in :meth:`reg.Dispatch.register`.
    :param index: a function that constructs an index given
      a fallback argument; typically you supply either a :class:`KeyIndex`
      or :class:`ClassIndex`.
    :param get_key: a callable that accepts a dictionary with the invocation
      arguments of the generic function and returns a key to be used for
      dispatching.
    :param fallback: optional fallback value. The fallback of the
      the most generic index for which no values could be
      found is used.
    :param default: default expected value of the predicate, to be
      used by :meth:`reg.Dispatch.register` whenever the expected
      value for the predicate is not given explicitly.

    """

    def __init__(self, name, index, get_key=None, fallback=None,
                 default=None):
        self.name = name
        self.index = index
        self.fallback = fallback
        self.get_key = get_key
        self.default = default

    def create_index(self):
        return self.index(self.fallback)

    def key_by_predicate_name(self, d):
        return d.get(self.name, self.default)


def match_key(name, func=None, fallback=None, default=None):
    """Predicate that returns a value used for dispatching.

    :name: predicate name.
    :func: a callable that accepts the same arguments as the generic
      function and returns the value used for dispatching.  The
      returned value must be of an immutable type.

      If ``None``, use a callable returning the argument
      with the same name as the predicate.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.

    """
    if func is None:
        get_key = itemgetter(name)
    else:
        get_key = lambda d: func(**d)
    return Predicate(name, KeyIndex, get_key, fallback, default)


def match_instance(name, func=None, fallback=None, default=None):
    """Predicate that returns an instance whose class is used for dispatching.

    :name: predicate name.

    :func: a callable that accepts the same arguments as the generic
      function and returns the instance whose class is used for
      dispatching.  If ``None``, use a callable returning the argument
      with the same name as the predicate.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.

    """
    if func is None:
        get_key = lambda d: d[name].__class__
    else:
        get_key = lambda d: func(**d).__class__
    return Predicate(name, ClassIndex, get_key, fallback, default)


def match_class(name, func=None, fallback=None, default=None):
    """Predicate that returns a class used for dispatching.

    :name: predicate name.

    :func: a callable that accepts the same arguments as the generic
      function and returns a class used for
      dispatching.  If ``None``, use a callable returning the argument
      with the same name as the predicate.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.

    """
    if func is None:
        get_key = itemgetter(name)
    else:
        get_key = lambda d: func(**d)
    return Predicate(name, ClassIndex, get_key, fallback, default)


class MultiPredicate(object):
    """Transitional class for compatibility, soon to be removed."""
    def __init__(self, predicates):
        self.predicates = predicates

    def get_key(self, d):
        return tuple([predicate.get_key(d) for predicate in self.predicates])

    def key_by_predicate_name(self, d):
        result = []
        for predicate in self.predicates:
            result.append(predicate.key_by_predicate_name(d))
        return tuple(result)


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


def create_predicates_registry(predicates):
    return MultiplePredicateRegistry(*predicates)


class MultiplePredicateRegistry(object):

    def __init__(self, *predicates):
        self.known_keys = {}
        self.predicates = predicates
        self.indexes = [predicate.create_index() for predicate in predicates]
        self.key = lambda **kw: tuple([p.get_key(kw) for p in predicates])

    def register(self, key, value):
        if key in self.known_keys:
            raise RegistrationError(
                "Already have registration for key: %s" % (key,))
        for index, key_item in zip(self.indexes, key):
            index.add(key_item, value)
        self.known_keys[key] = value

    def get(self, keys, default):
        empty = set()
        sets = (
            index.get(key) or empty for index, key in zip(self.indexes, keys))
        return next(sets, empty).intersection(*sets) or default

    def permutations(self, keys):
        return product(*(
            index.permutations(key) for index, key in zip(self.indexes, keys)
        ))

    def key(self, **kw):
        """Construct a dispatch key from the arguments of a generic function.

        :param kw: a dictionary with the arguments passed to a generic
          function.
        :returns: a tuple, to be used as a key for dispatching.

        """
        # Overwritten by init

    def key_dict_to_predicate_key(self, d):
        """Construct a dispatch key from predicate values.

        Uses ``name`` and ``default`` attributes of predicates to
        construct the dispatch key.

        :param d: dictionary mapping predicate names to predicate
          values. If a predicate is missing from ``d``, its default
          expected value is used.
        :returns: a tuple, to be used as a key for dispatching.
        """
        return tuple([p.key_by_predicate_name(d) for p in self.predicates])

    def component(self, keys):
        if not self.predicates:
            return self.known_keys.get(keys)
        return next(self.all(keys), None)

    def fallback(self, keys):
        if not self.predicates:
            return None
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

    def all(self, key):
        if not self.predicates:
            for v in self.known_keys.values():
                yield v
        if not key:
            return
        for p in self.permutations(key):
            result = self.get(p, NOT_FOUND)
            if result is not NOT_FOUND:
                yield tuple(result)[0]


SingleValueRegistry = MultiplePredicateRegistry


class PredicateRegistry(MultiplePredicateRegistry):
    """Transitional class for compatibility, soon to be removed."""

    def __init__(self, predicate):
        if isinstance(predicate, MultiPredicate):
            super(PredicateRegistry, self).__init__(*predicate.predicates)
            self.__class__ = MultiplePredicateRegistry
        else:
            super(PredicateRegistry, self).__init__(predicate)

    def register(self, key, value):
        super(PredicateRegistry, self).register((key,), value)

    def fallback(self, key):
        return super(PredicateRegistry, self).fallback((key,))

    def all(self, key):
        for k in super(PredicateRegistry, self).all((key,)):
            yield k
