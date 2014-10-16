from ..neopredicate import (KeyPredicate, ClassPredicate, MultiPredicate, ANY,
                            Registry)


def test_key_predicate_permutations():
    p = KeyPredicate('foo', None)
    assert list(p.permutations('GET')) == ['GET', ANY]


def test_class_predicate_permutations():
    class Foo(object):
        pass

    class Bar(Foo):
        pass

    class Qux:
        pass

    p = ClassPredicate('foo', None)

    assert list(p.permutations(Foo)) == [Foo, object, ANY]
    assert list(p.permutations(Bar)) == [Bar, Foo, object, ANY]
    # XXX do we want to fake Qux having object as a permutation?
    assert list(p.permutations(Qux)) == [Qux, ANY]


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
        (ASub, ANY),
        (ABase, BSub),
        (ABase, BBase),
        (ABase, object),
        (ABase, ANY),
        (object, BSub),
        (object, BBase),
        (object, object),
        (object, ANY),
        (ANY, BSub),
        (ANY, BBase),
        (ANY, object),
        (ANY, ANY)]


def test_multi_key_predicate_permutations():
    p = MultiPredicate('multi', None, [
        KeyPredicate('a', None),
        KeyPredicate('b', None),
        KeyPredicate('c', None),
    ])

    assert list(p.permutations(['A', 'B', 'C'])) == [
        ('A', 'B', 'C'),
        ('A', 'B', ANY),
        ('A', ANY, 'C'),
        ('A', ANY, ANY),
        (ANY, 'B', 'C'),
        (ANY, 'B', ANY),
        (ANY, ANY, 'C'),
        (ANY, ANY, ANY)]


def test_registry_single_key_predicate():
    r = Registry(KeyPredicate('a', None))

    r.register('A', 'A value')

    assert r.get('A') == 'A value'
    assert r.get('B') is None
    assert list(r.all('A')) == ['A value']
    assert list(r.all('B')) == []

