from ..predicate import (KeyIndex, ClassIndex, MultiIndex,
                         key_predicate, class_predicate, MultiPredicate,
                         PredicateRegistry as Registry, NOT_FOUND)
from ..error import RegistrationError
import pytest


def test_key_index_permutations():
    i = KeyIndex()
    assert list(i.permutations('GET')) == ['GET']


def test_class_index_permutations():
    class Foo(object):
        pass

    class Bar(Foo):
        pass

    class Qux:
        pass

    i = ClassIndex()

    assert list(i.permutations(Foo)) == [Foo, object]
    assert list(i.permutations(Bar)) == [Bar, Foo, object]
    assert list(i.permutations(Qux)) == [Qux, object]


def test_multi_class_predicate_permutations():
    class ABase(object):
        pass

    class ASub(ABase):
        pass

    class BBase(object):
        pass

    class BSub(BBase):
        pass

    i = MultiIndex([class_predicate('a'), class_predicate('a')])

    assert list(i.permutations([ASub, BSub])) == [
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
    i = MultiIndex([
        key_predicate('a'),
        key_predicate('b'),
        key_predicate('c'),
    ])

    assert list(i.permutations(['A', 'B', 'C'])) == [
        ('A', 'B', 'C')]


def test_registry_single_key_predicate():
    r = Registry(key_predicate('a'))

    r.register('A', 'A value')

    assert r.component('A') == 'A value'
    assert r.component('B') is None
    assert list(r.all('A')) == ['A value']
    assert list(r.all('B')) == []


def test_registry_single_class_predicate():
    r = Registry(class_predicate('a'))

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
    assert list(r.all(Foo)) == ['foo']
    assert list(r.all(FooSub)) == ['foo']
    assert list(r.all(Qux)) == []


def test_registry_single_classic_class_predicate():
    r = Registry(class_predicate('a'))

    class Foo:
        pass

    class FooSub(Foo):
        pass

    class Qux:
        pass

    r.register(Foo, 'foo')

    assert r.component(Foo) == 'foo'
    assert r.component(FooSub) == 'foo'
    assert r.component(Qux) is None
    assert list(r.all(Foo)) == ['foo']
    assert list(r.all(FooSub)) == ['foo']
    assert list(r.all(Qux)) == []


def test_registry_single_class_predicate_also_sub():
    r = Registry(class_predicate('a'))

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
    assert list(r.all(Foo)) == ['foo']
    assert list(r.all(FooSub)) == ['sub', 'foo']
    assert list(r.all(Qux)) == []


def test_registry_multi_class_predicate():
    r = Registry(MultiPredicate([
        class_predicate('a'),
        class_predicate('b'),
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

    assert list(r.all((A, B))) == ['foo']
    assert list(r.all((AA, BB))) == ['foo']
    assert list(r.all((AA, B))) == ['foo']
    assert list(r.all((A, BB))) == ['foo']
    assert list(r.all((A, object))) == []
    assert list(r.all((object, B))) == []


def test_registry_multi_mixed_predicate_class_key():
    r = Registry(MultiPredicate([
        class_predicate('a'),
        key_predicate('b'),
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

    assert list(r.all((A, 'B'))) == ['foo']
    assert list(r.all((A, 'unknown'))) == []
    assert list(r.all((AA, 'B'))) == ['foo']
    assert list(r.all((AA, 'unknown'))) == []
    assert list(r.all((Unknown, 'B'))) == []


def test_registry_multi_mixed_predicate_key_class():
    r = Registry(MultiPredicate([
        key_predicate('a'),
        class_predicate('b'),
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

    assert list(r.all(('A', B))) == ['foo']
    assert list(r.all(('A', BB))) == ['foo']
    assert list(r.all(('A', Unknown))) == []
    assert list(r.all(('unknown', Unknown))) == []


def test_single_predicate_get_key():
    def get_key(argdict):
        return argdict['foo']

    p = key_predicate('a', get_key)

    assert p.get_key({'foo': 'value'}) == 'value'


def test_multi_predicate_get_key():
    def a_key(d):
        return d['a']

    def b_key(d):
        return d['b']

    p = MultiPredicate([key_predicate('a', a_key),
                        key_predicate('b', b_key)])

    assert p.get_key(dict(a='A', b='B')) == ('A', 'B')


def test_single_predicate_fallback():
    r = Registry(key_predicate('a', fallback='fallback'))

    r.register('A', 'A value')

    assert r.component('A') == 'A value'
    assert r.component('B') is None
    assert r.fallback('B') == 'fallback'


def test_multi_predicate_fallback():
    r = Registry(MultiPredicate([key_predicate('a', fallback='fallback1'),
                                 key_predicate('b', fallback='fallback2')]))

    r.register(('A', 'B'), 'value')

    assert r.component(('A', 'B')) == 'value'
    assert r.component(('A', 'C')) is None
    assert r.fallback(('A', 'C')) == 'fallback2'
    assert r.component(('C', 'B')) is None
    assert r.fallback(('C', 'B')) == 'fallback1'

    assert list(r.all(('A', 'B'))) == ['value']
    assert list(r.all(('A', 'C'))) == []
    assert list(r.all(('C', 'B'))) == []


def test_predicate_self_request():
    m = Registry(MultiPredicate([
        key_predicate('a'),
        key_predicate('b', fallback='registered for all')]))
    m.register(('foo', 'POST'), 'registered for post')

    assert m.component(('foo', 'GET')) is None
    assert m.fallback(('foo', 'GET')) == 'registered for all'
    assert m.component(('foo', 'POST')) == 'registered for post'
    assert m.fallback(('foo', 'POST')) is NOT_FOUND
    assert m.component(('bar', 'GET')) is None


# XXX using an incomplete key returns undefined results

def test_predicate_duplicate_key():
    m = Registry(MultiPredicate([
        key_predicate('a'),
        key_predicate('b', fallback='registered for all')]))
    m.register(('foo', 'POST'), 'registered for post')
    with pytest.raises(RegistrationError):
        m.register(('foo', 'POST'), 'registered again')


def test_name_request_method_body_model_registered_for_base():
    m = Registry(MultiPredicate([
        key_predicate('name', fallback='name fallback'),
        key_predicate('request_method', fallback='request_method fallback'),
        class_predicate('body_model', fallback='body_model fallback')]))

    class Foo(object):
        pass

    class Bar(Foo):
        pass

    m.register(('foo', 'POST', Foo), 'post foo')

    assert m.component(('bar', 'GET', object)) is None
    assert m.fallback(('bar', 'GET', object)) == 'name fallback'
    assert m.component(('foo', 'GET', object)) is None
    assert m.fallback(('foo', 'GET', object)) == 'request_method fallback'
    assert m.component(('foo', 'POST', object)) is None
    assert m.fallback(('foo', 'POST', object)) == 'body_model fallback'
    assert m.component(('foo', 'POST', Foo)) == 'post foo'
    assert m.component(('foo', 'POST', Bar)) == 'post foo'


def test_name_request_method_body_model_registered_for_base_and_sub():
    m = Registry(MultiPredicate([
        key_predicate('name', fallback='name fallback'),
        key_predicate('request', fallback='request_method fallback'),
        class_predicate('body_model', fallback='body_model fallback')]))

    class Foo(object):
        pass

    class Bar(Foo):
        pass

    m.register(('foo', 'POST', Foo), 'post foo')
    m.register(('foo', 'POST', Bar), 'post bar')

    assert m.component(('bar', 'GET', object)) is None
    assert m.fallback(('bar', 'GET', object)) == 'name fallback'

    assert m.component(('foo', 'GET', object)) is None
    assert m.fallback(('foo', 'GET', object)) == 'request_method fallback'

    assert m.component(('foo', 'POST', object)) is None
    assert m.fallback(('foo', 'POST', object)) == 'body_model fallback'

    assert m.component(('foo', 'POST', Foo)) == 'post foo'
    assert m.component(('foo', 'POST', Bar)) == 'post bar'


def test_key_by_predicate_name():
    p = key_predicate('foo', default='default')

    assert p.key_by_predicate_name({'foo': 'value'}) == 'value'
    assert p.key_by_predicate_name({}) == 'default'


def test_multi_key_by_predicate_name():
    p = MultiPredicate([key_predicate('foo', default='default foo'),
                        key_predicate('bar', default='default bar')])
    assert p.key_by_predicate_name({'foo': 'FOO',
                                    'bar': 'BAR'}) == ('FOO', 'BAR')
    assert p.key_by_predicate_name({}) == ('default foo', 'default bar')


def test_nameless_predicate_key():
    p = key_predicate('a')

    assert p.key_by_predicate_name({}) is None
