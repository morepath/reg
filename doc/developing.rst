Developing Reg
==============

Install Reg for development
---------------------------

First make sure you have virtualenv_ installed for Python 3.5.

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

Now create a new virtualenv somewhere for Reg's development::

  $ virtualenv /path/to/ve_reg

The goal of this is to isolate you from any globally installed
versions of setuptools, which may be incompatible with the
requirements of the buildout tool. You should also be able to recycle
an existing virtualenv, but this method guarantees a clean one.

Clone Reg from github (https://github.com/morepath/reg) and go to the
reg directory::

  $ git clone git@github.com:morepath/reg.git
  $ cd reg

Now we need to run bootstrap.py to set up buildout, using the Python from the
virtualenv we've created before::

  $ /path/to/ve_reg/bin/python bootstrap.py

This installs buildout, which can now set up the rest of the development
environment::

  $ bin/buildout

This will download and install various dependencies and tools.

Running the tests
-----------------

You can run the tests using `py.test`_. Buildout will have installed
it for you in the ``bin`` subdirectory of your project::

  $ bin/py.test reg

To generate test coverage information as HTML do::

  $ bin/py.test --cov reg --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`py.test`: http://pytest.org/latest/

Running the documentation tests
-------------------------------

The documentation contains code. To check these code snippets, you
can run this code using this command::

  $ bin/sphinxpython bin/sphinx-build  -b doctest doc out

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/build/html``), run::

  $ bin/sphinxbuilder

Various checking tools
----------------------

The buildout will also have installed flake8_, which is a tool that
can do various checks for common Python mistakes using pyflakes_,
check for PEP8_ style compliance and can do `cyclomatic complexity`_
checking. To do pyflakes and pep8 checking do::

  $ bin/flake8 reg

.. _flake8: https://pypi.python.org/pypi/flake8

.. _pyflakes: https://pypi.python.org/pypi/pyflakes

.. _pep8: http://www.python.org/dev/peps/pep-0008/

.. _`cyclomatic complexity`: https://en.wikipedia.org/wiki/Cyclomatic_complexity

To also show cyclomatic complexity, use this command::

  $ bin/flake8 --max-complexity=10 reg
