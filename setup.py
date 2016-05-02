from __future__ import print_function

import os
import platform
import sys

from setuptools import setup, find_packages, Extension, Feature
from setuptools.command.build_ext import build_ext

from distutils.errors import CCompilerError
from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError


class optional_build_ext(build_ext):
    """This allows the building of C extensions to fail.
    """
    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError as e:
            self._unavailable(e)

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError, OSError) as e:
            self._unavailable(e)

    def _unavailable(self, e):
        print('*' * 80)
        print("""WARNING:

        An optional code optimization (C extension) could not be compiled.

        Optimizations for this package will not be available.""")
        print()
        print(e)
        print('*' * 80)


codeoptimization_c = os.path.join('reg', 'fastmapply.c')
codeoptimization = Feature(
    "Optional code optimizations",
    standard=True,
    ext_modules=[Extension(
        "reg.fastmapply",
        [os.path.normcase(codeoptimization_c)]
    )])

py_impl = getattr(platform, 'python_implementation', lambda: None)
is_pypy = py_impl() == 'PyPy'
is_jython = 'java' in sys.platform
is_pure = 'PURE_PYTHON' in os.environ

# Jython cannot build the C optimizations, while on PyPy they are
# anti-optimizations (the C extension compatibility layer is known-slow,
# and defeats JIT opportunities).
if is_pypy or is_jython or is_pure:
    features = {}
else:
    features = {'codeoptimization': codeoptimization}


long_description = (
    open('README.rst').read()
    + '\n' +
    open('CHANGES.txt').read())

tests_require = [
    'pytest >= 2.0',
    'pytest-cov',
    'pytest-remove-stale-bytecode',
    ]

setup(name='reg',
      version='0.9.3.dev0',
      description="Generic functions. Clever registries and lookups",
      long_description=long_description,
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      url='http://reg.readthedocs.org',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Development Status :: 5 - Production/Stable'
      ],
      install_requires=[
          'setuptools',
          'repoze.lru',
      ],
      tests_require=tests_require,
      extras_require=dict(
          test=tests_require,
      ),
      cmdclass={'build_ext': optional_build_ext},
      features=features)
