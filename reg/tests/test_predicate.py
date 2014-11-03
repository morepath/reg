from __future__ import unicode_literals
import pytest
from reg.predicate import (PredicateRegistry, Predicate, KeyIndex, ANY,
                           key_permutations, PredicateRegistryError,
                           PredicateMatcher)
from reg.registry import Registry


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

    with pytest.raises(KeyError):
        m.get(dict(name='foo'))


def test_duplicate_entry():
    m = PredicateRegistry([Predicate('name', KeyIndex),
                           Predicate('request_method', KeyIndex)])

    m.register(dict(name='foo'), 'registered for all')
    m.register(dict(name='foo'), 'registered for all again')

    with pytest.raises(PredicateRegistryError):
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


def test_permutations_bigger():
    d = {'a': 'A', 'b': 'B', 'c': 'C'}
    assert list(key_permutations(['a', 'b', 'c'], d)) == [
        {'a': 'A', 'b': 'B', 'c': 'C'},
        {'a': 'A', 'b': 'B', 'c': ANY},
        {'a': 'A', 'b': ANY, 'c': 'C'},
        {'a': 'A', 'b': ANY, 'c': ANY},
        {'a': ANY, 'b': 'B', 'c': 'C'},
        {'a': ANY, 'b': 'B', 'c': ANY},
        {'a': ANY, 'b': ANY, 'c': 'C'},
        {'a': ANY, 'b': ANY, 'c': ANY}]


def test_predicate_matcher():
    reg = Registry()

    class Document(object):
        def __init__(self, a, b):
            self.a = a
            self.b = b

    def foo(obj):
        pass

    predicates = [
        Predicate('a', KeyIndex, lambda doc: doc.a, 'A'),
        Predicate('b', KeyIndex, lambda doc: doc.b, 'B')
        ]

    matcher = PredicateMatcher(predicates)
    matcher.register({'a': 'A'}, 'a = A')
    matcher.register({'b': 'B'}, 'b = B')
    matcher.register({}, 'nothing matches')

    reg.register(foo, [Document], matcher)

    assert reg.component(foo, [Document(a='A', b='C')]) == 'a = A'
    assert reg.component(foo, [Document(a='C', b='B')]) == 'b = B'
    assert reg.component(foo, [Document(a='A', b='B')]) == 'a = A'
    assert reg.component(foo, [Document(a='C', b='C')]) == 'nothing matches'

    # we can also override lookup by supplying our own predicates
    assert reg.component(foo, [Document(a='C', b='C')],
                         predicates={'a': 'A', 'b': 'C'}) == 'a = A'
    # if we don't supply something in predicates ourselves, a default will
    # be used
    assert reg.component(foo, [Document(a='C', b='C')],
                         predicates={'a': 'C'}) == 'b = B'
