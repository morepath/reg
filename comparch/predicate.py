class AnyValue(object):
    def __repr__(self):
        return "<ANY VALUE>"

ANY_VALUE = AnyValue()

class PredicateMap(object):
    def __init__(self, names):
        self.names = names
        self.values = []
        self.indexes = {}
        for name in names:
            self.indexes[name] = {}
            
    def __setitem__(self, key, value):
        # XXX stop the same key being registered again
        i = len(self.values)
        self.values.append(value)
        for k in self.names:
            v = key.get(k, ANY_VALUE)
            index = self.indexes[k]
            s = index.get(v)
            if s is None:
                index[v] = s = set()
            s.add(i)

    def _get_specific(self, key):
        for k in self.names:
            v = key[k]
            index = self.indexes[k]
            s = index.get(v, set())
            if result is None:
                result = s
            else:
                result = result.intersection(s)
        assert 0 <= len(result) < 2 
        return result
            
    def __getitem__(self, key):
        for key_permutation in permutations(self.names, key):
            values = self._get_specific(key_permutation)
            if values:
                return values[0]
        raise KeyError(key)
        
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

def permutations(names, d):
    return _permutations(list(reversed(names)), d)

def _permutations(names, d):
    k = names[0]
    rest = names[1:]
    v = d.get(k, ANY_VALUE)
    if not rest:
        yield { k: v }
        if v is not ANY_VALUE:
            yield { k: ANY_VALUE }
        return
    for subd in _permutations(rest, d):
        subd[k] = v
        yield subd.copy()
        if v is not ANY_VALUE:
            subd[k] = ANY_VALUE
            yield subd.copy()
