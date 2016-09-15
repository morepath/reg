"""Compatibility support for Python 2 and 3."""

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)
