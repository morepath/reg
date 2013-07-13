import py.test
from comparch.mapping import (
    MapKey, Map, MultiMap, ClassMapKey, Registry, ancestor_multikeys)
    
def test_mapkey_without_parents():
    a = MapKey('a')
    assert a.key == 'a'
    assert a.parents == ()

def test_mapkey_with_parents():
    a = MapKey('a')
    b = MapKey('b', [a])
    assert b.parents == (a,)
    c = MapKey('c', (a,))
    assert c.parents == (a,)
    d = MapKey('d', [b, c])
    assert d.parents == (b, c)
    
def test_map_simple_key():
    m = Map()
    a = MapKey('a')
    m[a] = u'Value for A'
    assert m[a] == u'Value for A'

def test_map_same_underlying_key_is_same():
    m = Map()
    a = MapKey('a')
    a_another = MapKey('a')
    m[a] = u'Value for A'
    assert m[a_another] == u'Value for A'
    
def test_map_deletion():
    m = Map()
    a = MapKey('a')
    m[a] = u'Value for A'
    del m[a]
    with py.test.raises(KeyError):
        m[a]

def test_map_parent():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    c = MapKey('c', parents=[a])
    m[b] = u'Value for B'
    assert m[b] == u'Value for B'
    with py.test.raises(KeyError):
        m[c]
    with py.test.raises(KeyError):
        m[a]

def test_map_ancestor():
    m = Map()
    
    a = MapKey('a')
    b = MapKey('b', parents=[a])

    m = Map()
    m[a] = u'Value for A'
    assert m[b] == u'Value for A'

def test_map_ancestor_mro():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    c = MapKey('c', parents=[a])
    d = MapKey('d', parents=[b, c])
    
    m[b] = u'Value for B'
    m[c] = u'Value for C'

    # b comes first in mro
    assert m[d] == u'Value for B'

def test_map_ancestor_mro2():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    c = MapKey('c', parents=[a])
    d = MapKey('d', parents=[b, c])
    
    m[c] = u'Value for C'

    # now we do get C
    assert m[d] == u'Value for C'
    
def test_map_ancestor_direct_key_wins():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    c = MapKey('c', parents=[a])
    d = MapKey('d', parents=[b, c])
    
    m[b] = u'Value for B'
    m[c] = u'Value for C'
    m[d] = u'Value for D'
    
    assert m[d] == u'Value for D'

def test_map_all():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    c = MapKey('c', parents=[a])
    d = MapKey('d', parents=[b, c])

    m[b] = u'Value for B'
    m[c] = u'Value for C'
    m[d] = u'Value for D'
    assert list(m.all(d)) == [u'Value for D', u'Value for B', u'Value for C']

def test_map_all_empty(): 
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    c = MapKey('c', parents=[a])
    d = MapKey('d', parents=[b, c])

    m[b] = u'Value for B'
    m[c] = u'Value for C'
    m[d] = u'Value for D'
    assert list(m.all(d)) == [u'Value for D', u'Value for B', u'Value for C']
   
def test_exact_getitem():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    
    m[a] = u"Value for A"

    with py.test.raises(KeyError):
        m.exact_getitem(b)
    assert m.exact_getitem(a) == u'Value for A'

def test_exact_get():
    m = Map()
    a = MapKey('a')
    b = MapKey('b', parents=[a])
    
    m[a] = u"Value for A"

    assert m.exact_get(b) is None
    assert m.exact_get(b, u'default') == u'default'
    assert m.exact_get(a) == u'Value for A'
    
def test_multimap():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])
    three = MapKey('three', [two])

    m[(alpha, three)] = u'Value for alpha, three'
    m[(beta, two)] = u'Value for beta, two'

    assert m[(alpha, three)] == u'Value for alpha, three'
    assert m[(beta, two)] == u'Value for beta, two'

    assert m[(gamma, two)] == u'Value for beta, two'
    assert m[(beta, three)] == u'Value for beta, two'
    assert m[(gamma, three)] == u'Value for beta, two'
    
    with py.test.raises(KeyError):
        m[(alpha, one)]
    with py.test.raises(KeyError):
        m[(alpha, two)]
    with py.test.raises(KeyError):
        m[(beta, one)]

def test_ancestor_multikeys():
    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])
    three = MapKey('three', [two])

    assert list(ancestor_multikeys((gamma, two))) == [
        (gamma, two), (gamma, one), (beta, two),
        (beta, one), (alpha, two), (alpha, one)]
    
def test_multimap_arity_1():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    m[(alpha,)] = u'Value for alpha'
    m[(beta,)] = u'Value for beta'

    assert m[(alpha,)] == u'Value for alpha'
    assert m[(beta,)] == u'Value for beta'
    
