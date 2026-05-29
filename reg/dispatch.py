from __future__ import annotations

from functools import partial, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    NamedTuple,
    NoReturn as Never,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)
from .predicate import match_instance
from .predicate import PredicateRegistry
from .arginfo import arginfo
from .error import RegistrationError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from inspect import FullArgSpec
    from .predicate import Predicate
    from .types import DispatchCall, GetKeyLookup, KeyLookup

_T = TypeVar("_T")
_F = TypeVar("_F", bound="Callable[..., Any]")
_P = ParamSpec("_P")


def identity(registry: PredicateRegistry) -> PredicateRegistry:
    return registry


class dispatch:
    """Decorator to make a function dispatch based on its arguments.

    This takes the predicates to dispatch on as zero or more
    parameters.

    :param predicates: sequence of :class:`reg.Predicate` instances to
      do the dispatch on. You create predicates using
      :func:`reg.match_instance`, :func:`reg.match_key`,
      :func:`reg.match_class`, or with a custom predicate class. You
      can also pass in plain string argument, which is turned into a
      :func:`reg.match_instance` predicate.
    :param get_key_lookup: a function that gets a
      :class:`PredicateRegistry` instance and returns a key lookup. A
      :class:`PredicateRegistry` instance is itself a key lookup, but
      you can return a caching key lookup (such as
      :class:`reg.DictCachingKeyLookup` or
      :class:`reg.LruCachingKeyLookup`) to make it more efficient.
    :returns: a function that you can use as if it were a
      :class:`reg.Dispatch` instance.

    """

    def __init__(
        self,
        *predicates: str | Predicate,
        get_key_lookup: GetKeyLookup = identity,
        # NOTE: We keep allowing arbitrary keyword arguments at runtime
        #       for now, but type checkers should emit an error for these.
        **kw: Never,
    ) -> None:
        self.predicates = [self._make_predicate(predicate) for predicate in predicates]
        self.get_key_lookup = get_key_lookup

    def _make_predicate(self, predicate: str | Predicate) -> Predicate:
        if isinstance(predicate, str):
            return match_instance(predicate)
        return predicate

    def __call__(self, callable: Callable[_P, _T]) -> DispatchCall[_P, _T]:
        return Dispatch(self.predicates, callable, self.get_key_lookup).call


class _LookupEntry(NamedTuple):
    lookup: KeyLookup
    key: tuple[Any, ...]


class LookupEntry(_LookupEntry, Generic[_F]):
    """The dispatch data associated to a key."""

    @property
    def component(self) -> _F | None:
        """The function to dispatch to, excluding fallbacks."""
        return cast("_F | None", self.lookup.component(self.key))

    @property
    def fallback(self) -> _F | None:
        """The approriate fallback implementation."""
        return cast("_F | None", self.lookup.fallback(self.key))

    @property
    def matches(self) -> Iterable[_F]:
        """An iterator over all the compatible implementations."""
        return cast("Iterable[_F]", self.lookup.all(self.key))

    @property
    def all_matches(self) -> list[_F]:
        """The list of all compatible implementations."""
        return list(self.matches)


