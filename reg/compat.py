import sys
from types import MethodType

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


if PY3:
    string_types = (str,)
else:  # pragma: no cover
    string_types = (basestring,)  # noqa


if PY3:
    def create_method_for_class(callable, type):
        return MethodType(callable, type)

    def create_method_for_instance(callable, obj):
        return MethodType(callable, obj)
else:  # pragma: no cover
    def create_method_for_class(callable, type):
        return MethodType(callable, None, type)

    def create_method_for_instance(callable, obj):
        return MethodType(callable, obj, obj.__class__)
