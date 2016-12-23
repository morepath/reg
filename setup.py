import io
from setuptools import setup, find_packages

long_description = '\n'.join((
    io.open('README.rst', encoding='utf-8').read(),
    io.open('CHANGES.txt', encoding='utf-8').read()
))

setup(
    name='reg',
    version='0.11',
    description="Clever dispatch",
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
    extras_require=dict(
        test=[
            'pytest >= 2.9.0',
            'sphinx',
            'pytest-remove-stale-bytecode',
        ],
        pep8=[
            'flake8',
        ],
        coverage=[
            'pytest-cov',
        ],
        docs=[
            'sphinx',
        ],
    ),
)
