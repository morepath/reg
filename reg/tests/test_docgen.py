import pydoc
from sphinx.application import Sphinx
from .fixtures.module import Foo, foo


def rstrip_lines(s):
    "Delete trailing spaces from each line in s."
    return '\n'.join(l.rstrip() for l in s.splitlines())


def test_dispatch_method_class_help(capsys):
    pydoc.help(Foo)
    out, err = capsys.readouterr()
    assert rstrip_lines(out) == """\
Help on class Foo in module reg.tests.fixtures.module:

class Foo({builtins}.object)
 |  Class for foo objects.
 |
 |  Methods defined here:
 |
 |  bar(self, obj)
 |      Return the bar of an object.
 |
 |  baz(self, obj)
 |      Return the baz of an object.
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors defined here:
 |
 |  __dict__
 |      dictionary for instance variables (if defined)
 |
 |  __weakref__
 |      list of weak references to the object (if defined)
""".format(builtins=object.__module__)


def test_dispatch_method_help(capsys):
    pydoc.help(Foo.bar)
    out, err = capsys.readouterr()
    assert rstrip_lines(out) == """\
Help on function bar in module reg.tests.fixtures.module:

bar(self, obj)
    Return the bar of an object.
"""


def test_dispatch_help(capsys):
    pydoc.help(foo)
    out, err = capsys.readouterr()
    assert rstrip_lines(out) == """\
Help on function foo in module reg.tests.fixtures.module:

foo(obj)
    return the foo of an object.
"""


def test_autodoc(tmpdir):
    root = str(tmpdir)
    tmpdir.join('conf.py').write("extensions = ['sphinx.ext.autodoc']\n")
    tmpdir.join('contents.rst').write(
        ".. automodule:: reg.tests.fixtures.module\n"
        "  :members:\n")
    # status=None makes Sphinx completely quiet, in case you run
    # py.test with the -s switch.  For debugging you might want to
    # remove it.
    app = Sphinx(root, root, root, root, 'text', status=None)
    app.build()
    assert tmpdir.join('contents.txt').read() == """\
Sample module for testing autodoc.

class reg.tests.fixtures.module.Foo

   Class for foo objects.

   bar(obj)

      Return the bar of an object.

   baz(obj)

      Return the baz of an object.

reg.tests.fixtures.module.foo(obj)

   return the foo of an object.
"""