class Dispatch(Generic[_P, _T]):
    """Dispatch function.

    You can register implementations based on particular predicates. The
    dispatch function dispatches to these implementations based on its
    arguments.

    :param predicates: a list of predicates.
    :param callable: the Python function object to register dispatch
      implementations for. The signature of an implementation needs to
      match that of this function. This function is used as a fallback
      implementation that is called if no specific implementations match.
    :param get_key_lookup: a function that gets a
      :class:`PredicateRegistry` instance and returns a key lookup. A
      :class:`PredicateRegistry` instance is itself a key lookup, but
      you can return a caching key lookup (such as
      :class:`reg.DictCachingKeyLookup` or
      :class:`reg.LruCachingKeyLookup`) to make it more efficient.
    """

    def __init__(
        self,
        predicates: list[Predicate],
        callable: Callable[_P, _T],
        get_key_lookup: GetKeyLookup,
    ) -> None:
        self.wrapped_func = callable
        self.get_key_lookup = get_key_lookup
        self._original_predicates = predicates
        self._define_call()
        self._register_predicates(predicates)

    def _register_predicates(self, predicates: list[Predicate]) -> None:
        self.registry = PredicateRegistry(*predicates)
        self.predicates = predicates
        self.call.key_lookup = self.key_lookup = self.get_key_lookup(self.registry)
        self.call.__globals__.update(
            _registry_key=self.registry.key,
            _component_lookup=self.key_lookup.component,
            _fallback_lookup=self.key_lookup.fallback,
        )
        self._predicate_key.__globals__.update(
            _registry_key=self.registry.key,
            _return_type=partial(LookupEntry["Callable[_P, _T]"], self.key_lookup),
        )

    # tell type checkers about these auto-generated functions
    call: DispatchCall[_P, _T]
    _predicate_key: Callable[..., LookupEntry[Callable[_P, _T]]]

    def _define_call(self) -> None:
        # We build the generic function on the fly. Its definition
        # requires the signature of the wrapped function and the
        # arguments needed by the registered predicates
        # (predicate_args):
        code_template = """\
def call({signature}):
    _key = _registry_key({predicate_args})
    return (_component_lookup(_key) or
            _fallback_lookup(_key) or
            _fallback)({signature})
"""

        args = arginfo(self.wrapped_func)
        assert args is not None
        signature = format_signature(args)
        predicate_args = ", ".join("{0}={0}".format(x) for x in args.args)
        code_source = code_template.format(
            signature=signature, predicate_args=predicate_args
        )

        # We now compile call to byte-code:
        self.call = call = cast(
            "DispatchCall[_P, _T]",
            wraps(self.wrapped_func)(
                execute(
                    code_source,
                    _registry_key=None,
                    _component_lookup=None,
                    _fallback_lookup=None,
                    _fallback=self.wrapped_func,
                )["call"]
            ),
        )

        # We copy over the defaults from the wrapped function.
        call.__defaults__ = args.defaults

        # Make the methods available as attributes of call
        for k in dir(type(self)):
            if not k.startswith("_"):
                setattr(call, k, getattr(self, k))
        call.wrapped_func = self.wrapped_func

        # We now build the implementation for the predicate_key method
        self._predicate_key = execute(
            "def predicate_key({signature}):\n"
            "    return _return_type(_registry_key({predicate_args}))".format(
                signature=format_signature(args), predicate_args=predicate_args
            ),
            _registry_key=None,
            _return_type=None,
        )["predicate_key"]

    def clean(self) -> None:
        """Clean up implementations and added predicates.

        This restores the dispatch function to its original state,
        removing registered implementations and predicates added
        using :meth:`reg.Dispatch.add_predicates`.
        """
        self._register_predicates(self._original_predicates)

    def add_predicates(self, predicates: list[Predicate]) -> None:
        """Add new predicates.

        Extend the predicates used by this predicates. This can be
        used to add predicates that are configured during startup time.

        Note that this clears up any registered implementations.

        :param predicates: a list of predicates to add.
        """
        self._register_predicates(self.predicates + predicates)

    @overload
    def register(self, func: Callable[_P, _T], **key_dict: Any) -> Callable[_P, _T]: ...
    @overload
    def register(
        self, func: None = None, **key_dict: Any
    ) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]: ...

    def register(
        self, func: Callable[_P, _T] | None = None, **key_dict: Any
    ) -> Callable[_P, _T] | Callable[[Callable[_P, _T]], Callable[_P, _T]]:
        """Register an implementation.

        If ``func`` is not specified, this method can be used as a
        decorator and the decorated function will be used as the
        actual ``func`` argument.

        :param func: a function that implements behavior for this
          dispatch function. It needs to have the same signature as
          the original dispatch function. If this is a
          :class:`reg.DispatchMethod`, then this means it needs to
          take a first context argument.
        :param key_dict: keyword arguments describing the registration,
          with as keys predicate name and as values predicate values.
        :returns: ``func``.
        """
        if func is None:
            return partial(self.register, **key_dict)
        validate_signature(func, self.wrapped_func)
        predicate_key = self.registry.key_dict_to_predicate_key(key_dict)
        self.registry.register(predicate_key, func)
        return func

    def by_args(self, *args: _P.args, **kw: _P.kwargs) -> LookupEntry[Callable[_P, _T]]:
        """Lookup an implementation by invocation arguments.

        :param args: positional arguments used in invocation.
        :param kw: named arguments used in invocation.
        :returns: a :class:`reg.LookupEntry`.
        """
        return self._predicate_key(*args, **kw)

    def by_predicates(self, **predicate_values: Any) -> LookupEntry[Callable[_P, _T]]:
        """Lookup an implementation by predicate values.

        :param predicate_values: the values of the predicates to lookup.
        :returns: a :class:`reg.LookupEntry`.
        """
        return LookupEntry(
            self.key_lookup,
            self.registry.key_dict_to_predicate_key(predicate_values),
        )


def validate_signature(f: Callable[..., Any], dispatch: Callable[..., Any]) -> None:
    f_arginfo = arginfo(f)
    if f_arginfo is None:
        raise RegistrationError(
            "Cannot register non-callable for dispatch " "%r: %r" % (dispatch, f)
        )
    d_arginfo = arginfo(dispatch)
    assert d_arginfo is not None
    if not same_signature(d_arginfo, f_arginfo):
        raise RegistrationError(
            "Signature of callable dispatched to (%r) "
            "not that of dispatch (%r)" % (f, dispatch)
        )


def format_signature(args: FullArgSpec) -> str:
    return ", ".join(
        args.args
        + (["*" + args.varargs] if args.varargs else [])
        + (["**" + args.varkw] if args.varkw else [])
    )


def same_signature(a: FullArgSpec, b: FullArgSpec) -> bool:
    """Check whether a arginfo and b arginfo are the same signature.

    Actual names of arguments may differ. Default arguments may be
    different.
    """
    a_args = set(a.args)
    b_args = set(b.args)
    return len(a_args) == len(b_args) and a.varargs == b.varargs and a.varkw == b.varkw


def execute(code_source: str, **namespace: Any) -> dict[str, Any]:
    """Execute code in a namespace, returning the namespace."""
    code_object = compile(code_source, f"<generated code: {code_source}>", "exec")
    exec(code_object, namespace)
    return namespace
