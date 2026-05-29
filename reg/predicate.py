from __future__ import annotations

import inspect
from operator import itemgetter
from itertools import product
from typing import TYPE_CHECKING, Any, Generic

from .error import RegistrationError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from typing_extensions import TypeVar

    _ValueT = TypeVar("_ValueT", default=Callable[..., Any])
else:
    from typing import TypeVar

    _ValueT = TypeVar("_ValueT")


class Predicate(Generic[_ValueT]):
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

    def __init__(
        self,
        name: str,
        index: Callable[[_ValueT | None], KeyIndex[_ValueT]],
        # FIXME: This maybe shouldn't be optional, considering
        #        PredicateRegistry.key will crash if it got a
        #        Predicate without a get_key.
        get_key: Callable[[dict[str, Any]], Any] | None = None,
        fallback: _ValueT | None = None,
        default: Any | None = None,
    ) -> None:
        self.name = name
        self.index = index
        self.fallback = fallback
        self.get_key = get_key
        self.default = default

    def create_index(self) -> KeyIndex[_ValueT]:
        return self.index(self.fallback)

    def key_by_predicate_name(self, d: dict[str, Any]) -> Any | None:
        return d.get(self.name, self.default)


def match_key(
    name: str,
    func: Callable[..., Any] | None = None,
    fallback: Any | None = None,
    default: Any | None = None,
) -> Predicate[Any]:
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
    get_key: Callable[[dict[str, Any]], Any]
    if func is None:
        get_key = itemgetter(name)
    else:
        get_key = lambda d: func(**d)
    return Predicate(name, KeyIndex, get_key, fallback, default)


def match_instance(
    name: str,
    func: Callable[..., Any] | None = None,
    fallback: Any | None = None,
    default: Any | None = None,
) -> Predicate[Any]:
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


def match_class(
    name: str,
    func: Callable[..., Any] | None = None,
    fallback: Any | None = None,
    default: Any | None = None,
) -> Predicate[Any]:
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
    get_key: Callable[[dict[str, Any]], Any]
    if func is None:
        get_key = itemgetter(name)
    else:
        get_key = lambda d: func(**d)
    return Predicate(name, ClassIndex, get_key, fallback, default)


_emptyset: frozenset[Any] = frozenset()


class KeyIndex(dict[Any, set[_ValueT]]):
    def __init__(self, fallback: _ValueT | None = None) -> None:
        self.fallback = fallback

    def __missing__(self, key: Any) -> frozenset[Any]:
        return _emptyset

    def permutations(self, key: Any) -> Iterator[Any]:
        """Permutations for a simple immutable key.

        There is only a single permutation: the key itself.
        """
        yield key


class ClassIndex(KeyIndex[_ValueT]):
    def permutations(self, key: type[Any]) -> Iterator[type[Any]]:
        """Permutations for class key.

        Returns class and its base classes in mro order.
        """
        yield from inspect.getmro(key)


class PredicateRegistry(Generic[_ValueT]):
    def __init__(self, *predicates: Predicate[_ValueT]) -> None:
        self.known_keys: set[Any] = set()
        self.known_values: set[_ValueT] = set()
        self.predicates = predicates
        self.indexes = [predicate.create_index() for predicate in predicates]
        key_getters = [p.get_key for p in predicates]
        if len(predicates) == 0:
            self.key = lambda **kw: ()  # type: ignore
        elif len(predicates) == 1:
            (p,) = key_getters
            self.key = lambda **kw: (p(kw),)  # type: ignore
        elif len(predicates) == 2:
            p, q = key_getters
            self.key = lambda **kw: (p(kw), q(kw))  # type: ignore
        elif len(predicates) == 3:
            p, q, r = key_getters
            self.key = lambda **kw: (p(kw), q(kw), r(kw))  # type: ignore
        else:
            self.key = lambda **kw: tuple([p(kw) for p in key_getters])  # type: ignore

    def register(self, key: Any, value: _ValueT) -> None:
        if key in self.known_keys:
            raise RegistrationError(f"Already have registration for key: {key}")
        for index, key_item in zip(self.indexes, key):
            index.setdefault(key_item, set()).add(value)
        self.known_keys.add(key)
        self.known_values.add(value)

    def get(self, keys: Sequence[Any]) -> set[_ValueT]:
        # do an intersection of all sets that result from index lookup
        # this code is a bit convoluted for performance reasons.
        sets = (index[key] for index, key in zip(self.indexes, keys))
        # besides doing the intersection,
        # this returns the known values if there are no indexes at all
        return next(sets, self.known_values).intersection(*sets)

    def permutations(self, keys: Sequence[Any]) -> Iterator[tuple[Any, ...]]:
        return product(
            *(index.permutations(key) for index, key in zip(self.indexes, keys))
        )

    def key(self, **kw: Any) -> tuple[Any, ...]:  # type: ignore[empty-body]
        """Construct a dispatch key from the arguments of a generic function.

        :param kw: a dictionary with the arguments passed to a generic
          function.
        :returns: a tuple, to be used as a key for dispatching.

        """
        # Overwritten by init

    def key_dict_to_predicate_key(self, d: dict[str, Any]) -> tuple[Any, ...]:
        """Construct a dispatch key from predicate values.

        Uses ``name`` and ``default`` attributes of predicates to
        construct the dispatch key.

        :param d: dictionary mapping predicate names to predicate
          values. If a predicate is missing from ``d``, its default
          expected value is used.
        :returns: a tuple, to be used as a key for dispatching.
        """
        return tuple([p.key_by_predicate_name(d) for p in self.predicates])

    def component(self, keys: Sequence[Any]) -> _ValueT | None:
        return next(self.all(keys), None)

    def fallback(self, keys: Sequence[Any]) -> _ValueT | None:
        result = None
        for index, key in zip(self.indexes, keys):
            for k in index.permutations(key):
                match = index[k]
                if match:
                    break
            else:
                # no matching permutation for this key, so this is the fallback
                return index.fallback
            if result is None:
                result = match
            else:
                result = result.intersection(match)
            # as soon as the intersection becomes empty, we have a failed
            # match
            if not result:
                return index.fallback
        return None

    def all(self, key: Sequence[Any]) -> Iterator[_ValueT]:
        for p in self.permutations(key):
            yield from self.get(p)
