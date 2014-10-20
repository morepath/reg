from ..neopredicate import (
    KeyPredicate, ClassPredicate, MultiPredicate, Registry)


def test_key_predicate_permutations():
    p = KeyPredicate()
    assert list(p.permutations('GET')) == ['GET']


def test_class_predicate_permutations():
    class Foo(object):
        pass

    class Bar(Foo):
        pass

    class Qux:
        pass

    p = ClassPredicate()

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

    p = MultiPredicate([ClassPredicate(), ClassPredicate()])

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
        KeyPredicate(),
        KeyPredicate(),
        KeyPredicate(),
    ])

    assert list(p.permutations(['A', 'B', 'C'])) == [
        ('A', 'B', 'C')]


def test_registry_single_key_predicate():
    r = Registry(KeyPredicate())

    r.register('A', 'A value')

    assert r.get('A') == 'A value'
    assert r.get('B') is None
    assert list(r.all('A')) == ['A value']
    assert list(r.all('B')) == []


def test_registry_single_class_predicate():
    r = Registry(ClassPredicate())

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


def test_registry_single_class_predicate_also_sub():
    r = Registry(ClassPredicate())

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


def test_registry_multi_class_predicate():
    r = Registry(MultiPredicate([
        ClassPredicate(),
        ClassPredicate(),
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


def test_registry_multi_mixed_predicate_class_key():
    r = Registry(MultiPredicate([
        ClassPredicate(),
        KeyPredicate(),
    ]))

    class A(object):
        pass

    class AA(A):
        pass

    class Unknown(object):
        pass

    r.register((A, 'B'), 'foo')

    assert r.get((A, 'B')) == 'foo'
    assert r.get((A, 'unknown')) is None
    assert r.get((AA, 'B')) == 'foo'
    assert r.get((AA, 'unknown')) is None
    assert r.get((Unknown, 'B')) is None


def test_registry_multi_mixed_predicate_key_class():
    r = Registry(MultiPredicate([
        KeyPredicate(),
        ClassPredicate(),
    ]))

    class B(object):
        pass

    class BB(B):
        pass

    class Unknown(object):
        pass

    r.register(('A', B), 'foo')

    assert r.get(('A', B)) == 'foo'
    assert r.get(('A', BB)) == 'foo'
    assert r.get(('A', Unknown)) is None
    assert r.get(('unknown', Unknown)) is None


def test_single_predicate_get_key():
    def get_key(foo):
        return foo

    p = KeyPredicate(get_key)

    assert p.get_key({'foo': 'value'}) == 'value'


def test_multi_predicate_get_key():
    def a_key(a):
        return a

    def b_key(b):
        return b

    p = MultiPredicate([KeyPredicate(a_key), KeyPredicate(b_key)])

    assert p.get_key(dict(a='A', b='B')) == ('A', 'B')


def test_single_predicate_fallback():
    r = Registry(KeyPredicate(fallback='fallback'))

    r.register('A', 'A value')

    assert r.get('A') == 'A value'
    assert r.get('B') is 'fallback'


