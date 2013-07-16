from comparch.predicate import PredicateMap, permutations, ANY_VALUE

def test_predicatemap():
    m = PredicateMap(['name', 'request_method'])
    m[dict(name='foo')] = 'registered for all'
    m[dict(name='foo', request_method='POST')] = 'registered for post'

    assert m[dict(name='foo', request_method='GET')] == 'registered for all'
    assert m[dict(name='foo', request_method='POST')] == 'registered for post'
    
def test_permutations():
    d = { 'a': 'A', 'b': 'B' }
    assert list(permutations(['a', 'b'], d)) == [
        { 'a': 'A', 'b': 'B' },
        { 'a': 'A', 'b': ANY_VALUE },
        { 'a': ANY_VALUE, 'b': 'B'},
        { 'a': ANY_VALUE, 'b': ANY_VALUE}]
    assert list(permutations(['a', 'b', 'c'], d)) == [
        { 'a': 'A', 'b': 'B', 'c': ANY_VALUE },
        { 'a': 'A', 'b': ANY_VALUE, 'c': ANY_VALUE },
        { 'a': ANY_VALUE, 'b': 'B', 'c': ANY_VALUE},
        { 'a': ANY_VALUE, 'b': ANY_VALUE, 'c': ANY_VALUE}
        ]
