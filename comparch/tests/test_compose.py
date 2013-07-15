from comparch.registry import Registry
from comparch.interface import Interface
from comparch.compose import (
    ListClassLookup, ChainClassLookup, CachedClassLookup)

class ITarget(Interface):
    pass

def test_list_class_lookup():
    reg1 = Registry()
    reg2 = Registry()

    reg2.register(ITarget, (), None, 'reg2 component')

    lookup = ListClassLookup([reg1, reg2])
    assert lookup.get(ITarget, (), None) == 'reg2 component'

    reg1.register(ITarget, (), None, 'reg1 component')
    assert lookup.get(ITarget, (), None) == 'reg1 component'

def test_chain_class_lookup():
    reg1 = Registry()
    reg2 = Registry()

    reg2.register(ITarget, (), None, 'reg2 component')

    lookup = ChainClassLookup(reg1, reg2)
    assert lookup.get(ITarget, (), None) == 'reg2 component'

    reg1.register(ITarget, (), None, 'reg1 component')
    assert lookup.get(ITarget, (), None) == 'reg1 component'
    
def test_cached_class_lookup():
    reg = Registry()

    reg.register(ITarget, (), None, 'reg component')

    cached = CachedClassLookup(reg)

    assert cached.get(ITarget, (), None) == 'reg component'

    # we change the registration
    reg.register(ITarget, (), None, 'reg component changed')
                 
    # the cache won't know
    assert cached.get(ITarget, (), None) == 'reg component'
