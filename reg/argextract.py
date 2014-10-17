from .mapply import arginfo


class ArgDict(object):
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


class ArgExtractor(object):
    def __init__(self, argnames):
        self.argnames = argnames

    def __call__(self, argdict):
        result = {}
        for argname in self.argnames:
            d[argname] = d[argname]
        return d

