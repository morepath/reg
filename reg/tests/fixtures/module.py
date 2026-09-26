"Sample module for testing autodoc."

from reg import dispatch_method, dispatch


class Foo:
    "Class for foo objects."

    @dispatch_method("obj")
    def bar(self, obj):  # type: ignore[no-untyped-def]
        "Return the bar of an object."
        return "default"

    def baz(self, obj):  # type: ignore[no-untyped-def]
        "Return the baz of an object."


@dispatch("obj")
def foo(obj):  # type: ignore[no-untyped-def]
    "return the foo of an object."
    return "default"
