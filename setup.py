import os
from setuptools import setup, find_packages

long_description = (
    open('README.rst').read()
    + '\n' +
    open('CHANGES.txt').read())

tests_require = [
    'pytest >= 2.0',
    'pytest-cov'
    ]

setup(name='reg',
      version='0.4',
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
        'Development Status :: 4 - Beta'
        ],
      install_requires=[
        'setuptools',
        'repoze.lru',
        'future',
        ],
      tests_require=tests_require,
      extras_require = dict(
        test=tests_require,
        )
      )
