import py.test
from comparch.mapping import (
    MapKey, Map, MultiMapKey, MultiMap, ClassMapKey, InverseMap)


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

    m[MultiMapKey(alpha, three)] = u'Value for alpha, three'
    m[MultiMapKey(beta, two)] = u'Value for beta, two'

    assert m[MultiMapKey(alpha, three)] == u'Value for alpha, three'
    assert m[MultiMapKey(beta, two)] == u'Value for beta, two'

    assert m[MultiMapKey(gamma, two)] == u'Value for beta, two'
    assert m[MultiMapKey(beta, three)] == u'Value for beta, two'
    assert m[MultiMapKey(gamma, three)] == u'Value for beta, two'

    with py.test.raises(KeyError):
        m[MultiMapKey(alpha, one)]
    with py.test.raises(KeyError):
        m[MultiMapKey(alpha, two)]
    with py.test.raises(KeyError):
        m[MultiMapKey(beta, one)]


def test_ancestor_multikeys():
    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])

    assert list(MultiMapKey(gamma, two).ancestors) == [
        MultiMapKey(gamma, two), MultiMapKey(gamma, one),
        MultiMapKey(beta, two), MultiMapKey(beta, one),
        MultiMapKey(alpha, two), MultiMapKey(alpha, one)]


def test_multimap_arity_1():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])

    m[MultiMapKey(alpha)] = u'Value for alpha'
    m[MultiMapKey(beta)] = u'Value for beta'

    assert m[MultiMapKey(alpha)] == u'Value for alpha'
    assert m[MultiMapKey(beta)] == u'Value for beta'


def test_multimap_with_fallback():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])
    three = MapKey('three', [two])

    m[MultiMapKey(alpha, three)] = u'Value for alpha, three'
    m[MultiMapKey(beta, two)] = u'Value for beta, two'

    # fallback
    m[MultiMapKey(alpha, one)] = u'Value for alpha, one'

    # this gets the more specific interface
    assert m[MultiMapKey(alpha, three)] == u'Value for alpha, three'
    assert m[MultiMapKey(beta, two)] == u'Value for beta, two'

    assert m[MultiMapKey(gamma, two)] == u'Value for beta, two'
    assert m[MultiMapKey(beta, three)] == u'Value for beta, two'
    assert m[MultiMapKey(gamma, three)] == u'Value for beta, two'

    # this uses the fallback
    assert m[MultiMapKey(alpha, one)] == u'Value for alpha, one'
    assert m[MultiMapKey(alpha, two)] == u'Value for alpha, one'
    assert m[MultiMapKey(beta, one)] == u'Value for alpha, one'


def test_multimap_all():
    m = MultiMap()

    alpha = MapKey('alpha')
    beta = MapKey('beta', [alpha])
    gamma = MapKey('gamma', [beta])

    one = MapKey('one')
    two = MapKey('two', [one])
    three = MapKey('three', [two])

    m[MultiMapKey(alpha, three)] = u'Value for alpha, three'
    m[MultiMapKey(beta, two)] = u'Value for beta, two'
    m[MultiMapKey(alpha, one)] = u'Value for alpha, one'

    # this gets the more specific interface
    assert list(m.all(MultiMapKey(alpha, three))) == [
        u'Value for alpha, three',
        u'Value for alpha, one']
    assert list(m.all(MultiMapKey(beta, two))) == [
        u'Value for beta, two',
        u'Value for alpha, one']
    assert list(m.all(MultiMapKey(gamma, two))) == [
        u'Value for beta, two',
        u'Value for alpha, one']
    assert list(m.all(MultiMapKey(beta, three))) == [
        u'Value for beta, two',
        u'Value for alpha, three',
        u'Value for alpha, one']
    assert list(m.all(MultiMapKey(gamma, three))) == [
        u'Value for beta, two',
        u'Value for alpha, three',
        u'Value for alpha, one']

    # this uses the fallback only
    assert list(m.all(MultiMapKey(alpha, one))) == [u'Value for alpha, one']
    assert list(m.all(MultiMapKey(alpha, two))) == [u'Value for alpha, one']
    assert list(m.all(MultiMapKey(beta, one))) == [u'Value for alpha, one']

    # we get nothing at all
    frub = MapKey('frub')
    assert list(m.all(MultiMapKey(frub,))) == []


