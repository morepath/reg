"""An implicit global component lookup facility that can be installed
explicitly.
"""
from __future__ import unicode_literals

import threading


class Implicit(object):
    """Implicit global lookup.

    There will only one singleton instance of this, called
    ``reg.implicit``. The lookup can then be accessed using
    ``reg.implicit.lookup``.

    Dispatch functions as well as their ``component`` and ``all``
    methods make use of this information if you do not pass an
    explicit ``lookup`` argument to them. This is handy as it becomes
    unnecessary to have to pass a ``lookup`` object everywhere.

    The drawback is that this single global lookup is implicit, which
    makes it harder to test in isolation. Reg supports testing with
    the explicit ``lookup`` argument, but that is not useful if you
    are testing code that relies on an implicit lookup. Therefore Reg
    strives to make the implicit global lookup as explicit as
    possible so that it can be manipulated in tests where this is
    necessary.

    It is also possible for a framework to change the implicit lookup
    during run-time. This is done by simply assigning to
    ``implicit.lookup``. The lookup is stored on a thread-local and is
    unique per thread.

    To change the lookup back to a lookup in the global implicit
    registry, call ``reset``.

    The implicit lookup is thread-local: each thread has a separate
    implicit global lookup.
    """

    def __init__(self):
        self.base_lookup = None
        self.local = None

    def initialize(self, lookup):
        """Initialize implicit with lookup.

        :param lookup: The lookup that will be the global implicit lookup.
        :type lookup: ILookup.
        """
        self.base_lookup = lookup
        self.local = Local(lookup=self.base_lookup)

    def clear(self):
        """Clear global implicit lookup.
        """
        self.base_lookup = None
        self.local = Local(lookup=None)

    def reset(self):
        """Reset global implicit lookup to original lookup.

        This can be used to wipe out any composed lookups that
        were installed in this thread.
        """
        self.local.lookup = self.base_lookup

    @property
    def lookup(self):
        """Get the implicit ILookup."""
        if self.local is None:
            return None
        return self.local.lookup

    @lookup.setter
    def lookup(self, value):
        """Set the implicit ILookup."""
        self.local.lookup = value

    # XXX also document base_lookup


class Local(threading.local):
    def __init__(self, **kw):
        self.__dict__.update(kw)

implicit = Implicit()
