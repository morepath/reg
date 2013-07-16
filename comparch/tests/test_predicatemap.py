import py.test
from comparch.predicate import PredicateMap, ANY_VALUE, tuple_permutations

def test_predicatemap():
    m = PredicateMap(['name', 'request_method'])
    m[dict(name='foo')] = 'registered for all'
    m[dict(name='foo', request_method='POST')] = 'registered for post'

    assert m[dict(name='foo', request_method='GET')] == 'registered for all'
    assert m[dict(name='foo', request_method='POST')] == 'registered for post'

def test_duplicate_entry():
    m = PredicateMap(['name', 'request_method'])

    m[dict(name='foo')] = 'registered for all'
    m[dict(name='foo')] = 'registered for all again'

    assert m[dict(name='foo', request_method='GET')] == 'registered for all again'

def test_involved_entry():
    m = PredicateMap(['a', 'b', 'c', 'd'])
    m[dict(a='A')] = 'a=A'
    m[dict(a='A', b='B')] = 'a=A b=B'
    m[dict(a='A', c='C')] = 'a=A c=C'
    m[dict(a='A', b='B', c='C')] = 'a=A b=B c=C'
    m[dict(a='A+', b='B')] = 'a=A+ b=B'
    m[dict(b='B')] = 'b=B'
    m[dict(a='A+', c='C')] = 'a=A+ c=C'
    m[dict(b='B', d='D')] = 'b=B d=D'
    
    assert m[dict(a='A', b='B', c='C')] == 'a=A b=B c=C'
    with py.test.raises(KeyError):
        m[dict(a='BOO')]
    assert m[dict(a='A', b='SOMETHING')] == 'a=A'
    assert m[dict(a='A', b='SOMETHING', c='C')] == 'a=A c=C'
    assert m[dict(b='B')] == 'b=B'
    assert m[dict(a='SOMETHING', b='B', d='D')] == 'b=B d=D'
    
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
