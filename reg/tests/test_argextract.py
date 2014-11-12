import pytest
from ..argextract import KeyExtractor, ArgExtractor, NOT_FOUND
from ..error import KeyExtractorError


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

    d = ArgExtractor(foo, ['self', 'request'])

    assert k(d(Model(), Request('GET'))) == 'GET'
    assert k(d(Model(), Request('POST'))) == 'POST'


def test_keyextractor_error():
    def illegal_function(*arg):
        pass

    def illegal_function2(**kw):
        pass

    with pytest.raises(TypeError):
        KeyExtractor(illegal_function)

    with pytest.raises(TypeError):
        KeyExtractor(illegal_function2)


def test_keyextractor_not_found():
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

    d = ArgExtractor(foo, ['self', 'request'])

    with pytest.raises(KeyExtractorError):
        # do not pass in request, so cannot extract the key
        k(d(Model())) == 'GET'


def test_argextractor_no_args():
    def foo():
        pass

    d = ArgExtractor(foo, [])
    assert d() == {}


def test_argextractor_one_arg():
    def foo(a):
        pass

    d = ArgExtractor(foo, ['a'])

    assert d(1) == {'a': 1}
    assert d(a=1) == {'a': 1}


def test_argextractor_two_args():
    def foo(a, b):
        pass

    d = ArgExtractor(foo, ['a', 'b'])
    assert d(1, 2) == {'a': 1, 'b': 2}
    assert d(a=1, b=2) == {'a': 1, 'b': 2}


def test_argextractor_one_arg_default():
    def foo(a='default'):
        pass

    d = ArgExtractor(foo, ['a'])
    assert d(1) == {'a': 1}
    assert d(a=1) == {'a': 1}
    assert d() == {'a': 'default'}


def test_argextractor_two_args_default():
    def foo(a, b='default'):
        pass

    d = ArgExtractor(foo, ['a', 'b'])
    assert d(1, 2) == {'a': 1, 'b': 2}
    assert d(a=1, b=2) == {'a': 1, 'b': 2}
    assert d(1) == {'a': 1, 'b': 'default'}
    assert d(a=1) == {'a': 1, 'b': 'default'}


def test_argextractor_no_args_but_got_arg():
    def foo():
        pass

    d = ArgExtractor(foo, [])
    # it's okay to get an argument here; it will simply not be extracted
    assert d(1) == {}
    assert d(a=1) == {}


def test_argextractor_one_arg_but_didnt_get_it():
    def foo(a):
        pass

    d = ArgExtractor(foo, ['a'])
    assert d() == {'a': NOT_FOUND}


def test_argextractor_one_arg_but_got_other_one():
    def foo(a):
        pass

    d = ArgExtractor(foo, ['a'])
    assert d(b='wrong one') == {'a': NOT_FOUND}


def test_argextractor_explicit_args():
    def foo(a, b):
        pass

    d = ArgExtractor(foo, ['a', 'b'])
    assert d(*[1, 2]) == {'a': 1, 'b': 2}


def test_argextractor_explicit_kw():
    def foo(a, b):
        pass

    d = ArgExtractor(foo, ['a', 'b'])
    assert d(**{'a': 1, 'b': 2}) == {'a': 1, 'b': 2}


def test_argextractor_func_takes_args():
    def foo(*args):
        pass

    d = ArgExtractor(foo, ['args'])
    assert d(1, 2) == {'args': (1, 2)}
    assert d() == {'args': ()}
    assert d(args=[1, 2]) == {'args': ()}


def test_argextractor_func_takes_normal_and_args():
    def foo(a, *args):
        pass

    d = ArgExtractor(foo, ['a', 'args'])
    assert d(1, 2, 3) == {'a': 1, 'args': (2, 3)}
    assert d(1, 2) == {'a': 1, 'args': (2,)}
    assert d(1) == {'a': 1, 'args': ()}
    # XXX this is actually not valid Python
    assert d(2, 3, a=1) == {'a': 1, 'args': (2, 3)}


def test_argextractor_func_takes_normal_with_default_and_args():
    def foo(a='default', *args):
        pass

    d = ArgExtractor(foo, ['a', 'args'])
    assert d(1, 2, 3) == {'a': 1, 'args': (2, 3)}
    assert d(1, 2) == {'a': 1, 'args': (2,)}
    assert d(1) == {'a': 1, 'args': ()}
    assert d() == {'a': 'default', 'args': ()}


def test_argextractor_func_positional_other_name():
    def foo(*a):
        pass

    d = ArgExtractor(foo, ['a'])
    assert d(1, 2) == {'a': (1, 2)}


def test_argextractor_func_takes_kw():
    def foo(**kw):
        pass

    d = ArgExtractor(foo, ['kw'])
    assert d(a=1) == {'kw': {'a': 1}}
    assert d(a=1, b=2) == {'kw': {'a': 1, 'b': 2}}
    assert d() == {'kw': {}}
    assert d(1) == {'kw': {}}


def test_argextractor_func_kw_other_name():
    def foo(**k):
        pass

    d = ArgExtractor(foo, ['k'])
    assert d(a=1) == {'k': {'a': 1}}
    assert d(a=1, b=2) == {'k': {'a': 1, 'b': 2}}
    assert d() == {'k': {}}
    assert d(1) == {'k': {}}


def test_argextractor_func_takes_normal_and_kw():
    def foo(a, **kw):
        pass

    d = ArgExtractor(foo, ['a', 'kw'])
    assert d(1, b=2) == {'a': 1, 'kw': {'b': 2}}
    assert d(a=1, b=2) == {'a': 1, 'kw': {'b': 2}}
    assert d() == {'a': NOT_FOUND, 'kw': {}}
    assert d(1) == {'a': 1, 'kw': {}}


def test_argextractor_func_takes_args_and_kw():
    def foo(*args, **kw):
        pass

    d = ArgExtractor(foo, ['args', 'kw'])
    assert d(1, 2, b=3) == {'args': (1, 2), 'kw': {'b': 3}}
    assert d(args=3) == {'args': (), 'kw': {'args': 3}}
    assert d(1, 2) == {'args': (1, 2), 'kw': {}}


def test_argextractor_illegal_names():
    def foo(a, b):
        pass

    with pytest.raises(TypeError) as e:
        ArgExtractor(foo, ['not_there'])
    assert str(e.value).startswith(
        'Argument not_there not in signature of callable: ')


def test_argextractor_illegal_names_kw():
    def foo(**kw):
        pass

    with pytest.raises(TypeError) as e:
        ArgExtractor(foo, ['not_there'])

    assert str(e.value).startswith(
        'Argument not_there not in signature of callable: ')
