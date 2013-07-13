from .interface import Interface, abstractmethod, abstractproperty

class ILookup(Interface):
    @abstractmethod
    def component(self, target, objs, discriminator):
        """Look up a component in the registry.
        
        The target is the class that we want to look up. The component
        found should normally be a subclass of that class, but no such
        checking is done and it doesn't have to be.
        
        objs is a list of 0 to n objects that we use to look up the
        component.  If multiple objs are listed, the lookup is made
        for that combination of objs. The classes of the objects are
        used to do the look up.

        The discriminator is a immutable object (such as a string or a
        tuple) under which the component should be looked up. If the
        component hasn't been registered with that discriminator, it
        won't be found.
        
        If the component can be found, it will be returned. If the
        component cannot be found, ``None`` is returned.
        """

    @abstractmethod
    def adapt(self, target, objs, discriminator):
        """Look up an adapter in the registry. Adapt objs to target abc.
        
        The behavior of this method is like that of lookup, but it
        performs an extra step: it calls the found component with the
        objs given as arguments. The resulting instance should be a
        subclass of the target class (although no such checking is
        done).
        """

class IChainLookup(ILookup):
    @abstractproperty
    def lookup(self):
        "The first ILookup to look in."
    @abstractproperty
    def next(self):
        "The next ILookup in the chain."

class IRegistry(Interface):
    @abstractmethod
    def register(self, target, sources, discriminator, component):
        """Register a component with the registry.

        The target is a class by which the component can be
        looked up.  The registered object should either be an instance
        of that class, or in the case of an adapter, return a such an
        instance.
        
        sources is a list of 0 to n classes that
        the component is registered for. If multiple sources are listed,
        a registration is made for that combination of sources.

        The discriminator is an immutable value under which the
        component should be registered. This can be used to
        distinguish different registrations from each other.
        
        The component is a python object (function, class, instance) that is
        registered.
        """
        
class IImplicit(Interface):
    """Implicit global registry and lookup.

    Comparch supports an implicit registry and lookup to be set up
    globally. The implicit global registry can be used in registration code.
    The implicit global lookup can be used for lookups.
    
    The global registry is normally only set up once per application,
    during startup time. The initialize method will set up the default
    registry. This also sets up a lookup for this
    registry. Afterwards, the registry can be accessed through the
    ``registry`` property (but cannot be set through this).
    
    The global implicit lookup can be accessed through the ``lookup``
    property.
    
    Changing the implicit lookup during run-time is done by simply
    assigning to it. Typically you'd assign an lookup constructed
    using comparch.ListLookup or comparch.ChainLookup. This way a
    lookup can look for a component in one registry first, and then
    fall back to another registry, etc.

    To change the lookup back to a lookup in the global implicit
    registry, call ``reset_lookup``.
    
    The implicit lookup is thread-local: each thread has a separate
    implicit global lookup.
    """

    @abstractproperty
    def registry(self):
        """IRegistry. Read-only."""

    def _get_lookup(self):
        """Get the implicit lookup."""
        
    def _set_lookup(self, value):
        """Set the implicit lookup."""
    lookup = abstractproperty(_get_lookup, _set_lookup)

    @abstractproperty
    def base_lookup(self):
        """ILookup based on IRegistry"""

    @abstractmethod
    def initialize(self):
        """Set up a standard global implicit registry and lookup.
        """

    @abstractmethod
    def initialize_with_registry(self, registry):
        """Set up global implicit registry and lookup according to argument.
        """

    @abstractmethod
    def clear(self):
        """Clear global implicit registry and lookup.
        """

    @abstractmethod
    def reset_lookup(self):
        """Reset global implicit lookup to base_lookup.
        """
   
class NoImplicitRegistryError(Exception):
    pass

class NoImplicitLookupError(Exception):
    pass

class ComponentLookupError(TypeError):
    pass
