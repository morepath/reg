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
        t = d_to_t(self.names, key)
        for k, v in t:
            index = self.indexes[k]
            s = index.get(v)
            if s is None:
                index[v] = s = set()
            s.add(i)

    def _get_specific(self, t):
        result = None
        for k, v in t:
            index = self.indexes[k]
            s = index.get(v, set())
            if result is None:
                result = s
            else:
                result = result.intersection(s)
        assert 0 <= len(result) < 2 
        return result
            
    def __getitem__(self, key):
        t = d_to_t(self.names, key)
        for p in tuple_permutations(t):
            ids = self._get_specific(p)
            if ids:
                return self.values[ids.pop()]
        raise KeyError(key)
        
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
 
def d_to_t(names, d):
    return [(name, d.get(name, ANY_VALUE)) for name in names]

def tuple_permutations(t):
    first = t[0]
    rest = t[1:]
    k, v = first
    if not rest:
        yield (first,)
        if v is not ANY_VALUE:
            yield ((k, ANY_VALUE),)
        return
    ps = tuple_permutations(rest)
    for p in ps:
        yield (first,) + p
    ps = tuple_permutations(rest) # generator, so do this again
    if v is not ANY_VALUE:
        for p in ps:
            yield ((k, ANY_VALUE),) + p

