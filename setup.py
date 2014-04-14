#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(
    name='Collectfast',
    description='Collectstatic on Steroids',
    version='0.2.0',
    long_description=open('README.md').read(),
    author='Anton Agestam',
    author_email='msn@antonagestam.se',
    packages=find_packages(),
    url='https://github.com/FundedByMe/collectfast/',
    license='Creative Commons Attribution-ShareAlike 3.0 Unported License',
    include_package_data=True,
    install_requires=['Django>=1.4', 'python-dateutil>=2.1', 'pytz>=2013b',],
    classifiers=['Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3']
)
