#!/usr/bin/env python

from setuptools import setup, find_packages

version = '5'

setup(name='blueshed-micro',
      version=version,
      description="tornado realtime rpc",
      packages=find_packages('.', exclude=['tests*']),
      include_package_data=True,
      exclude_package_data={'': ['*tests/*']},
      zip_safe=False,
      install_requires=[
          'setuptools',
          'certifi>=14.5.14',
          'tornado>=4.3',
          'pika>=0.10.0',
          'SQLAlchemy>=1.0.12',
          'PyMySQL>=0.7.2',
      ],)
