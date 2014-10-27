from .arginfo import arginfo
from .sentinel import NOT_FOUND
from .error import KeyExtractorError


class ArgExtractor(object):
    """Extract arguments for a callable and desired args.

    Given a callable and a sequence of desired argument names the ArgExtractor
    can extract these from the actual arguments given to a callable. The
    result is a dictionary mapping from argument name to argument value.
    """

    def __init__(self, callable, names):
        self.callable = callable
        self.info = arginfo(callable)
        # XXX check whether names are valid according to info
        self.names, self.varargs, self.keywords = self.initialize_names(names)
        self.defaults = self.initialize_defaults()
        self.index = self.initialize_index()

    def initialize_names(self, names):
        varargs = None
        keywords = None
        new_names = []
        for name in names:
            if name == self.info.varargs:
                varargs = name
            elif name == self.info.keywords:
                keywords = name
            else:
                if name not in self.info.args:
                    raise TypeError(
                        "Argument %s not in signature of callable: %r" % (
                            name, self.callable))
                new_names.append(name)
        return new_names, varargs, keywords

    def initialize_defaults(self):
        result = {}
        args = self.info.args
        defaults = self.info.defaults
        if self.info.defaults is not None:
            default_amount = len(defaults)
        else:
            default_amount = 0
            defaults = ()
        for arg in args[:-default_amount]:
            result[arg] = NOT_FOUND
        for arg, default in zip(args[-default_amount:], defaults):
            result[arg] = default
        return result

    def initialize_index(self):
        result = {}
        for i, arg in enumerate(self.info.args):
            result[arg] = i
        return result

    def __call__(self, *args, **kw):
        result = {}
        last_pos = -1
        for name in self.names:
            value, pos = self.extract_arg(name, args, kw)
            result[name] = value
            if value is not NOT_FOUND and pos > last_pos:
                last_pos = pos
        if self.keywords is not None:
            keywords = kw.copy()
            for name in result.keys():
                keywords.pop(name, None)
            result[self.keywords] = keywords
        if self.varargs is not None:
            result[self.varargs] = args[last_pos + 1:]
        return result

    def extract_arg(self, name, args, kw):
        i = self.index.get(name)
        if i is None:
            return NOT_FOUND, None
        result = kw.get(name, NOT_FOUND)
        if result is not NOT_FOUND:
            return result, -1
        elif i < len(args):
            return args[i], i
        else:
            return self.defaults.get(name, NOT_FOUND), i


class KeyExtractor(object):
    """Extract those arguments from argdict that callable wants and call it.
    """
    def __init__(self, callable):
        self.callable = callable
        self.info = arginfo(callable)
        if self.info.varargs is not None:
            raise TypeError("KeyExtractor does not support *args")
        if self.info.keywords is not None:
            raise TypeError("KeyExtractor does not support **kw")
        self.names = self.info.args

    def __call__(self, argdict):
        d = {}
        for name in self.names:
            d[name] = value = argdict[name]
            if value is NOT_FOUND:
                raise KeyExtractorError(name)
        return self.callable(**d)


class ClassKeyExtractor(KeyExtractor):
    def __call__(self, argdict):
        return super(ClassKeyExtractor, self).__call__(argdict).__class__


class NameKeyExtractor(object):
    def __init__(self, name):
        self.name = name
        self.names = set([name])

    def __call__(self, argdict):
        value = argdict[self.name]
        if value is NOT_FOUND:
            raise KeyExtractorError(self.name)
        return value.__class__
