import io
from setuptools import setup, find_packages

long_description = '\n'.join((
    io.open('README.rst', encoding='utf-8').read(),
    io.open('CHANGES.txt', encoding='utf-8').read()
))

tests_require = [
    'pytest >= 2.0',
    'pytest-cov',
    'pytest-remove-stale-bytecode',
    ]

setup(name='reg',
      version='0.9.3',
      description="Generic functions. Clever registries and lookups",
      long_description=long_description,
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      url='http://reg.readthedocs.io',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Development Status :: 5 - Production/Stable'
        ],
      install_requires=[
        'setuptools',
        'repoze.lru',
        ],
      tests_require=tests_require,
      extras_require=dict(
        test=tests_require,
        )
      )
