"""Basic interfaces and API docs.
"""

from .interface import Interface, abstractmethod, abstractproperty, SENTINEL


class IMatcher(Interface):
    """Look up by calling and returning value.

    If an IMatcher component is registered, it is called with the objects
    as an argument, and the resulting value is considered to be the looked up
    component. If the resulting value is None, no component is found for
    this matcher.
    """






class IImplicit(Interface):
    """Implicit global lookup.

    There will only one singleton instance of this, called ``implicit``.

    Normally during startup of an application the framework will
    register the implicit lookup by using ``implicit.register()``.

    The lookup can then be accessed using ``implicit.lookup``.

    ``Interface.component()`` and ``Interface.adapt`` make use of this
    information if you do not pass an explicit ``lookup`` keyword
    argument. This is handy as it becomes unnecessary to have to pass
    a ``lookup`` object everywhere.

    The drawback is that this single global lookup is implicit, which
    makes it harder to test in isolation. Reg supports testing
    with the explicit ``lookup`` argument, but that is not useful if
    you are testing code that relies on an implicit lookup. Therefore
    Reg has strived to make the implicit global lookup as
    explicit as possible so that it can be manipulated in tests where
    this is necessary.

    It is also possible for a framework to change the implicit lookup
    during run-time. This is done by simply assigning to
    ``implicit.lookup``. The lookup is stored on a thread-local and is
    unique per thread.

    Reg offers facilities to compose such a custom lookup:

    * ``reg.ListClassLookup`` and ``reg.ChainClassLookup``
       which can be used to chain multiple ``IClassLookup``s together.

   * ``reg.CachedClassLookup`` which can be used to create a
      faster caching version of an ``IClassLookup``.

    * ``reg.Lookup`` which can be used to turn a ``IClassLookup``
      into a proper ``ILookup``.

    To change the lookup back to a lookup in the global implicit
    registry, call ``reset_lookup``.

    The implicit lookup is thread-local: each thread has a separate
    implicit global lookup.
    """

    @abstractmethod
    def initialize(self, lookup):
        """Initialize implicit with lookup.
        """

    @abstractmethod
    def clear(self):
        """Clear global implicit lookup.
        """

    @abstractmethod
    def reset(self):
        """Reset global implicit lookup to original lookup used for
        registration.

        This can be used to wipe out any composed lookups that
        were installed during this thread.
        """

    def _get_lookup(self):
        """Get the implicit ILokup."""

    def _set_lookup(self, value):
        """Set the implicit ILookup."""
    lookup = abstractproperty(_get_lookup, _set_lookup)

    # XXX abcs don't support defining required attributes apparently
    # attribute base_lookup
    # Access the base lookup that was registered using ``register()``.
    #
    # This can be used as a basis to compose a new lookup.
    # """


class NoImplicitRegistryError(Exception):
    pass


class NoImplicitLookupError(Exception):
    pass


class ComponentLookupError(TypeError):
    pass


class PredicateRegistryError(Exception):
    pass