def test_multimap_empty_key():
    m = MultiMap()
    assert list(MultiMapKey().ancestors) == [MultiMapKey()]

    m[MultiMapKey()] = u'Value for the empty'
    assert m[MultiMapKey()] == u'Value for the empty'
    assert list(m.all(MultiMapKey())) == [u'Value for the empty']


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
    assert a.ancestors == [ClassMapKey(A), ClassMapKey(object)]

    assert b.parents == (ClassMapKey(A),)
    assert b.ancestors == [ClassMapKey(B), ClassMapKey(A), ClassMapKey(object)]

    assert c.parents == (ClassMapKey(B),)
    assert c.ancestors == [ClassMapKey(C), ClassMapKey(B),
                           ClassMapKey(A), ClassMapKey(object)]

    assert d.parents == (ClassMapKey(B), ClassMapKey(A))
    assert d.ancestors == [ClassMapKey(D), ClassMapKey(B),
                           ClassMapKey(A), ClassMapKey(object)]


def test_inverse_map():
    m = InverseMap()

    animal = MapKey('animal')
    elephant = MapKey('elephant', parents=[animal])
    african_elephant = MapKey('african elephant', parents=[elephant])

    m.register(animal, 'Animal')
    m.register(elephant, 'Elephant')

    assert list(m.all(animal)) == ['Animal', 'Elephant']
    assert list(m.all(elephant)) == ['Elephant']
    assert list(m.all(african_elephant)) == []


def test_inverse_map_registration_order():
    m = InverseMap()

    animal = MapKey('animal')
    elephant = MapKey('elephant', parents=[animal])
    african_elephant = MapKey('african elephant', parents=[elephant])

    m.register(elephant, 'Elephant')
    m.register(animal, 'Animal')

    assert list(m.all(animal)) == ['Animal', 'Elephant']
    assert list(m.all(elephant)) == ['Elephant']
    assert list(m.all(african_elephant)) == []


def test_inverse_map_sub():
    m = InverseMap()

    animal = MapKey('animal')
    elephant = MapKey('elephant', parents=[animal])
    african_elephant = MapKey('african elephant', parents=[elephant])

    m.register(elephant, 'Elephant')

    assert list(m.all(animal)) == ['Elephant']
    assert list(m.all(elephant)) == ['Elephant']
    assert list(m.all(african_elephant)) == []


def test_inverse_map_sub2():
    m = InverseMap()

    animal = MapKey('animal')
    elephant = MapKey('elephant', parents=[animal])
    african_elephant = MapKey('african elephant', parents=[elephant])

    m.register(african_elephant, 'African Elephant')

    assert list(m.all(animal)) == ['African Elephant']
    assert list(m.all(elephant)) == ['African Elephant']
    assert list(m.all(african_elephant)) == ['African Elephant']


def test_inverse_map_two_descendants():
    m = InverseMap()

    animal = MapKey('animal')
    elephant = MapKey('elephant', parents=[animal])
    rhino = MapKey('rhino', parents=[animal])

    m.register(elephant, 'Elephant')
    m.register(rhino, 'Rhino')

    assert list(m.all(elephant)) == ['Elephant']
    assert list(m.all(rhino)) == ['Rhino']

    # we get out the descendants in declaration order
    assert list(m.all(animal)) == ['Elephant', 'Rhino']


def test_inverse_map_empty():
    m = InverseMap()

    animal = MapKey('animal')

    assert list(m.all(animal)) == []
