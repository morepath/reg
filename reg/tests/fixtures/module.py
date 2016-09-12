"Sample module for testing autodoc."

from reg import dispatch_method, dispatch


class Foo(object):
    "Class for foo objects."
    @dispatch_method('obj')
    def bar(self, obj):
        "Return the bar of an object."
        return "default"

    def baz(self, obj):
        "Return the baz of an object."


@dispatch('obj')
def foo(obj):
    "return the foo of an object."
    return "default"
