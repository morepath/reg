import threading
from .interfaces import IImplicit

class Implicit(IImplicit):
    def __init__(self):
        self.base_lookup = None
        self.local = None

    def initialize(self, lookup):
        self.base_lookup = lookup
        self.local = Local(lookup=self.base_lookup)
        
    def clear(self):
        self.base_lookup = None
        self.local = Local(lookup=None)

    def reset(self):
        self.local.lookup = self.base_lookup
    
    @property
    def lookup(self):
        if self.local is None:
            return None
        return self.local.lookup

    @lookup.setter
    def lookup(self, value):
        self.local.lookup = value

class Local(threading.local):
    def __init__(self, **kw):
        self.__dict__.update(kw)

implicit = Implicit()
