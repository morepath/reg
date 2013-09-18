from reg.registry import ClassRegistry as Registry
from reg.interface import Interface
from reg.compose import (
    ListClassLookup, ChainClassLookup, CachedClassLookup)


class ITarget(Interface):
    pass


def test_list_class_lookup():
    reg1 = Registry()
    reg2 = Registry()

    reg2.register(ITarget, (), 'reg2 component')

    lookup = ListClassLookup([reg1, reg2])
    assert lookup.get(ITarget, ()) == 'reg2 component'

    reg1.register(ITarget, (), 'reg1 component')
    assert lookup.get(ITarget, ()) == 'reg1 component'


def test_list_class_lookup_all():
    reg1 = Registry()
    reg2 = Registry()

    reg1.register(ITarget, (), 'reg1')
    reg2.register(ITarget, (), 'reg2')

    lookup = ListClassLookup([reg1, reg2])
    assert list(lookup.get_all(ITarget, ())) == ['reg1', 'reg2']


def test_chain_class_lookup():
    reg1 = Registry()
    reg2 = Registry()

    reg2.register(ITarget, (), 'reg2 component')

    lookup = ChainClassLookup(reg1, reg2)
    assert lookup.get(ITarget, ()) == 'reg2 component'

    reg1.register(ITarget, (), 'reg1 component')
    assert lookup.get(ITarget, ()) == 'reg1 component'


def test_chain_class_lookup_all():
    reg1 = Registry()
    reg2 = Registry()

    reg1.register(ITarget, (), 'reg1')
    reg2.register(ITarget, (), 'reg2')

    lookup = ChainClassLookup(reg1, reg2)
    assert list(lookup.get_all(ITarget, ())) == ['reg1', 'reg2']


def test_cached_class_lookup():
    reg = Registry()

    reg.register(ITarget, (), 'reg component')

    cached = CachedClassLookup(reg)

    assert cached.get(ITarget, ()) == 'reg component'

    # we change the registration
    reg.register(ITarget, (), 'reg component changed')

    # the cache won't know
    assert cached.get(ITarget, ()) == 'reg component'


def test_cached_class_lookup_all():
    reg = Registry()

    reg.register(ITarget, (), 'reg component')

    cached = CachedClassLookup(reg)

    assert list(cached.get_all(ITarget, ())) == ['reg component']

    # we change the registration
    reg.register(ITarget, (), 'reg component changed')

    # the cache won't know
    assert list(cached.get_all(ITarget, ())) == ['reg component']
