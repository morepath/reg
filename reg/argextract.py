from .mapply import arginfo


class ArgDict(object):
    """Construct a dict according to the argument spec of callable.

    Given a callable, the ArgDict extractor can turn arguments to this
    callable into a dictionary, with as key the name of the argument
    and as value the value of the argument. Reg can then use this
    information to extract information for it to use for a generic
    function call.
    """
    def __init__(self, callable):
        self.callable = callable
        self.info = arginfo(callable)
        if self.info.defaults is not None:
            self.defaults_amount = len(self.info.defaults)
        else:
            self.defaults_amount = 0

    def __call__(self, *args, **kw):
        result = {}
        positional_args = []
        keyword_args = []
        for arg in self.info.args:
            if arg in kw:
                keyword_args.append(arg)
            else:
                positional_args.append(arg)
        for name, value in zip(positional_args[:len(args)], args):
            result[name] = value
        if self.info.defaults is not None:
            for name, value in zip(positional_args[len(args):],
                                   self.info.defaults):
                result[name] = value
        for name in keyword_args:
            result[name] = kw.pop(name)
        if self.info.varargs is not None:
            result[self.info.varargs] = args[len(positional_args):]
        if self.info.keywords is not None:
            result[self.info.keywords] = kw
        return result


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
            d[name] = argdict[name]
        return self.callable(**d)
