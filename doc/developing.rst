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

Create a new virtualenv inside the reg directory::

  $ python -m venv --upgrade-deps .venv

Activate the virtualenv::

  $ source .venv/bin/activate

Install the various dependencies and development tools from
develop_requirements.txt::

  (.venv) $ pip install -Ur develop_requirements.txt

For upgrading the requirements just run the command again.

.. note::

   The following commands work only if you have the virtualenv activated.

.. _github: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

Code quality checks
-------------------

Morepath uses Ruff_ for linting, import sorting, and code formatting. Run
the checks from the project directory with::

  (.venv) $ ruff check .
  (.venv) $ ruff format --check .

To apply lint fixes and format the code, run::

  (.venv) $ ruff check --fix .
  (.venv) $ ruff format .

Ruff uses the project settings in ``pyproject.toml``. The ``lint`` tox
environment runs both checks.

To run the checks automatically on staged Python files before each
commit, enable the repository's optional Git hook once in your clone::

  (.venv) $ git config core.hooksPath .githooks

The hook checks the staged contents without modifying files.
First it checks for formatting issues and then for remaining linting issues.
It looks for Ruff in ``.venv`` and after on ``PATH``.
On failure, it lists affected files and exact Ruff fix commands.
Review and stage the changes before committing again.
If needed install Ruff with::

  (.venv) $ pip install -e .[lint]

Hooks are local conveniences and can be bypassed. CI continues to run the full
project lint and formatting checks.

.. _Ruff: https://docs.astral.sh/ruff/

Running the tests
-----------------

You can run the tests using `pytest`_::

  (.venv) $ pytest

To generate test coverage information as HTML do::

  (.venv) $ pytest --cov --cov-report html

You can then point your web browser to the ``htmlcov/index.html`` file
in the project directory and click on modules to see detailed coverage
information.

.. _`pytest`: https://pytest.org

Type checking
-------------

Reg uses mypy_ and pyright_ for type checking. Run either checker
from the project directory::

  (.venv) $ mypy
  (.venv) $ pyright

Both checkers use the settings in ``pyproject.toml``.

.. _mypy: https://mypy.readthedocs.io/
.. _pyright: https://microsoft.github.io/pyright/

Running the documentation tests
-------------------------------

The documentation contains code. To check these code snippets, you
can run this code using this command::

  (.venv) $ sphinx-build -b doctest doc doc/_build/doctest

Or alternatively if you have ``Make`` installed::

  (.venv) $ cd doc
  (.venv) $ make doctest

Or from the Reg project directory::

  (.venv) $ make -C doc doctest

Building the HTML documentation
-------------------------------

To build the HTML documentation (output in ``doc/_build/html``), run::

  (.venv) $ sphinx-build doc doc/_build/html

Or alternatively if you have ``Make`` installed::

  (.venv) $ cd doc
  (.venv) $ make html

Or from the Reg project directory::

  (.venv) $ make -C doc html

Tox
---

With tox you can test Reg under different Python environments.

We have gh-actions continuous integration installed on Reg's github
repository and it runs the same tox tests after each checkin.

First you should install all Python versions which you want to
test. The versions which are not installed will be skipped. You should
at least install Python 3.14 which is required by flake8, coverage,
doctests, mypy and pyright.

One tool you can use to install multiple versions of Python is pyenv_.

To find out which test environments are defined for Reg in tox.ini run::

  (.venv) $ tox -l

You can run all tox tests with::

  (.venv) $ tox

You can also specify a test environment to run e.g.::

  (.venv) $ tox -e py311
  (.venv) $ tox -e lint
  (.venv) $ tox -e docs

To run a simple performance test you can use::

  (.venv) $ tox -e perf

.. _pyenv: https://github.com/pyenv/pyenv
