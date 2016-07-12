import reg
from reg.dispatch import methoddispatch
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


class BaseApp(object):
    def __init__(self, lookup):
        self.lookup = lookup


def test_dispatch_basic():
    class App(BaseApp):
        @methoddispatch(match_class('cls', lambda cls: cls))
        def something(self, cls):
            raise NotImplementedError()

    def something_for_object(self, cls):
        return "Something for %s" % cls

    r = Registry()
    r.register_function(App.something, something_for_object, cls=object)

    app = App(r.lookup())

    assert app.something(DemoClass) == (
        "Something for <class 'reg.tests.test_classdispatch.DemoClass'>")

    assert app.something.component(DemoClass) is something_for_object
    assert list(app.something.all(DemoClass)) == [something_for_object]


def test_classdispatch_multidispatch():
    class App(BaseApp):
        @methoddispatch(match_class('cls', lambda cls: cls), 'other')
        def something(self, cls, other):
            raise NotImplementedError()

    def something_for_object_and_object(self, cls, other):
        return "Something, other is object: %s" % other

    def something_for_object_and_foo(self, cls, other):
        return "Something, other is Foo: %s" % other

    r = Registry()
    r.register_function(
        App.something,
        something_for_object_and_object,
        cls=object, other=object)

    r.register_function(
        App.something,
        something_for_object_and_foo,
        cls=object, other=Foo)

    app = App(r.lookup())

    assert app.something(DemoClass, Bar()) == (
        'Something, other is object: <instance of Bar>')
    assert app.something(DemoClass, Foo()) == (
        "Something, other is Foo: <instance of Foo>")


def test_classdispatch_extra_arguments():
    class App(BaseApp):
        @methoddispatch(match_class('cls', lambda cls: cls))
        def something(self, cls, extra):
            raise NotImplementedError()

    def something_for_object(self, cls, extra):
        return "Extra: %s" % extra

    r = Registry()
    r.register_function(App.something, something_for_object,
                        cls=object)

    app = App(r.lookup())
    assert app.something(DemoClass, 'foo') == "Extra: foo"


def test_classdispatch_no_arguments():
    class App(BaseApp):
        @methoddispatch()
        def something(self):
            raise NotImplementedError()

    def something_impl(self):
        return "Something!"

    r = Registry()
    r.register_function(App.something, something_impl)

    app = App(r.lookup())
    assert app.something() == 'Something!'


def test_classdispatch_override():
    class App(BaseApp):
        @methoddispatch(match_class('cls', lambda cls: cls))
        def something(self, cls):
            raise NotImplementedError()

    def something_for_object(self, cls):
        return "Something for %s" % cls

    def something_for_special(self, cls):
        return "Special for %s" % cls

    r = Registry()
    r.register_function(App.something,
                        something_for_object,
                        cls=object)
    r.register_function(App.something,
                        something_for_special,
                        cls=SpecialClass)

    app = App(r.lookup())
    assert app.something(SpecialClass) == (
        "Special for <class 'reg.tests.test_classdispatch.SpecialClass'>")


def test_classdispatch_fallback():
    class App(BaseApp):
        @methoddispatch()
        def something(self, cls):
            return "Fallback"

    r = Registry()

    app = App(r.lookup())
    assert app.something(DemoClass) == "Fallback"
