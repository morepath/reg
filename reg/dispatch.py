from __future__ import unicode_literals
from .predicate import match_argname
from .compat import string_types
from .reify import reify


class dispatch_method(object):
    def __init__(self, *predicates):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        return MethodDispatchDescriptor(self.predicates, callable)


class dispatch_classmethod(object):
    def __init__(self, *predicates):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        return ClassMethodDispatchDescriptor(self.predicates, callable)


class dispatch_method_external_predicates(object):
    def __call__(self, callable):
        return MethodDispatchDescriptor([], callable,
                                        external_predicates=True)


cached_method_dispatch = {}


class MethodDispatchDescriptor(object):
    def __init__(self, predicates, callable, external_predicates=False):
        self.predicates = predicates
        self.wrapped_func = callable
        self.external_predicates = external_predicates

    def __get__(self, obj, type=None):
        if obj is None:
            d = cached_method_dispatch.get((type, self.wrapped_func))
            if d is not None:
                return d
        d = MethodDispatch(obj, type, self.predicates, self.wrapped_func,
                           self.external_predicates)
        if obj is None:
            cached_method_dispatch[(type, self.wrapped_func)] = d
            return d
        setattr(obj, self.wrapped_func.__name__, d)
        return d


class ClassMethodDispatchDescriptor(object):
    def __init__(self, predicates, callable, external_predicates=False):
        self.predicates = predicates
        self.wrapped_func = callable
        self.external_predicates = external_predicates

    def __get__(self, obj, type=None):
        d = MethodDispatch(type, None, self.predicates, self.wrapped_func,
                           self.external_predicates)
        if type is None:
            return d
        setattr(type, self.wrapped_func.__name__, d)
        return d


class MethodDispatch(object):
    def __init__(self, obj, type,
                 predicates, wrapped_func, external_predicates=False):
        self.obj = obj
        self.type = type
        self.predicates = predicates
        self.wrapped_func = wrapped_func
        self.external_predicates = external_predicates

    @reify
    def lookup(self):
        if self.obj is None:
            raise TypeError("no lookup available for dispatch")
        return self.obj.lookup

    def __repr__(self):
        if self.obj is None:
            # Python 3 style
            return '<dispatch function %s.%s at 0x%02x>' % (
                self.type.__name__, self.wrapped_func.__name__,
                id(self.wrapped_func))
        if self.obj is not None:
            obj = self.obj
            name = obj.__class__.__name__
        else:
            name = type.__name__
            obj = type
        return '<bound dispatch method %s.%s of %r>' % (
            name,
            self.wrapped_func.__name__,
            obj)

    def __call__(self, *args, **kw):
        return self.lookup.call(self.wrapped_func, self.obj, *args, **kw)

    def component(self, *args, **kw):
        return self.lookup.component(self.wrapped_func,
                                     self.obj, *args, **kw)

    def fallback(self, *args, **kw):
        return self.lookup.fallback(self.wrapped_func,
                                    self.obj, *args, **kw)

    def component_key_dict(self, **kw):
        return self.lookup.component_key_dict(self.wrapped_func, kw)

    def all(self, *args, **kw):
        return self.lookup.all(self.wrapped_func, self.obj, *args, **kw)

    def all_key_dict(self, **kw):
        return self.lookup.all_key_dict(self.wrapped_func, kw)
