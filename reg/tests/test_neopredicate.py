from ..neopredicate import (
    key_predicate, class_predicate, MultiPredicate, Registry)


def test_key_predicate_permutations():
    p = key_predicate()
    assert list(p.permutations('GET')) == ['GET']


def test_class_predicate_permutations():
    class Foo(object):
        pass

    class Bar(Foo):
        pass

    class Qux:
        pass

    p = class_predicate()

    assert list(p.permutations(Foo)) == [Foo, object]
    assert list(p.permutations(Bar)) == [Bar, Foo, object]
    # XXX do we want to fake Qux having object as a permutation?
    assert list(p.permutations(Qux)) == [Qux]


def test_multi_class_predicate_permutations():
    class ABase(object):
        pass

    class ASub(ABase):
        pass

    class BBase(object):
        pass

    class BSub(BBase):
        pass

    p = MultiPredicate([class_predicate(), class_predicate()])

    assert list(p.permutations([ASub, BSub])) == [
        (ASub, BSub),
        (ASub, BBase),
        (ASub, object),
        (ABase, BSub),
        (ABase, BBase),
        (ABase, object),
        (object, BSub),
        (object, BBase),
        (object, object),
    ]


def test_multi_key_predicate_permutations():
    p = MultiPredicate([
        key_predicate(),
        key_predicate(),
        key_predicate(),
    ])

    assert list(p.permutations(['A', 'B', 'C'])) == [
        ('A', 'B', 'C')]


def test_registry_single_key_predicate():
    r = Registry(key_predicate())

    r.register('A', 'A value')

    assert r.component('A') == 'A value'
    assert r.component('B') is None
    assert list(r.all('A')) == ['A value']
    assert list(r.all('B')) == []


def test_registry_single_class_predicate():
    r = Registry(class_predicate())

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    class Qux(object):
        pass

    r.register(Foo, 'foo')

    assert r.component(Foo) == 'foo'
    assert r.component(FooSub) == 'foo'
    assert r.component(Qux) is None


def test_registry_single_class_predicate_also_sub():
    r = Registry(class_predicate())

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    class Qux(object):
        pass

    r.register(Foo, 'foo')
    r.register(FooSub, 'sub')

    assert r.component(Foo) == 'foo'
    assert r.component(FooSub) == 'sub'
    assert r.component(Qux) is None


def test_registry_multi_class_predicate():
    r = Registry(MultiPredicate([
        class_predicate(),
        class_predicate(),
    ]))

    class A(object):
        pass

    class AA(A):
        pass

    class B(object):
        pass

    class BB(B):
        pass

    r.register((A, B), 'foo')

    assert r.component((A, B)) == 'foo'
    assert r.component((AA, BB)) == 'foo'
    assert r.component((AA, B)) == 'foo'
    assert r.component((A, BB)) == 'foo'
    assert r.component((A, object)) is None
    assert r.component((object, B)) is None


def test_registry_multi_mixed_predicate_class_key():
    r = Registry(MultiPredicate([
        class_predicate(),
        key_predicate(),
    ]))

    class A(object):
        pass

    class AA(A):
        pass

    class Unknown(object):
        pass

    r.register((A, 'B'), 'foo')

    assert r.component((A, 'B')) == 'foo'
    assert r.component((A, 'unknown')) is None
    assert r.component((AA, 'B')) == 'foo'
    assert r.component((AA, 'unknown')) is None
    assert r.component((Unknown, 'B')) is None


def test_registry_multi_mixed_predicate_key_class():
    r = Registry(MultiPredicate([
        key_predicate(),
        class_predicate(),
    ]))

    class B(object):
        pass

    class BB(B):
        pass

    class Unknown(object):
        pass

    r.register(('A', B), 'foo')

    assert r.component(('A', B)) == 'foo'
    assert r.component(('A', BB)) == 'foo'
    assert r.component(('A', Unknown)) is None
    assert r.component(('unknown', Unknown)) is None


def test_single_predicate_get_key():
    def get_key(argdict):
        return argdict['foo']

    p = key_predicate(get_key)

    assert p.get_key({'foo': 'value'}) == 'value'


def test_multi_predicate_get_key():
    def a_key(d):
        return d['a']

    def b_key(d):
        return d['b']

    p = MultiPredicate([key_predicate(a_key), key_predicate(b_key)])

    assert p.get_key(dict(a='A', b='B')) == ('A', 'B')


def test_single_predicate_fallback():
    r = Registry(key_predicate(fallback='fallback'))

    r.register('A', 'A value')

    assert r.component('A') == 'A value'
    assert r.component('B') is 'fallback'


def test_multi_predicate_fallback():
    r = Registry(MultiPredicate([key_predicate(fallback='fallback1'),
                                 key_predicate(fallback='fallback2')]))

    r.register(('A', 'B'), 'value')

    assert r.component(('A', 'B')) == 'value'
    assert r.component(('A', 'C')) == 'fallback2'
    assert r.component(('C', 'B')) == 'fallback1'

