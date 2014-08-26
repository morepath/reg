import reg
from reg.registry import Registry


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


def test_classgeneric_basic():
    @reg.classgeneric
    def something(cls):
        raise NotImplementedError()

    def something_for_object(cls):
        return "Something for %s" % cls

    r = Registry()
    r.register(something, [object], something_for_object)

    assert something(DemoClass, lookup=r) == (
        "Something for <class 'reg.tests.test_classgeneric.DemoClass'>")

    assert something.component(DemoClass, lookup=r) is something_for_object
    assert list(something.all(DemoClass, lookup=r)) == [something_for_object]


def test_classgeneric_multidispatch():
    @reg.classgeneric
    def something(cls, other):
        raise NotImplementedError()

    def something_for_object_and_object(cls, other):
        return "Something, other is object: %s" % other

    def something_for_object_and_foo(cls, other):
        return "Something, other is Foo: %s" % other

    r = Registry()
    r.register(something, [object, object], something_for_object_and_object)

    r.register(something, [object, Foo], something_for_object_and_foo)

    assert something(DemoClass, Bar(), lookup=r) == (
        'Something, other is object: <instance of Bar>')
    assert something(DemoClass, Foo(), lookup=r) == (
        "Something, other is Foo: <instance of Foo>")


def test_classgeneric_keyword_arguments():
    @reg.classgeneric
    def something(cls, extra):
        raise NotImplementedError()

    def something_for_object(cls, extra):
        return "Extra: %s" % extra

    r = Registry()
    r.register(something, [object], something_for_object)

    assert something(DemoClass, lookup=r, extra='foo') == "Extra: foo"


def test_classgeneric_no_arguments():
    @reg.classgeneric
    def something():
        raise NotImplementedError()

    def something_impl():
        return "Something!"

    r = Registry()
    r.register(something, [], something_impl)

    assert something(lookup=r) == 'Something!'


def test_classgeneric_override():
    @reg.classgeneric
    def something(cls):
        raise NotImplementedError()

    def something_for_object(cls):
        return "Something for %s" % cls

    def something_for_special(cls):
        return "Special for %s" % cls

    r = Registry()
    r.register(something, [object], something_for_object)
    r.register(something, [SpecialClass], something_for_special)

    assert something(SpecialClass, lookup=r) == (
        "Special for <class 'reg.tests.test_classgeneric.SpecialClass'>")


def test_classgeneric_fallback():
    @reg.classgeneric
    def something(cls):
        return "Fallback"

    r = Registry()

    assert something(DemoClass, lookup=r) == "Fallback"
