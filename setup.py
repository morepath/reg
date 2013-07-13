import os
from setuptools import setup, find_packages

setup(name='comparch',
      version = '0.1dev',
      description="Component Architecture Foundations",
      author="Martijn Faassen",
      author_email="faassen@startifact.com",
      license="BSD",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools'
        ],
      extras_require = dict(
        test=['pytest >= 2.0'],
        ),
      )
