from ..neopredicate import (KeyPredicate, ClassPredicate, MultiPredicate, FALLBACK,
                            Registry)


def test_key_predicate_permutations():
    p = KeyPredicate('foo', None)
    assert list(p.permutations('GET')) == ['GET', FALLBACK]


def test_class_predicate_permutations():
    class Foo(object):
        pass

    class Bar(Foo):
        pass

    class Qux:
        pass

    p = ClassPredicate('foo', None)

    assert list(p.permutations(Foo)) == [Foo, object, FALLBACK]
    assert list(p.permutations(Bar)) == [Bar, Foo, object, FALLBACK]
    # XXX do we want to fake Qux having object as a permutation?
    assert list(p.permutations(Qux)) == [Qux, FALLBACK]


def test_multi_class_predicate_permutations():
    class ABase(object):
        pass

    class ASub(ABase):
        pass

    class BBase(object):
        pass

    class BSub(BBase):
        pass

    p = MultiPredicate('multi', None,
                       [ClassPredicate('a', None),
                        ClassPredicate('b', None)])

    assert list(p.permutations([ASub, BSub])) == [
        (ASub, BSub),
        (ASub, BBase),
        (ASub, object),
        (ASub, FALLBACK),
        (ABase, BSub),
        (ABase, BBase),
        (ABase, object),
        (ABase, FALLBACK),
        (object, BSub),
        (object, BBase),
        (object, object),
        (object, FALLBACK),
        (FALLBACK, BSub),
        (FALLBACK, BBase),
        (FALLBACK, object),
        (FALLBACK, FALLBACK)]


def test_multi_key_predicate_permutations():
    p = MultiPredicate('multi', None, [
        KeyPredicate('a', None),
        KeyPredicate('b', None),
        KeyPredicate('c', None),
    ])

    assert list(p.permutations(['A', 'B', 'C'])) == [
        ('A', 'B', 'C'),
        ('A', 'B', FALLBACK),
        ('A', FALLBACK, 'C'),
        ('A', FALLBACK, FALLBACK),
        (FALLBACK, 'B', 'C'),
        (FALLBACK, 'B', FALLBACK),
        (FALLBACK, FALLBACK, 'C'),
        (FALLBACK, FALLBACK, FALLBACK)]


def test_registry_single_key_predicate():
    r = Registry(KeyPredicate('a', None))

    r.register('A', 'A value')

    assert r.get('A') == 'A value'
    assert r.get('B') is None
    assert list(r.all('A')) == ['A value']
    assert list(r.all('B')) == []
    assert r.get(FALLBACK) is None


def test_registry_single_class_predicate():
    r = Registry(ClassPredicate('a', None))

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    class Qux(object):
        pass

    r.register(Foo, 'foo')

    assert r.get(Foo) == 'foo'
    assert r.get(FooSub) == 'foo'
    assert r.get(Qux) is None
    assert r.get(FALLBACK) is None


def test_registry_single_class_predicate_also_sub():
    r = Registry(ClassPredicate('a', None))

    class Foo(object):
        pass

    class FooSub(Foo):
        pass

    class Qux(object):
        pass

    r.register(Foo, 'foo')
    r.register(FooSub, 'sub')

    assert r.get(Foo) == 'foo'
    assert r.get(FooSub) == 'sub'
    assert r.get(Qux) is None
    assert r.get(FALLBACK) is None


def test_registry_multi_class_predicate():
    r = Registry(MultiPredicate('multi',  None, [
        ClassPredicate('a', None),
        ClassPredicate('b', None),
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

    assert r.get((A, B)) == 'foo'
    assert r.get((AA, BB)) == 'foo'
    assert r.get((AA, B)) == 'foo'
    assert r.get((A, BB)) == 'foo'
    assert r.get((A, object)) is None
    assert r.get((object, B)) is None
    assert r.get((FALLBACK, FALLBACK)) is None


def test_registry_multi_mixed_predicate_class_key():
    r = Registry(MultiPredicate('multi',  None, [
        ClassPredicate('a', None),
        KeyPredicate('b', None),
    ]))

    class A(object):
        pass

    class AA(A):
        pass

    class Unknown(object):
        pass

    r.register((A, 'B'), 'foo')
    r.register((A, FALLBACK), 'fallback')

    assert r.get((A, 'B')) == 'foo'
    assert r.get((A, 'unknown')) == 'fallback'
    assert r.get((AA, 'B')) == 'foo'
    assert r.get((AA, 'unknown')) == 'fallback'
    assert r.get((Unknown, 'B')) is None


def test_registry_multi_mixed_predicate_key_class():
    r = Registry(MultiPredicate('multi',  None, [
        KeyPredicate('a', None),
        ClassPredicate('b', None),
    ]))

    class B(object):
        pass

    class BB(B):
        pass

    class Unknown(object):
        pass

    r.register(('A', B), 'foo')
    r.register((FALLBACK, FALLBACK), 'fallback')

    assert r.get(('A', B)) == 'foo'
    assert r.get(('A', BB)) == 'foo'
    assert r.get(('A', Unknown)) == 'fallback'
    assert r.get(('unknown', Unknown)) == 'fallback'
