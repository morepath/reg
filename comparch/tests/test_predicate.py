import py.test
from comparch.predicate import PredicateRegistry, ANY_VALUE, tuple_permutations

def test_predicatemap():
    m = PredicateRegistry(['name', 'request_method'])
    m.register(dict(name='foo'), 'registered for all')
    m.register(dict(name='foo', request_method='POST'), 'registered for post')

    assert m.get(dict(name='foo', request_method='GET')) == 'registered for all'
    assert m.get(dict(name='foo', request_method='POST')) == 'registered for post'
    assert m.get(dict(name='bar'), default='default') == 'default'
    
def test_duplicate_entry():
    m = PredicateRegistry(['name', 'request_method'])

    m.register(dict(name='foo'), 'registered for all')
    m.register(dict(name='foo'), 'registered for all again')

    assert m.get(dict(name='foo', request_method='GET')) == 'registered for all again'

def test_involved_entry():
    m = PredicateRegistry(['a', 'b', 'c', 'd'])
    m.register(dict(a='A'), 'a=A')
    m.register(dict(a='A', b='B'), 'a=A b=B')
    m.register(dict(a='A', c='C'), 'a=A c=C')
    m.register(dict(a='A', b='B', c='C'), 'a=A b=B c=C')
    m.register(dict(a='A+', b='B'), 'a=A+ b=B')
    m.register(dict(b='B'), 'b=B')
    m.register(dict(a='A+', c='C'), 'a=A+ c=C')
    m.register(dict(b='B', d='D'), 'b=B d=D')
    
    assert m.get(dict(a='A', b='B', c='C')) == 'a=A b=B c=C'

    assert m.get(dict(a='BOO')) is None
    assert m.get(dict(a='A', b='SOMETHING')) == 'a=A'
    assert m.get(dict(a='A', b='SOMETHING', c='C')) == 'a=A c=C'
    assert m.get(dict(b='B')) == 'b=B'
    assert m.get(dict(a='SOMETHING', b='B', d='D')) == 'b=B d=D'

def test_break_early():
    m = PredicateRegistry(['a', 'b'])
    m.register(dict(b='B'), 'b=B')
    assert m.get(dict(b='C')) is None
    
def test_tuple_permutations():
    t = (('a', 'A'), ('b', 'B'))
    assert list(tuple_permutations(t)) == [
        (('a', 'A'), ('b', 'B')),
        (('a', 'A'), ('b', ANY_VALUE )),
        (('a', ANY_VALUE), ('b', 'B')),
        (('a', ANY_VALUE), ('b', ANY_VALUE))]
    t = (('a', ANY_VALUE), ('b', 'B'))
    assert list(tuple_permutations(t)) == [
        (('a', ANY_VALUE), ('b', 'B')),
        (('a', ANY_VALUE), ('b', ANY_VALUE))
        ]
