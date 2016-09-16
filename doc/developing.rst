Developing Reg
==============

Install Reg for development
---------------------------

.. highlight:: console

Clone Reg from github::

  $ git clone git@github.com:morepath/reg.git

If this doesn't work and you get an error 'Permission denied (publickey)',
you need to upload your ssh public key to github_.

Then go to the reg directory::

  $ cd reg

Make sure you have virtualenv_ installed.

Create a new virtualenv for Python 3 inside the reg directory::

  $ virtualenv -p python3 env/py3

Activate the virtualenv::

  $ source env/py3/bin/activate

Make sure you have recent setuptools and pip installed::

  $ pip install -U setuptools pip

Install the various dependencies and development tools from
develop_requirements.txt::

  $ pip install -Ur develop_requirements.txt

For upgrading the requirements just run the command again.

If you want to test Reg with Python 2.7 as well you can create a
second virtualenv for it::

  $ virtualenv -p python2.7 env/py27

You can then activate it::

  $ source env/py27/bin/activate

Then uprade setuptools and pip and install the develop requirements as
described above.

.. note::

   The following commands work only if you have the virtualenv activated.

.. _github: https://help.github.com/articles/generating-an-ssh-key

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

Running the tests
-----------------

You can run the tests using `py.test`_::

  $ py.test

To generate test coverage information as HTML do::

  $ py.test --cov reg --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`py.test`: http://pytest.org/latest/

Running the documentation tests
-------------------------------

The documentation contains code. To check these code snippets, you
can run this code using this command::

  (py3) $ sphinx-build -b doctest doc doc/build/doctest

Or alternatively if you have ``Make`` installed::

  (py3) $ cd doc
  (py3) $ make doctest

Or from the Reg project directory::

  (py3) $ make -C doc doctest

Since the sample code in the documentation is maintained in Python 3
syntax, we do not support running the doctests with Python 2.7.

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/build/html``), run::

  $ sphinx-build doc doc/build/html

Or alternatively if you have ``Make`` installed::

  $ cd doc
  $ make html

Or from the Reg project directory::

  $ make -C doc html

Various checking tools
----------------------

flake8_ is a tool that can do various checks for common Python
mistakes using pyflakes_, check for PEP8_ style compliance and
can do `cyclomatic complexity`_ checking. To do pyflakes and pep8
checking do::

  $ flake8 reg

To also show cyclomatic complexity, use this command::

  $ flake8 --max-complexity=10 reg

.. _flake8: https://pypi.python.org/pypi/flake8

.. _pyflakes: https://pypi.python.org/pypi/pyflakes

.. _pep8: http://www.python.org/dev/peps/pep-0008/

.. _`cyclomatic complexity`: https://en.wikipedia.org/wiki/Cyclomatic_complexity

Tox
---

With tox you can test Morepath under different Python environments.

We have Travis continuous integration installed on Morepath's github
repository and it runs the same tox tests after each checkin.

First you should install all Python versions which you want to
test. The versions which are not installed will be skipped. You should
at least install Python 3.5 which is required by flake8, coverage and
doctests and Python 2.7 for testing Morepath with Python 2.

One tool you can use to install multiple versions of Python is pyenv_.

To find out which test environments are defined for Morepath in tox.ini run::

  $ tox -l

You can run all tox tests with::

  $ tox

You can also specify a test environment to run e.g.::

  $ tox -e py35
  $ tox -e pep8
  $ tox -e docs

To run a simple performance test you can use::

  $ tox -e perf

.. _pyenv: https://github.com/yyuu/pyenv
