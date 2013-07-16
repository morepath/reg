from comparch.predicate import PredicateMap, ANY_VALUE, tuple_permutations

def test_predicatemap():
    m = PredicateMap(['name', 'request_method'])
    m[dict(name='foo')] = 'registered for all'
    m[dict(name='foo', request_method='POST')] = 'registered for post'

    assert m[dict(name='foo', request_method='GET')] == 'registered for all'
    assert m[dict(name='foo', request_method='POST')] == 'registered for post'

# def test_duplicate_entry():
#     m = PredicateMap(['name', 'request_method'])

#     m[dict(name='foo')] = 'registered for all'
#     m[dict(name='foo')] = 'registered for all again'

#     assert m[dict(name='foo', request_method='GET')] == 'registered for all again'

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
