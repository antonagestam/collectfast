#!/usr/bin/env python
from distutils.core import setup

from setuptools import find_packages

import collectfast

setup(
    name="Collectfast",
    description="A Faster Collectstatic",
    version=collectfast.__version__,
    long_description=open("README.rst").read(),
    author="Anton Agestam",
    author_email="msn@antonagestam.se",
    packages=find_packages(),
    url="https://github.com/antonagestam/collectfast/",
    license="MIT License",
    include_package_data=True,
    install_requires=[
        "Django>=1.11",
        "django-storages>=1.6",
        "typing",
        "typing-extensions",
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
)
