from ..dispatch import dispatch
from ..predicate import match_class


class DemoClass(object):
    pass


class SpecialClass(object):
    pass


class Foo(object):
    def __repr__(self):
        return "<instance of Foo>"


class Bar(object):
    def __repr__(self):
        return "<instance of Bar>"


def test_dispatch_basic():
    @dispatch(match_class('cls'))
    def something(cls):
        raise NotImplementedError()

    def something_for_object(cls):
        return "Something for %s" % cls

    something.register(something_for_object, cls=object)

    assert something(DemoClass) == (
        "Something for <class '{}.DemoClass'>".format(__name__))

    assert something.by_args(DemoClass).component is something_for_object
    assert something.by_args(DemoClass).all_matches == [something_for_object]


def test_classdispatch_multidispatch():
    @dispatch(match_class('cls'), 'other')
    def something(cls, other):
        raise NotImplementedError()

    def something_for_object_and_object(cls, other):
        return "Something, other is object: %s" % other

    def something_for_object_and_foo(cls, other):
        return "Something, other is Foo: %s" % other

    something.register(
        something_for_object_and_object,
        cls=object, other=object)

    something.register(
        something_for_object_and_foo,
        cls=object, other=Foo)

    assert something(DemoClass, Bar()) == (
        'Something, other is object: <instance of Bar>')
    assert something(DemoClass, Foo()) == (
        "Something, other is Foo: <instance of Foo>")


def test_classdispatch_extra_arguments():
    @dispatch(match_class('cls'))
    def something(cls, extra):
        raise NotImplementedError()

    def something_for_object(cls, extra):
        return "Extra: %s" % extra

    something.register(something_for_object, cls=object)

    assert something(DemoClass, 'foo') == "Extra: foo"


def test_classdispatch_no_arguments():
    @dispatch()
    def something():
        raise NotImplementedError()

    def something_impl():
        return "Something!"

    something.register(something_impl)

    assert something() == 'Something!'


def test_classdispatch_override():
    @dispatch(match_class('cls'))
    def something(cls):
        raise NotImplementedError()

    def something_for_object(cls):
        return "Something for %s" % cls

    def something_for_special(cls):
        return "Special for %s" % cls

    something.register(something_for_object,
                       cls=object)
    something.register(something_for_special,
                       cls=SpecialClass)

    assert something(SpecialClass) == (
        "Special for <class '{}.SpecialClass'>".format(__name__))


def test_classdispatch_fallback():
    @dispatch()
    def something(cls):
        return "Fallback"

    assert something(DemoClass) == "Fallback"
