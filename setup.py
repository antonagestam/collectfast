#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(
    name='Collectfast',
    version='0.1.6',
    description='Custom management command that compares the MD5 sum and '
                'etag from S3 and if the two are the same skips file copy.',
    long_description=open('README.md').read(),
    author='Anton Agestam',
    author_email='msn@antonagestam.se',
    packages=find_packages(),
    url='https://github.com/FundedByMe/collectfast/',
    license='Creative Commons Attribution-ShareAlike 3.0 Unported License',
    include_package_data=True,
    install_requires=['Django<=1.4', 'python-dateutil<=2.1', 'pytz<=2013b',],
)
