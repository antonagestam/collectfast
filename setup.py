#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(
    name='Collectfast',
    description='A Faster Collectstatic',
    version='0.4.1',
    long_description=open('README.rst').read(),
    author='Anton Agestam',
    author_email='msn@antonagestam.se',
    packages=find_packages(),
    url='https://github.com/antonagestam/collectfast/',
    license='Creative Commons Attribution-ShareAlike 3.0 Unported License',
    include_package_data=True,
    install_requires=['Django>=1.8', 'python-dateutil>=2.1', 'pytz>=2014.2', ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ]
)
