import pytest
from ..argextract import ArgDict, KeyExtractor


def test_argdict_no_args():
    def foo():
        pass

    d = ArgDict(foo)
    assert d() == {}


def test_argdict_one_arg():
    def foo(a):
        pass

    d = ArgDict(foo)
    assert d(1) == { 'a': 1 }
    assert d(a=1) == { 'a': 1 }


def test_argdict_two_args():
    def foo(a, b):
        pass

    d = ArgDict(foo)
    assert d(1, 2) == { 'a': 1, 'b': 2}
    assert d(a=1, b=2) == { 'a': 1, 'b': 2}


def test_argdict_one_arg_default():
    def foo(a='default'):
        pass

    d = ArgDict(foo)
    assert d(1) == { 'a': 1 }
    assert d(a=1) == { 'a': 1 }
    assert d() == { 'a': 'default' }


def test_argdict_two_args_default():
    def foo(a, b='default'):
        pass

    d = ArgDict(foo)
    assert d(1, 2) == { 'a': 1, 'b': 2 }
    assert d(a=1, b=2) == { 'a': 1, 'b': 2 }
    assert d(1) == { 'a': 1, 'b': 'default' }
    assert d(a=1) == { 'a': 1, 'b': 'default' }


def test_argdict_no_args_but_got_arg():
    def foo():
        pass

    d = ArgDict(foo)
    # it's okay to get an argument here; it will simply not be extracted
    assert d(1) == {}
    assert d(a=1) == {}


def test_argdict_one_arg_but_didnt_get_it():
    def foo(a):
        pass

    d = ArgDict(foo)
    assert d() == {}


def test_argdict_one_arg_but_got_other_one():
    def foo(a):
        pass

    d = ArgDict(foo)
    assert d(b='wrong one') == {}


def test_argdict_explicit_args():
    def foo(a, b):
        pass

    d = ArgDict(foo)
    assert d(*[1, 2]) == { 'a': 1, 'b': 2 }


def test_argdict_explicit_kw():
    def foo(a, b):
        pass

    d = ArgDict(foo)
    assert d(**{'a': 1, 'b': 2}) == { 'a': 1, 'b': 2 }


def test_argdict_func_takes_args():
    def foo(*args):
        pass

    d = ArgDict(foo)
    assert d(1, 2) == { 'args': (1, 2) }
    assert d(args=[1, 2]) == { 'args': () }


def test_argdict_func_takes_normal_and_args():
    def foo(a, *args):
        pass

    d = ArgDict(foo)
    assert d(1, 2, 3) == { 'a': 1, 'args': (2, 3) }
    assert d(1, 2) == { 'a': 1, 'args': (2,) }
    assert d(1) == { 'a': 1, 'args': () }
    assert d(2, 3, a=1) == { 'a': 1, 'args': (2, 3) }


def test_argdict_func_takes_normal_with_default_and_args():
    def foo(a='default', *args):
        pass

    d = ArgDict(foo)
    assert d(1, 2, 3) == { 'a': 1, 'args': (2, 3) }
    assert d(1, 2) == { 'a': 1, 'args': (2,) }
    assert d(1) == { 'a': 1, 'args': () }
    assert d() == { 'a': 'default', 'args': () }


def test_argdict_func_positional_other_name():
    def foo(*a):
        pass

    d = ArgDict(foo)
    assert d(1, 2) == { 'a': (1, 2) }


def test_argdict_func_takes_kw():
    def foo(**kw):
        pass

    d = ArgDict(foo)
    assert d(a=1) == { 'kw': { 'a': 1 } }
    assert d(a=1, b=2) == { 'kw': { 'a': 1, 'b': 2 } }
    assert d() == { 'kw': {} }
    assert d(1) == { 'kw': {} }


def test_argdict_func_kw_other_name():
    def foo(**k):
        pass

    d = ArgDict(foo)
    assert d(a=1) == { 'k': { 'a': 1 } }
    assert d(a=1, b=2) == { 'k': { 'a': 1, 'b': 2 } }
    assert d() == { 'k': {} }
    assert d(1) == { 'k': {} }


def test_argdict_func_takes_normal_and_kw():
    def foo(a, **kw):
        pass

    d = ArgDict(foo)
    assert d(1, b=2) == { 'a': 1, 'kw': { 'b': 2 } }
    assert d(a=1, b=2) == { 'a': 1, 'kw': { 'b': 2 } }
    assert d() == { 'kw': {} }
    assert d(1) == { 'a': 1, 'kw': {} }


def test_keyextractor():
    class Model(object):
        pass

    class Request(object):
        def __init__(self, request_method):
            self.request_method = request_method

    def get_request_method(request):
        return request.request_method

    def foo(self, request):
        pass

    k = KeyExtractor(get_request_method)

    d = ArgDict(foo)

    assert k(d(Model(), Request('GET'))) == 'GET'
    assert k(d(Model(), Request('POST'))) == 'POST'


def test_keyextractor_error():
    def illegal_function(*arg):
        pass

    def illegal_function2(*kw):
        pass

    with pytest.raises(TypeError):
        k = KeyExtractor(illegal_function)

    with pytest.raises(TypeError):
        k = KeyExtractor(illegal_function2)

