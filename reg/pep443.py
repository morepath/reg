from __future__ import unicode_literals
from functools import update_wrapper
from reg.mapping import Map, ClassMapKey

# pep 443 dispatch function support


# XXX absolutely no caching done
def singledispatch(func):
    registry = Map()

    def dispatch(typ):
        """generic_func.dispatch(type) -> <function implementation>

        Runs the dispatch algorithm to return the best available implementation
        for the given `type` registered on `generic_func`.

        """
        return registry[ClassMapKey(typ)]

    def register(typ, func=None):
        """generic_func.register(type, func) -> func

        Registers a new implementation for the given `type` on a
        `generic_func`.
        """
        if func is None:
            return lambda f: register(typ, f)
        registry[ClassMapKey(typ)] = func
        return func

    def wrapper(*args, **kw):
        return dispatch(args[0].__class__)(*args, **kw)

    registry[ClassMapKey(object)] = func
    wrapper.register = register
    wrapper.dispatch = dispatch
    update_wrapper(wrapper, func)
    return wrapper

# XXX taken from functools implementation. need to look into this for
# abc support

# def _compose_mro(cls, haystack):
#     """Calculates the MRO for a given class `cls`, including relevant
#     abstract base classes from `haystack`.

#     """
#     bases = set(cls.__mro__)
#     mro = list(cls.__mro__)
#     for needle in haystack:
#         if (needle in bases or not hasattr(needle, '__mro__')
#                             or not issubclass(cls, needle)):
#             continue   # either present in the __mro__ already or unrelated
#         for index, base in enumerate(mro):
#             if not issubclass(base, needle):
#                 break
#         if base in bases and not issubclass(needle, base):
#             # Conflict resolution: put classes present in __mro__ and their
#             # subclasses first. See test_mro_conflicts() in test_functools.py
#             # for examples.
#             index += 1
#         mro.insert(index, needle)
#     return mro

# def _find_impl(cls, registry):
#     """Returns the best matching implementation for the given class `cls` in
#     `registry`. Where there is no registered implementation for a specific
#     type, its method resolution order is used to find a more generic
#     implementation.

#     Note: if `registry` does not contain an implementation for the base
#     `object` type, this function may return None.

#     """
#     mro = _compose_mro(cls, registry.keys())
#     match = None
#     for t in mro:
#         if match is not None:
#             # If `match` is an ABC but there is another unrelated, equally
#             # matching ABC. Refuse the temptation to guess.
#             if (t in registry and not issubclass(match, t)
#                               and match not in cls.__mro__):
#                 raise RuntimeError("Ambiguous dispatch: {} or {}".format(
#                     match, t))
#             break
#         if t in registry:
#             match = t
#     return registry.get(match)
