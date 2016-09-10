from .arginfo import arginfo


class KeyExtractor(object):
    """Call callable with relevant arguments.

    Automatically calls callable with the relevant arguments in argdict,
    based on the arguments it expects. The callable should transform
    these arguments into a value that it returns.
    """
    def __init__(self, callable):
        self.callable = callable
        self.names = arginfo(callable).args

    def __call__(self, argdict):
        """Extract relevant arguments from argdict and call callable with it.
        """
        return self.callable(**{name: argdict[name] for name in self.names})


class ClassKeyExtractor(KeyExtractor):
    """Get class of value returned by callable.
    """
    def __call__(self, argdict):
        return super(ClassKeyExtractor, self).__call__(argdict).__class__