def test_multimap_with_fallback():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])
    three = MapKey('three', [two])

    m[(alpha, three)] = u'Value for alpha, three'
    m[(beta, two)] = u'Value for beta, two'

    # fallback
    m[(alpha, one)] = u'Value for alpha, one'

    # this gets the more specific interface
    assert m[(alpha, three)] == u'Value for alpha, three'
    assert m[(beta, two)] == u'Value for beta, two'

    assert m[(gamma, two)] == u'Value for beta, two'
    assert m[(beta, three)] == u'Value for beta, two'
    assert m[(gamma, three)] == u'Value for beta, two'

    # this uses the fallback
    assert m[(alpha, one)] == u'Value for alpha, one'
    assert m[(alpha, two)] == u'Value for alpha, one'
    assert m[(beta, one)] == u'Value for alpha, one'

def test_multimap_all():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])
    three = MapKey('three', [two])

    m[(alpha, three)] = u'Value for alpha, three'
    m[(beta, two)] = u'Value for beta, two'
    m[(alpha, one)] = u'Value for alpha, one'

    # this gets the more specific interface
    assert m.all((alpha, three)) == [u'Value for alpha, three',
                                     u'Value for alpha, one']
    assert m.all((beta, two)) == [u'Value for beta, two',
                                  u'Value for alpha, one']
    assert m.all((gamma, two)) == [u'Value for beta, two',
                                   u'Value for alpha, one']
    assert m.all((beta, three)) == [u'Value for beta, two',
                                    u'Value for alpha, three',
                                    u'Value for alpha, one']
    assert m.all((gamma, three)) == [u'Value for beta, two',
                                     u'Value for alpha, three',
                                     u'Value for alpha, one']

    # this uses the fallback only
    assert m.all((alpha, one)) == [u'Value for alpha, one']
    assert m.all((alpha, two)) == [u'Value for alpha, one']
    assert m.all((beta, one)) == [u'Value for alpha, one']

    # we get nothing at all
    frub = MapKey('frub')
    assert m.all((frub,)) == []

# XXX test_multimap_deletion

def test_class_mapkey():
    class A(object):
        pass
    a = ClassMapKey(A)
    
    class B(A):
        pass
    b = ClassMapKey(B)
    
    class C(B):
        pass
    c = ClassMapKey(C)
    
    class D(B, A):
        pass
    d = ClassMapKey(D)

    assert a.parents == (ClassMapKey(object),) 
    assert a.ancestors == [ClassMapKey(A), ClassMapKey(object),]

    assert b.parents == (ClassMapKey(A),)
    assert b.ancestors == [ClassMapKey(B), ClassMapKey(A), ClassMapKey(object)]

    assert c.parents == (ClassMapKey(B),)
    assert c.ancestors == [ClassMapKey(C), ClassMapKey(B),
                           ClassMapKey(A), ClassMapKey(object)]

    assert d.parents == (ClassMapKey(B), ClassMapKey(A))
    assert d.ancestors == [ClassMapKey(D), ClassMapKey(B),
                           ClassMapKey(A), ClassMapKey(object)]

def test_registry_sources():
    reg = Registry()
    
    class Document(object):
        pass

    class SpecialDocument(Document):
        pass

    class LineCount(object):
        pass

    reg.register((Document,), LineCount, None,
                 'document line count')
    reg.register((SpecialDocument,), LineCount, None,
                 'special document line count')

    assert (reg.lookup((Document(),), LineCount, None) ==
            'document line count')
    
    assert (reg.lookup((SpecialDocument(),), LineCount, None) ==
            'special document line count')

    class AnotherDocument(Document):
        pass

    assert (reg.lookup((AnotherDocument(),), LineCount, None) ==
            'document line count')
                           
    class Other(object):
        pass
    
    assert reg.lookup((Other(),), LineCount, None) is None

def test_registry_target_find_specific():
    reg = Registry()
    
    class Document(object):
        pass

    class LineCount(object):
        pass

    class SpecialLineCount(LineCount):
        pass

    class SpecialDocument(Document):
        pass
    
    reg.register((Document,), LineCount, None, 'line count')
    reg.register((Document,), SpecialLineCount, None, 'special line count')

    assert reg.lookup((Document(),), LineCount, None) == 'line count'
    assert reg.lookup((Document(),), SpecialLineCount, None) == 'special line count'

    assert reg.lookup((SpecialDocument(),), LineCount, None) == 'line count'
    assert reg.lookup((SpecialDocument(),), SpecialLineCount, None) == 'special line count'

def test_registry_target_find_subclass():
    reg = Registry()

    class Document(object):
        pass

    class Animal(object):
        pass

    class Elephant(Animal):
        pass
    
    reg.register((Document,), Elephant, None, 'elephant')
    assert reg.lookup((Document(),), Animal, None) == 'elephant'
