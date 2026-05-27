import inspect
import sys

if sys.version_info < (3, 14):

    def get_signature(callable):  # pragma: no cover
        """A compatibility wrapper for `inspect.signature`."""
        return inspect.signature(callable)

else:
    from annotationlib import Format  # pragma: no cover

    def get_signature(callable):  # pragma: no cover
        """A compatibility wrapper for `inspect.signature`."""
        return inspect.signature(callable, annotation_format=Format.FORWARDREF)


def arginfo(callable):
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
    try:
        return arginfo._cache[callable]
    except KeyError:
        # Try to get __call__ function from the cache.
        try:
            return arginfo._cache[callable.__call__]
        except (AttributeError, KeyError):
            pass

    if inspect.isfunction(callable):
        cache_key = callable
    elif inspect.ismethod(callable):
        cache_key = callable
    elif inspect.isclass(callable):
        cache_key = callable
        if callable.__init__ is WRAPPER_DESCRIPTOR:
            # Only in this specific case do we replace the callable
            # into `inspect.signature` with something else, to ensure
            # we don't get a `ValueError` and instead end up with
            # an empty signature.
            callable = fake_empty_init
    else:
        # Since arbitrary callable objects may not be hashable
        # we instead retrieve their call method, which should be
        try:
            cache_key = callable.__call__
        except AttributeError:
            return None

    signature = get_signature(callable)
    args = []
    varargs = None
    varkw = None
    defaults = []
    kwonlyargs = []
    kwonlydefaults = {}
    annotations = {}

    if signature.return_annotation is not signature.empty:
        annotations["return"] = signature.return_annotation

    for parameter in signature.parameters.values():
        if (
            parameter.kind is parameter.POSITIONAL_OR_KEYWORD
            or parameter.kind is parameter.POSITIONAL_ONLY
        ):
            args.append(parameter.name)
            if parameter.default is not parameter.empty:
                defaults.append(parameter.default)
        elif parameter.kind is parameter.KEYWORD_ONLY:
            kwonlyargs.append(parameter.name)
            if parameter.default is not parameter.empty:
                kwonlydefaults[parameter.name] = parameter.default
        elif parameter.kind is parameter.VAR_POSITIONAL:
            varargs = parameter.name
        elif parameter.kind is parameter.VAR_KEYWORD:
            varkw = parameter.name

        if parameter.annotation is not parameter.empty:
            annotations[parameter.name] = parameter.annotation

    result = arginfo._cache[cache_key] = inspect.FullArgSpec(
        args,
        varargs,
        varkw,
        tuple(defaults) if defaults else None,
        kwonlyargs,
        kwonlydefaults if kwonlydefaults else None,
        annotations,
    )
    return result


def is_cached(callable):
    if callable in arginfo._cache:
        return True
    return callable.__call__ in arginfo._cache


arginfo._cache = {}
arginfo.is_cached = is_cached


def fake_empty_init():
    pass  # pragma: nocoverage


class Dummy:
    pass


WRAPPER_DESCRIPTOR = Dummy.__init__
