# taken from pyramid.compat

import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


if PY3:
    string_types = (str,)
else:
    string_types = (basestring,)
