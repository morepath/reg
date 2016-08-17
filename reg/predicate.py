import inspect

from repoze.lru import LRUCache
from .sentinel import NOT_FOUND
from .argextract import KeyExtractor, ClassKeyExtractor, NameKeyExtractor
from .error import RegistrationError, KeyExtractorError
from .argextract import ArgExtractor


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


def match_class(name, func=None, fallback=None, default=None):
    """Predicate that extracts class returned by func.

    :name: predicate name.
    :func: argument that takes arguments. These arguments are
      extracted from the arguments given to the dispatch function.
      This function should return a class; dispatching is done on this
      class. If ``None`` use the class of the argument having the same
      name as the predicate.
    :fallback: the fallback value. By default it is ``None``.
    :default: optional default value.
    :returns: a :class:`Predicate`.

    """
    if func is None:
        func = eval('lambda {0}: {0}'.format(name))
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


def create_predicates_registry(predicates):
    if len(predicates) == 0:
        return SingleValueRegistry()
    if len(predicates) == 1:
        # an optimization in case just one predicate in use
        predicate = predicates[0]
    else:
        predicate = MultiPredicate(predicates)
    return PredicateRegistry(predicate)


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

    def argnames(self):
        return self.predicate.argnames()

    def key(self, d):
        return self.predicate.get_key(d)

    def key_dict_to_predicate_key(self, d):
        """Construct predicate key from key dictionary.

        Uses ``name`` and ``default`` attributes of predicate to
        construct the predicate key. If the key cannot be constructed
        then a ``KeyError`` is raised.

        :param key_dict: dictionary with predicate name keys and predicate
          values. For omitted keys, the predicate default is used.
        :returns: an immutable predicate_key based on the dictionary
          and the names and defaults of the predicates the callable
          was configured with.
        """
        return self.predicate.key_by_predicate_name(d)

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

    def argnames(self):
        return []

    def key(self, d):
        return ()

    def key_dict_to_predicate_key(self, d):
        return ()

    def component(self, key):
        return self.value

    def fallback(self, key):
        return None

    def all(self, key):
        yield self.value


