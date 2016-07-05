from __future__ import unicode_literals
import inspect


def arginfo(callable):
    """Get information about the arguments of a callable.

    Returns a :class:`inspect.ArgSpec` object as for
    :func:`inspect.getargspec`.

    :func:`inspect.getargspec` returns information about the arguments
    of a function. arginfo also works for classes and instances with a
    __call__ defined. Unlike getargspec, arginfo treats bound methods
    like functions, so that the self argument is not reported.

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
    func, cache_key, remove_self = get_callable_info(callable)
    if func is None:
        return None
    result = inspect.getargspec(func)
    if remove_self:
        args = result.args[1:]
        result = inspect.ArgSpec(args, result.varargs, result.keywords,
                                 result.defaults)
    arginfo._cache[cache_key] = result
    return result


def is_cached(callable):
    if callable in arginfo._cache:
        return True
    return callable.__call__ in arginfo._cache


arginfo._cache = {}
arginfo.is_cached = is_cached


def get_callable_info(callable):
    """Get information about a callable.

    Returns a tuple of:

    * actual function/method that can be inspected with inspect.getargspec.

    * cache key to use to cache results.

    * whether to remove self or not.

    Note that in Python 3, __init__ is not a method, but we still
    want to remove self from it.

    If not inspectable (None, None, False) is returned.
    """
    if inspect.isfunction(callable):
        return callable, callable, False
    if inspect.ismethod(callable):
        return callable, callable, True
    if inspect.isclass(callable):
        return get_class_init(callable), callable, True
    try:
        callable = getattr(callable, '__call__')
        return callable, callable, True
    except AttributeError:
        return None, None, False


def fake_empty_init():
    pass  # pragma: nocoverage


class Dummy(object):
    pass


WRAPPER_DESCRIPTOR = Dummy.__init__


def get_class_init(class_):
    try:
        func = class_.__init__
    except AttributeError:  # pragma: no cover
        # Python 2 classic class without __init__.
        return fake_empty_init
    # If this is a new-style class and there is no __init__
    # defined, in CPython (but not PyPy) this is a WRAPPER_DESCRIPTOR.
    if func is WRAPPER_DESCRIPTOR:
        return fake_empty_init
    # A PyPy class without __init__ needs to be handled specially,
    # as the default __init__ in this case falsely reports varargs
    # and keywords.
    if is_pypy_default_init(func):
        return fake_empty_init  # pragma: nocoverage
    return func


def is_pypy_default_init(func):
    try:
        return func.func_code.co_name == 'descr__init__'
    except AttributeError:  # pragma: nocoverage
        return False
