import reg
from reg.registry import Registry
from reg.predicate import match_class


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
    @reg.dispatch(match_class('cls', lambda cls: cls))
    def something(cls):
        raise NotImplementedError()

    def something_for_object(cls):
        return "Something for %s" % cls

    r = Registry()
    r.register_function(something, something_for_object, cls=object)

    l = r.lookup()
    assert something(DemoClass, lookup=l) == (
        "Something for <class 'reg.tests.test_classdispatch.DemoClass'>")

    assert something.component(DemoClass, lookup=l) is something_for_object
    assert list(something.all(DemoClass, lookup=l)) == [something_for_object]


def test_classdispatch_multidispatch():
    @reg.dispatch(match_class('cls', lambda cls: cls), 'other')
    def something(cls, other):
        raise NotImplementedError()

    def something_for_object_and_object(cls, other):
        return "Something, other is object: %s" % other

    def something_for_object_and_foo(cls, other):
        return "Something, other is Foo: %s" % other

    r = Registry()
    r.register_function(
        something,
        something_for_object_and_object,
        cls=object, other=object)

    r.register_function(
        something,
        something_for_object_and_foo,
        cls=object, other=Foo)

    l = r.lookup()
    assert something(DemoClass, Bar(), lookup=l) == (
        'Something, other is object: <instance of Bar>')
    assert something(DemoClass, Foo(), lookup=l) == (
        "Something, other is Foo: <instance of Foo>")


def test_classdispatch_extra_arguments():
    @reg.dispatch(match_class('cls', lambda cls: cls))
    def something(cls, extra):
        raise NotImplementedError()

    def something_for_object(cls, extra):
        return "Extra: %s" % extra

    r = Registry()
    r.register_function(something, something_for_object,
                        cls=object)

    assert something(DemoClass, 'foo', lookup=r.lookup()) == "Extra: foo"


def test_classdispatch_no_arguments():
    @reg.dispatch()
    def something():
        raise NotImplementedError()

    def something_impl():
        return "Something!"

    r = Registry()
    r.register_function(something, something_impl)

    assert something(lookup=r.lookup()) == 'Something!'


def test_classdispatch_override():
    @reg.dispatch(match_class('cls', lambda cls: cls))
    def something(cls):
        raise NotImplementedError()

    def something_for_object(cls):
        return "Something for %s" % cls

    def something_for_special(cls):
        return "Special for %s" % cls

    r = Registry()
    r.register_function(something,
                        something_for_object,
                        cls=object)
    r.register_function(something,
                        something_for_special,
                        cls=SpecialClass)

    assert something(SpecialClass, lookup=r.lookup()) == (
        "Special for <class 'reg.tests.test_classdispatch.SpecialClass'>")


def test_classdispatch_fallback():
    @reg.dispatch()
    def something(cls):
        return "Fallback"

    r = Registry()

    assert something(DemoClass, lookup=r.lookup()) == "Fallback"