class CachingKeyLookup(object):
    """
    A key lookup that caches.

    Implements the read-only API of :class:`PredicateRegistry`, using
    a cache to speed up access.

    The cache is LRU.

    :param: key_lookup - the :class:`PredicateRegistry` to cache.
    :param component_cache_size: how many cache entries to store for
      the :meth:`component` method. This is also used by dispatch
      calls.
    :param all_cache_size: how many cache entries to store for the
      the :meth:`all` method.
    :param fallback_cache_size: how many cache entries to store for
      the :meth:`fallback` method.
    """
    def __init__(self, key_lookup, component_cache_size, all_cache_size,
                 fallback_cache_size):
        self.key_lookup = key_lookup
        self.key_dict_to_predicate_key = key_lookup.key_dict_to_predicate_key
        self.component_cache = LRUCache(component_cache_size)
        self.all_cache = LRUCache(all_cache_size)
        self.fallback_cache = LRUCache(fallback_cache_size)

    def argnames(self):
        return self.key_lookup.argnames()

    def key(self, d):
        return self.key_lookup.key(d)

    def component(self, predicate_key):
        """Lookup value in registry based on predicate_key.

        If value for predicate_key cannot be found, looks up first
        permutation of predicate_key for which there is a value. Permutations
        are made according to the predicates registered for the key.

        :param predicate_key: an immutable predicate key, constructed
          for predicates given for this key.
        :returns: a registered value, or ``None``.
        """
        result = self.component_cache.get(predicate_key, NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = self.key_lookup.component(predicate_key)
        self.component_cache.put(predicate_key, result)
        return result

    def fallback(self, predicate_key):
        """Lookup fallback based on predicate_key.

        This finds the fallback for the most specific predicate
        that fails to match.

        :param predicate_key: an immutable predicate key, constructed
          for predicates given for this key.
        :returns: the fallback value for the most specific predicate
          the failed to match.
        """
        result = self.fallback_cache.get(predicate_key, NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = self.key_lookup.fallback(predicate_key)
        self.fallback_cache.put(predicate_key, result)
        return result

    def all(self, predicate_key):
        """Lookup iterable of values registered for predicate_key.

        Looks up values registered for all permutations of
        predicate_key, the most specific first.

        :param predicate_key: an immutable predicate key, constructed for
          the predicates given for this key.
        :returns: An iterable of registered values.
        """
        result = self.all_cache.get(predicate_key, NOT_FOUND)
        if result is not NOT_FOUND:
            return result
        result = list(self.key_lookup.all(predicate_key))
        self.all_cache.put(predicate_key, result)
        return result


class Lookup(object):
    """The lookup is used for generic dispatch.

    The arguments to the lookup functions are those of the dispatch
    function being called. The lookup extracts the predicate_key from
    these arguments and then looks up the actual function to call. This
    function is then called with the original arguments.

    :param key_lookup: the key lookup, either a :class:`PredicateRegistry` or
      :class:`CachingKeyLookup`.
    """
    def __init__(self, callable, key_lookup):
        self.key_lookup = key_lookup
        self.callable = callable
        self.arg_extractor = ArgExtractor(callable, self.key_lookup.argnames())

    def predicate_key(self, *args, **kw):
        """Construct predicate_key for function arguments.

        For function arguments, construct the appropriate
        ``predicate_key``. This is used by the dispatch mechanism to
        dispatch to the right function.

        If the ``predicate_key`` cannot be constructed from ``args``
        and ``kw``, this raises a :exc:`KeyExtractorError`.

        :param args: the varargs given to the callable.
        :param kw: the keyword arguments given to the callable.
        :returns: an immutable ``predicate_key`` based on the predicates
          the callable was configured with.
        """
        return self.key_lookup.key(self.arg_extractor(*args, **kw))

    def call(self, *args, **kw):
        """Call with args and kw.

        If nothing more specific is registered, call the dispatch
        function as a fallback.

        :args: varargs for the call. Is also used to extract
           dispatch information to construct predicate_key.
        :kw: keyword arguments for the call. Is also used to extract
           dispatch information to construct predicate_key.
        :returns: the result of the call.
        """
        try:
            key = self.predicate_key(*args, **kw)
            component = self.key_lookup.component(key)
        except KeyExtractorError:
            # if we cannot extract the key this could be because the
            # dispatch was never initialized, as register_function
            # was not called. In this case we want the fallback.
            # Alternatively we cannot construct the key because we
            # were passed the wrong arguments.
            # In both cases, call the fallback. In case the wrong arguments
            # were passed, we get the appropriate TypeError then
            component = self.callable

        if component is None:
            # try to use the fallback
            component = self.key_lookup.fallback(key)
            if component is None:
                # if fallback is None use the original callable as fallback
                component = self.callable
        return component(*args, **kw)

    def component(self, *args, **kw):
        """Lookup function dispatched to with args and kw.

        Looks up the function to dispatch to using args and
        kw. Returns the fallback value (default: ``None``) if nothing
        could be found.

        :args: varargs. Used to extract dispatch information to
           construct ``predicate_key``.
        :kw: keyword arguments. Used to extract
           dispatch information to construct ``predicate_key``.
        :returns: the function being dispatched to, or None.
        """
        key = self.predicate_key(*args, **kw)
        return self.key_lookup.component(key)

    def fallback(self, *args, **kw):
        """Lookup fallback for args and kw.

        :args: varargs. Used to extract dispatch information to
           construct ``predicate_key``.
        :kw: keyword arguments. Used to extract
           dispatch information to construct ``predicate_key``.
        :returns: the function being dispatched to, or fallback.
        """
        key = self.predicate_key(*args, **kw)
        return self.key_lookup.fallback(key)

    def component_by_keys(self, **kw):
        """Look up function based on key_dict.

        Looks up the function to dispatch to using a key_dict,
        mapping predicate name to predicate value. Returns the fallback
        value (default: ``None``) if nothing could be found.

        :kw: key is predicate name, value is
          predicate value under which it was registered.
          If omitted, predicate default is used.
        :returns: the function being dispatched to, or fallback.
        """
        key = self.key_lookup.key_dict_to_predicate_key(kw)
        return self.key_lookup.component(key)

    def all(self, *args, **kw):
        """Lookup all functions dispatched to with args and kw.

        Looks up functions for all permutations based on predicate_key,
        where predicate_key is constructed from args and kw.

        :args: varargs. Used to extract dispatch information to
           construct predicate_key.
        :kw: keyword arguments. Used to extract
           dispatch information to construct predicate_key.
        :returns: an iterable of functions.
        """
        key = self.predicate_key(*args, **kw)
        return self.key_lookup.all(key)

    def all_key_dict(self, key_dict):
        """Look up all functions dispatched to using on key_dict.

        Looks up the function to dispatch to using a ``key_dict``,
        mapping predicate name to predicate value. Returns the fallback
        value (default: ``None``) if nothing could be found.

        :key_dict: a dictionary. key is predicate name, value is
          predicate value. If omitted, predicate default is used.
        :returns: iterable of functions being dispatched to.
        """
        key = self.key_lookup.key_dict_to_predicate_key(key_dict)
        return self.key_lookup.all(key)


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
