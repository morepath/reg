from __future__ import unicode_literals
from functools import update_wrapper
from .predicate import match_argname
from .compat import string_types


class dispatch_method(object):
    def __init__(self, *predicates):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        result = MethodDispatchDescriptor(self.predicates, callable)
        # XXX this isn't right as it isn't a function object
        #update_wrapper(result, callable)
        return result


class dispatch_classmethod(object):
    def __init__(self, *predicates):
        self.predicates = [self._make_predicate(predicate)
                           for predicate in predicates]

    def _make_predicate(self, predicate):
        if isinstance(predicate, string_types):
            return match_argname(predicate)
        return predicate

    def __call__(self, callable):
        result = ClassMethodDispatchDescriptor(self.predicates, callable)
        # XXX this isn't right as it isn't a function object
        #update_wrapper(result, callable)
        return result


class dispatch_method_external_predicates(object):
    def __call__(self, callable):
        return MethodDispatchDescriptor([], callable,
                                        external_predicates=True)


class MethodDispatchDescriptor(object):
    def __init__(self, predicates, callable, external_predicates=False):
        self.predicates = predicates
        self.wrapped_func = callable
        self.external_predicates = external_predicates

    def __get__(self, obj, type=None):
        d = MethodDispatch(obj, self.predicates, self.wrapped_func,
                           self.external_predicates)
        if obj is None:
            return d
        setattr(obj, self.wrapped_func.__name__, d)
        return d


class ClassMethodDispatchDescriptor(object):
    def __init__(self, predicates, callable, external_predicates=False):
        self.predicates = predicates
        self.wrapped_func = callable
        self.external_predicates = external_predicates

    def __get__(self, obj, type=None):
        d = MethodDispatch(type, self.predicates, self.wrapped_func,
                           self.external_predicates)
        if type is None:
            return d
        setattr(type, self.wrapped_func.__name__, d)
        return d


class MethodDispatch(object):
    def __init__(self, obj,
                 predicates, wrapped_func, external_predicates=False):
        self.obj = obj
        self.predicates = predicates
        self.wrapped_func = wrapped_func
        self.external_predicates = external_predicates

    # def __repr__(self):
    #     return repr(self.wrapped_func)
    def __call__(self, *args, **kw):
        return self.obj.lookup.call(self.wrapped_func, self.obj, *args, **kw)

    def component(self, *args, **kw):
        return self.obj.lookup.component(self.wrapped_func,
                                         self.obj, *args, **kw)

    def fallback(self, *args, **kw):
        return self.obj.lookup.fallback(self.wrapped_func,
                                        self.obj, *args, **kw)

    def component_key_dict(self, **kw):
        return self.obj.lookup.component_key_dict(self.wrapped_func, kw)

    def all(self, *args, **kw):
        return self.obj.lookup.all(self.wrapped_func, self.obj, *args, **kw)

    def all_key_dict(self, **kw):
        return self.obj.lookup.all_key_dict(self.wrapped_func, kw)
