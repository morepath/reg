from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    ParamSpec,
    Protocol,
    TypeAlias,
    overload,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from inspect import FullArgSpec
    from typing_extensions import TypeVar
    from .dispatch import LookupEntry
    from .predicate import Predicate, PredicateRegistry

    _ValueT = TypeVar("_ValueT", covariant=True, default=Callable[..., Any])
else:
    from typing import TypeVar

    _ValueT = TypeVar("_ValueT", covariant=True)


_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_R = TypeVar("_R")
_P = ParamSpec("_P")


# NOTE: Dispatch.call serves as a proxy for most of the public interface
#       of Dispatch. We model this using a protocol, since there isn't
#       a proper class for this for this object. We duplicate the docs
#       so language servers can give better hints.
class DispatchCall(Protocol[_P, _T]):
    __name__: str
    __qualname__: str
    __defaults__: tuple[Any, ...] | None
    __globals__: dict[str, Any]
    wrapped_func: Callable[_P, _T]
    get_key_lookup: GetKeyLookup
    key_lookup: KeyLookup

    def clean(self) -> None:
        """Clean up implementations and added predicates.

        This restores the dispatch function to its original state,
        removing registered implementations and predicates added
        using :meth:`reg.Dispatch.add_predicates`.
        """
        raise NotImplementedError

    def add_predicates(self, predicates: list[Predicate]) -> None:
        """Add new predicates.

        Extend the predicates used by this predicates. This can be
        used to add predicates that are configured during startup time.

        Note that this clears up any registered implementations.

        :param predicates: a list of predicates to add.
        """
        raise NotImplementedError

    @overload
    def register(self, func: Callable[_P, _T], **key_dict: Any) -> Callable[_P, _T]: ...
    @overload
    def register(
        self, func: None = None, **key_dict: Any
    ) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
        raise NotImplementedError

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
        raise NotImplementedError

    def by_args(self, *args: _P.args, **kw: _P.kwargs) -> LookupEntry[Callable[_P, _T]]:
        """Lookup an implementation by invocation arguments.

        :param args: positional arguments used in invocation.
        :param kw: named arguments used in invocation.
        :returns: a :class:`reg.LookupEntry`.
        """
        raise NotImplementedError

    def by_predicates(self, **predicate_values: Any) -> LookupEntry[Callable[_P, _T]]:
        """Lookup an implementation by predicate values.

        :param predicate_values: the values of the predicates to lookup.
        :returns: a :class:`reg.LookupEntry`.
        """
        raise NotImplementedError

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        raise NotImplementedError


class DispatchMethodCall(DispatchCall[Concatenate[_T, _P], _R], Protocol[_P, _T, _R]):
    def by_args(self, *args: _P.args, **kw: _P.kwargs) -> LookupEntry[Callable[Concatenate[_T, _P], _R]]:  # type: ignore[override]
        """Lookup an implementation by invocation arguments.

        :param args: positional arguments used in invocation.
        :param kw: named arguments used in invocation.
        :returns: a :class:`reg.LookupEntry`.
        """
        raise NotImplementedError


# NOTE: This is so we can expose the original DispatchMethod through __func__
#       and have the correct signature for `__call__`.
class BoundDispatchMethodCall(DispatchMethodCall[_P, _T, _R], Protocol[_P, _T, _R]):
    @property
    def __self__(self) -> _T:
        raise NotImplementedError

    @property
    def __func__(self) -> DispatchMethodCall[_P, _T, _R]:
        raise NotImplementedError

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:  # type: ignore[override]
        raise NotImplementedError


# NOTE: arginfo serves as a proxy for the is_cached function, we duplicate
#       the docs for better language server support.
class ArgInfo(Protocol):
    __name__: str
    __qualname__: str
    _cache: dict[Callable[..., Any], FullArgSpec]
    is_cached: Callable[[Callable[..., Any]], bool]

    def __call__(self, callable: Callable[..., Any]) -> FullArgSpec | None:
        """Get information about the arguments of a callable.

        Returns a :class:`inspect.FullArgSpec` object as for
        :func:`inspect.getfullargspec`.

        :func:`inspect.getfullargspec` returns information about the arguments
        of a function. arginfo also works for classes and instances with a
        __call__ defined. Unlike getfullargspec, arginfo treats bound methods
        like functions, so that the self argument is not reported. Another
        difference is the handling of decorated functions. This will return
        the original signature, rather than the signature of the wrapper, if
        wrapped via :func:`functools.wraps`.

        arginfo returns ``None`` if given something that is not callable.

        arginfo caches previous calls (except for instances with a
        __call__), making calling it repeatedly cheap.

        This was originally inspired by the pytest.core varnames() function,
        but has been completely rewritten to handle class constructors,
        also show other getarginfo() information, and for readability.
        """


class KeyLookup(Protocol[_ValueT]):
    def component(self, key: Sequence[Any], /) -> _ValueT | None:
        raise NotImplementedError

    def fallback(self, key: Sequence[Any], /) -> _ValueT | None:
        raise NotImplementedError

    def all(self, key: Sequence[Any], /) -> Iterable[_ValueT]:
        raise NotImplementedError


GetKeyLookup: TypeAlias = Callable[[PredicateRegistry[_ValueT]], KeyLookup[_ValueT]]
