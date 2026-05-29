from __future__ import annotations

import inspect
from types import MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    NoReturn as Never,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)
from .dispatch import dispatch, Dispatch, format_signature, execute, identity
from .arginfo import arginfo

if TYPE_CHECKING:
    from collections.abc import Callable
    from .dispatch import LookupEntry
    from .predicate import Predicate, PredicateRegistry
    from .types import BoundDispatchMethodCall, DispatchMethodCall, KeyLookup

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_R = TypeVar("_R")
_R1 = TypeVar("_R1")
_P = ParamSpec("_P")
_P1 = ParamSpec("_P1")


class dispatch_method(dispatch, Generic[_P, _T, _R]):
    """Decorator to make a method on a context class dispatch.

    This takes the predicates to dispatch on as zero or more parameters.

    :param predicates: sequence of :class:`Predicate` instances to do
      the dispatch on. You create predicates using
      :func:`reg.match_instance`, :func:`reg.match_key`,
      :func:`reg.match_class`, or with a custom predicate class.

      You can also pass in plain string argument, which is turned into
      a :func:`reg.match_instance` predicate.
    :param get_key_lookup: a function that gets a
      :class:`PredicateRegistry` instance and returns a key lookup. A
      :class:`PredicateRegistry` instance is itself a key lookup, but
      you can return a caching key lookup (such as
      :class:`reg.DictCachingKeyLookup` or
      :class:`reg.LruCachingKeyLookup`) to make it more efficient.
    :param first_invocation_hook: a callable that accepts an instance of the
      class in which this decorator is used. It is invoked the first
      time the method is invoked.

    """

    callable: Callable[Concatenate[_T, _P], _R]

    def __init__(
        # NOTE: When we first create this object, we don't know yet what kind
        #       of object and callable we're binding to, so to avoid unknown
        #       type errors we solve the type vars here and return a new
        #       type from `__call__`. It would be more robust if this was
        #       a factory for `dispatch_method` decorators instead, but it's
        #       a little difficult to justify changing at this point.
        self: dispatch_method[Any, Any, Any],
        *predicates: str | Predicate,
        first_invocation_hook: Callable[[Any], object] = lambda x: None,
        get_key_lookup: Callable[[PredicateRegistry], KeyLookup] = identity,
        # NOTE: We keep allowing arbitrary keyword arguments at runtime
        #       for now, but type checkers should emit an error for these.
        **kw: Never,
    ) -> None:
        self.first_invocation_hook = first_invocation_hook
        super().__init__(*predicates, get_key_lookup=get_key_lookup, **kw)
        self._cache: dict[type[_T] | None, DispatchMethodCall[_P, _T, _R]] = {}

    # NOTE: This needs to be able to modify the bound type vars, so we
    #       use different type vars, with a separate scope.
    def __call__(  # type: ignore[override]
        self: dispatch_method[Any, Any, Any],
        callable: Callable[Concatenate[_T1, _P1], _R1],
    ) -> dispatch_method[_P1, _T1, _R1]:
        self.callable = callable
        return self

    @overload
    def __get__(
        self, obj: _T, type: type[_T] | None = None
    ) -> BoundDispatchMethodCall[_P, _T, _R]: ...
    @overload
    def __get__(
        self, obj: None, type: type[_T] | None = None
    ) -> DispatchMethodCall[_P, _T, _R]: ...

    def __get__(
        self, obj: _T | None, type: type[_T] | None = None
    ) -> BoundDispatchMethodCall[_P, _T, _R] | DispatchMethodCall[_P, _T, _R]:
        # we get the method from the cache
        # this guarantees that we distinguish between dispatches
        # on a per class basis, and on the name of the method

        dispatch = self._cache.get(type)

        if dispatch is None:
            # if this is the first time we access the dispatch method,
            # we create it and store it in the cache
            dispatch = DispatchMethod(
                self.predicates, self.callable, self.get_key_lookup
            ).call
            self._cache[type] = dispatch

        # we cannot attach the dispatch method to the class
        # directly (skipping the descriptor during next access) here,
        # because we need to return a distinct dispatch for each
        # class, including subclasses.
        if obj is None:
            # we access it through the class directly, so unbound
            return dispatch

        self.first_invocation_hook(obj)

        # if we access the instance, we simulate binding it
        bound = cast("BoundDispatchMethodCall[_P, _T, _R]", MethodType(dispatch, obj))
        # we store it on the instance, so that next time we
        # access this, we do not hit the descriptor anymore
        # but return the bound dispatch function directly
        setattr(obj, self.callable.__name__, bound)
        return bound


class DispatchMethod(Dispatch[Concatenate[_T, _P], _R], Generic[_P, _T, _R]):
    call: DispatchMethodCall[  # pyright: ignore[reportIncompatibleVariableOverride]
        _P, _T, _R
    ]

    def by_args(self, *args: _P.args, **kw: _P.kwargs) -> LookupEntry[Callable[Concatenate[_T, _P], _R]]:  # type: ignore[override]
        """Lookup an implementation by invocation arguments.

        :param args: positional arguments used in invocation.
        :param kw: named arguments used in invocation.
        :returns: a :class:`reg.LookupEntry`.
        """
        return super().by_args(None, *args, **kw)  # type: ignore[arg-type]


@overload
def methodify(
    func: Callable[_P, _T], selfname: None = None
) -> Callable[Concatenate[Any, _P], _T]: ...


# NOTE: For this overload we no longer know what the signature will look
#       like since it might be concatenated or not, so we have to discard
#       it if we want to preserve the gradual guarantee
@overload
def methodify(func: Callable[..., _T], selfname: str) -> Callable[..., _T]: ...


def methodify(
    func: Callable[_P, _T], selfname: str | None = None
) -> Callable[Concatenate[Any, _P], _T] | Callable[..., _T]:
    """Turn a function into a method, if needed.

    If ``selfname`` is not specified, wrap the function so that it
    takes an additional first argument, like a method.

    If ``selfname`` is specified, check whether it is the same as the
    name of the first argument of ``func``. If itsn't, wrap the
    function so that it takes an additional first argument, with the
    name specified by ``selfname``.

    If it is, the signature of ``func`` needn't be amended, but
    wrapping might still be necessary.

    In all cases, :func:`inspect_methodified` lets you retrieve the wrapped
    function.

    :param func: the function to turn into method.

    :param selfname: if specified, the name of the argument
      referencing the class instance.  Typically, ``"self"``.

    :returns: function that can be used as a method when assigned to a
      class.

    """
    args = arginfo(func)
    if args is None:
        raise TypeError("methodify must take a callable")
    if args.args[:1] != [selfname]:
        # Add missing self to the signature:
        code_template = (
            "def wrapper({selfname}, {signature}): return _func({signature})"
        )
    elif inspect.ismethod(func):
        # Bound method: must be wrapped despite same signature:
        code_template = "def wrapper({signature}): return _func({signature})"
    else:
        # No wrapping needed:
        return func
    code_source = code_template.format(
        signature=format_signature(args), selfname=selfname or "_"
    )
    return execute(code_source, _func=func)["wrapper"]  # type: ignore[no-any-return]


def clean_dispatch_methods(cls: type[object]) -> None:
    """For a given class clean all dispatch methods.

    This resets their registry to the original state using
    :meth:`reg.DispatchMethod.clean`.

    :param cls: a class that has :class:`reg.DispatchMethod` methods on it.
    """
    for name in dir(cls):
        attr = getattr(cls, name)
        if inspect.isfunction(attr) and hasattr(attr, "clean"):
            attr.clean()  # pyright: ignore[reportFunctionMemberAccess]
