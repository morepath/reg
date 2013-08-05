"""Data structure that allows look up of components that match predicates.
"""

class AnyValue(object):
    def __repr__(self):
        return "<ANY VALUE>"

ANY_VALUE = AnyValue()

# XXX API isn't right yet; redefine in terms of the tuple instead of dict
class PredicateRegistry(object):
    def __init__(self, names):
        self.names = names
        self.key_to_value_id = {}
        self.values = {}
        self.counter = 0
        self.indexes = {}
        for name in names:
            self.indexes[name] = {}
            
    def register(self, key, value):        
        t = d_to_t(self.names, key)

        # make new value id
        value_id = self.counter
        self.values[value_id] = value
        self.counter += 1

        # get previous value id, if it is there
        old_value_id = self.key_to_value_id.get(t)
        if old_value_id is not None:
            del self.values[old_value_id]
    
        # record new value id
        self.key_to_value_id[t] = value_id
        
        for k, v in t:
            index = self.indexes[k]
            s = index.get(v)
            if s is None:
                index[v] = s = set()
            s.add(value_id)
            # old value id needs to be cleaned up
            if old_value_id is not None:
                s.discard(old_value_id)

    def _get_specific(self, t):
        result = None
        for k, v in t:
            index = self.indexes[k]
            s = index.get(v, set())
            if result is None:
                result = s
            else:
                result = result.intersection(s)
            if not result:
                return result
        assert 0 <= len(result) < 2 
        return result
            
    def get(self, key, default=None):
        t = d_to_t(self.names, key)
        for p in tuple_permutations(t):
            ids = self._get_specific(p)
            if ids:
                return self.values[ids.pop()]
        return default

def d_to_t(names, d):
    return tuple([(name, d.get(name, ANY_VALUE)) for name in names])

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
