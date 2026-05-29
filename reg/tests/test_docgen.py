from __future__ import annotations

import pydoc
import pytest
import sys
from pathlib import Path
from sphinx.application import Sphinx
from .fixtures.module import Foo, foo


def rstrip_lines(s: str) -> str:
    "Delete trailing spaces from each line in s."
    return "\n".join(line.rstrip() for line in s.splitlines())


def test_dispatch_method_class_help(capsys: pytest.CaptureFixture[str]) -> None:
    pydoc.help(Foo)
    out, err = capsys.readouterr()
    assert (
        rstrip_lines(out)
        == """\
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
 |      dictionary for instance variables{postamble}
 |
 |  __weakref__
 |      list of weak references to the object{postamble}
""".format(
            builtins=object.__module__,
            postamble=" (if defined)" if sys.version_info < (3, 11) else "",
        )
    )


def test_dispatch_method_help(capsys: pytest.CaptureFixture[str]) -> None:
    pydoc.help(Foo.bar)
    out, err = capsys.readouterr()
    assert rstrip_lines(out) == """\
Help on function bar in module reg.tests.fixtures.module:

bar(self, obj)
    Return the bar of an object.
"""


def test_dispatch_help(capsys: pytest.CaptureFixture[str]) -> None:
    pydoc.help(foo)
    out, err = capsys.readouterr()
    assert rstrip_lines(out) == """\
Help on function foo in module reg.tests.fixtures.module:

foo(obj)
    return the foo of an object.
"""


def test_autodoc(tmp_path: Path) -> None:
    root = str(tmp_path)
    (tmp_path / "conf.py").write_text("extensions = ['sphinx.ext.autodoc']\n")
    (tmp_path / "contents.rst").write_text(
        ".. automodule:: reg.tests.fixtures.module\n" "  :members:\n"
    )
    # status=None makes Sphinx completely quiet, in case you run
    # py.test with the -s switch.  For debugging you might want to
    # remove it.
    app = Sphinx(root, root, root + "/build", root, "text", status=None)
    app.build()
    assert (tmp_path / "build/contents.txt").read_text() == """\
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
