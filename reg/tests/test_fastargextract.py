#import pytest
from ..argextract import NOT_FOUND
from ..fastargextract import argextract


def test_argextractor_no_args():
    def foo():
        pass

    assert argextract(foo, (), NOT_FOUND) == {}


def test_argextractor_one_arg_alone():
    def foo(a):
        pass

    assert argextract(foo, ('a',), NOT_FOUND, 1) == {'a': 1}
    assert argextract(foo, ('a',), NOT_FOUND, a=1) == {'a': 1}


def test_argextractor_two_args():
    def foo(a, b):
        pass

    assert argextract(foo, ('a', 'b'), NOT_FOUND, 1, 2) == {'a': 1, 'b': 2}
    assert argextract(foo, ('a', 'b'), NOT_FOUND, a=1, b=2) == {
        'a': 1, 'b': 2}


def test_argextractor_one_arg_default():
    def foo(a='default'):
        pass

    assert argextract(foo, ('a',), NOT_FOUND, 1) == {'a': 1}
    assert argextract(foo, ('a',), NOT_FOUND, a=1) == {'a': 1}
    assert argextract(foo, ('a',), NOT_FOUND) == {'a': 'default'}


def test_argextractor_two_args_default():
    def foo(a, b='default'):
        pass

    assert argextract(foo, ('a', 'b'), NOT_FOUND, 1, 2) == {'a': 1, 'b': 2}
    assert argextract(foo, ('a', 'b'), NOT_FOUND, a=1, b=2) == {
        'a': 1, 'b': 2}
    assert argextract(foo, ('a', 'b'), NOT_FOUND, 1) == {
        'a': 1, 'b': 'default'}
    assert argextract(foo, ('a', 'b'), NOT_FOUND, a=1) == {
        'a': 1, 'b': 'default'}


def test_argextractor_no_args_but_got_arg():
    def foo():
        pass
    # it's okay to get an argument here; it will simply not be extracted
    assert argextract(foo, (), NOT_FOUND, 1) == {}
    assert argextract(foo, (), NOT_FOUND, a=1) == {}


def test_argextractor_one_arg_but_didnt_get_it():
    def foo(a):
        pass

    assert argextract(foo, ('a',), NOT_FOUND) == {'a': NOT_FOUND}


def test_argextractor_one_arg_but_got_other_one():
    def foo(a):
        pass

    assert argextract(foo, ('a',), NOT_FOUND, b="wrong one") == {
        'a': NOT_FOUND}


def test_argextractor_explicit_args():
    def foo(a, b):
        pass

    assert argextract(foo, ('a', 'b',), NOT_FOUND, *[1, 2]) == {
        'a': 1,
        'b': 2
    }


def test_argextractor_explicit_kw():
    def foo(a, b):
        pass

    assert argextract(foo, ('a', 'b'), NOT_FOUND, **{'a': 1, 'b': 2}) == {
        'a': 1, 'b': 2}


def test_argextractor_func_takes_args():
    def foo(*args):
        pass

    assert argextract(foo, ('args',), NOT_FOUND, 1, 2) == {'args': (1, 2)}
    assert argextract(foo, ('args',), NOT_FOUND) == {'args': ()}
    assert argextract(foo, ('args',), NOT_FOUND, args=[1, 2]) == {
        'args': ()
    }


def test_argextractor_func_takes_normal_and_args():
    def foo(a, *args):
        pass

    assert argextract(foo, ('a', 'args'), NOT_FOUND, 1, 2, 3) == {
        'a': 1, 'args': (2, 3)}
    assert argextract(foo, ('a', 'args'), NOT_FOUND, 1, 2) == {
        'a': 1, 'args': (2,)}
    assert argextract(foo, ('a', 'args'), NOT_FOUND, 1) == {
        'a': 1, 'args': ()}
    # XXX this is actually not valid Python
    assert argextract(foo, ('a', 'args'), NOT_FOUND, 2, 3, a=1) == {
        'a': 1, 'args': (2, 3)}


def test_argextractor_func_takes_normal_with_default_and_args():
    def foo(a='default', *args):
        pass

    assert argextract(foo, ('a', 'args'), NOT_FOUND, 1, 2, 3) == {
        'a': 1, 'args': (2, 3)}
    assert argextract(foo, ('a', 'args'), NOT_FOUND, 1, 2) == {
        'a': 1, 'args': (2,)}
    assert argextract(foo, ('a', 'args'), NOT_FOUND, 1) == {
        'a': 1, 'args': ()}
    assert argextract(foo, ('a', 'args'), NOT_FOUND) == {
        'a': 'default', 'args': ()}


def test_argextractor_func_positional_other_name():
    def foo(*a):
        pass

    assert argextract(foo, ('a',), NOT_FOUND, 1, 2) == {
        'a': (1, 2)
    }


def test_argextractor_func_takes_kw():
    def foo(**kw):
        pass

    assert argextract(foo, ('kw',), NOT_FOUND, a=1) == {'kw': {'a': 1}}
    assert argextract(foo, ('kw',), NOT_FOUND, a=1, b=2) == {
        'kw': {'a': 1, 'b': 2}}
    assert argextract(foo, ('kw',), NOT_FOUND) == {
        'kw': {}}
    assert argextract(foo, ('kw',), 1, NOT_FOUND) == {
        'kw': {}}


def test_argextractor_func_kw_other_name():
    def foo(**k):
        pass

    assert argextract(foo, ('k',), NOT_FOUND, a=1) == {'k': {'a': 1}}
    assert argextract(foo, ('k',), NOT_FOUND, a=1, b=2) == {
        'k': {'a': 1, 'b': 2}}
    assert argextract(foo, ('k',), NOT_FOUND) == {'k': {}}
    assert argextract(foo, ('k',), NOT_FOUND, 1) == {'k': {}}


def test_argextractor_func_takes_normal_and_kw():
    def foo(a, **kw):
        pass

    assert argextract(foo, ('a', 'kw'), NOT_FOUND, 1, b=2) == {
        'a': 1, 'kw': {'b': 2}}
    assert argextract(foo, ('a', 'kw'), NOT_FOUND, a=1, b=2) == {
        'a': 1, 'kw': {'b': 2}}
    assert argextract(foo, ('a', 'kw'), NOT_FOUND) == {
        'a': NOT_FOUND, 'kw': {}}
    assert argextract(foo, ('a', 'kw'), NOT_FOUND, 1) == {'a': 1, 'kw': {}}


def test_argextractor_func_takes_args_and_kw():
    def foo(*args, **kw):
        pass

    assert argextract(foo, ('args', 'kw'), NOT_FOUND, 1, 2, b=3) == {
        'args': (1, 2), 'kw': {'b': 3}}
    assert argextract(foo, ('args', 'kw'), NOT_FOUND, args=3) == {
        'args': (), 'kw': {'args': 3}}
    assert argextract(foo, ('args', 'kw'), NOT_FOUND, 1, 2) == {
        'args': (1, 2), 'kw': {}}


# def test_argextractor_illegal_names():
#     def foo(a, b):
#         pass

#     with pytest.raises(TypeError) as e:
#         argextract(foo, ('not_there',), NOT_FOUND)
#     assert str(e.value).startswith(
#         'Argument not_there not in signature of callable: ')


# def test_argextractor_illegal_names_kw():
#     def foo(**kw):
#         pass

#     with pytest.raises(TypeError) as e:
#         ArgExtractor(foo, ['not_there'])

#     assert str(e.value).startswith(
#         'Argument not_there not in signature of callable: ')
