import py.test
from reg.predicate import (PredicateRegistry, Predicate, KeyIndex, ANY,
                           key_permutations, PredicateRegistryError)


def test_predicate_registry():
    m = PredicateRegistry([Predicate('name', KeyIndex),
                           Predicate('request_method', KeyIndex)])
    m.register(dict(name='foo'), 'registered for all')
    m.register(dict(name='foo', request_method='POST'), 'registered for post')

    assert (m.get(dict(name='foo', request_method='GET')) ==
            'registered for all')
    assert (m.get(dict(name='foo', request_method='POST')) ==
            'registered for post')
    assert (m.get(dict(name='bar', request_method='GET'), default='default') ==
            'default')


def test_predicate_registry_missing_key():
    m = PredicateRegistry([Predicate('name', KeyIndex),
                           Predicate('request_method', KeyIndex)])
    m.register(dict(name='foo', request_method='POST'), 'registered for post')

    with py.test.raises(PredicateRegistryError):
        m.get(dict(name='foo'))


def test_duplicate_entry():
    m = PredicateRegistry([Predicate('name', KeyIndex),
                           Predicate('request_method', KeyIndex)])

    m.register(dict(name='foo'), 'registered for all')
    m.register(dict(name='foo'), 'registered for all again')

    with py.test.raises(PredicateRegistryError):
        m.get(dict(name='foo', request_method='GET'))


def test_involved_entry():
    m = PredicateRegistry([Predicate('a', KeyIndex),
                           Predicate('b', KeyIndex),
                           Predicate('c', KeyIndex),
                           Predicate('d', KeyIndex)])
    m.register(dict(a='A'), 'a=A')
    m.register(dict(a='A', b='B'), 'a=A b=B')
    m.register(dict(a='A', c='C'), 'a=A c=C')
    m.register(dict(a='A', b='B', c='C'), 'a=A b=B c=C')
    m.register(dict(a='A+', b='B'), 'a=A+ b=B')
    m.register(dict(b='B'), 'b=B')
    m.register(dict(a='A+', c='C'), 'a=A+ c=C')
    m.register(dict(b='B', d='D'), 'b=B d=D')

    assert m.get(dict(a='A', b='B', c='C', d=ANY)) == 'a=A b=B c=C'

    assert m.get(dict(a='BOO', b=ANY, c=ANY, d=ANY)) is None
    assert m.get(dict(a='A', b='SOMETHING', c=ANY, d=ANY)) == 'a=A'
    assert m.get(dict(a='A', b='SOMETHING', c='C', d=ANY)) == 'a=A c=C'
    assert m.get(dict(a=ANY, b='B', c=ANY, d=ANY)) == 'b=B'
    assert m.get(dict(a='SOMETHING', b='B', c=ANY, d='D')) == 'b=B d=D'


def test_break_early():
    m = PredicateRegistry([Predicate('a', KeyIndex), Predicate('b', KeyIndex)])
    m.register(dict(b='B'), 'b=B')
    assert m.get(dict(a=ANY, b='C')) is None


def test_permutations():
    d = {'a': 'A', 'b': 'B'}
    assert list(key_permutations(['a', 'b'], d)) == [
        {'a': 'A', 'b': 'B'},
        {'a': 'A', 'b': ANY},
        {'a': ANY, 'b': 'B'},
        {'a': ANY, 'b': ANY}]
