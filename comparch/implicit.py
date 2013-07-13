import threading
from .registry import Registry
from .abcs import IImplicit

class Local(threading.local):
    def __init__(self, **kw):
        self.__dict__.update(kw)
    
class Implicit(IImplicit):
    def __init__(self):
        self._registry = None
        self.local = None
        
    def initialize(self):
        self.initialize_with_registry(Registry())

    def initialize_with_registry(self, registry):
        self._registry = registry
        self.local = Local(lookup=registry)
        
    def clear(self):
        self._registry = None
        self.local = Local(lookup=None)
    
    @property
    def registry(self):
        return self._registry

    @property
    def base_lookup(self):
        return self.registry
        
    @property
    def lookup(self):
        if self.local is None:
            return None
        return self.local.lookup

    @lookup.setter
    def lookup(self, value):
        self.local.lookup = value

    def reset_lookup(self):
        self.lookup = self.base_lookup

implicit = Implicit()
