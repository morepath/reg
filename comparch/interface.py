from abc import ABCMeta, abstractmethod, abstractproperty

class Interface(object):
    __metaclass__ = ABCMeta
    def __call__(cls, blah):
        pass

