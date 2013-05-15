#!/usr/bin/env python

from distutils.core import setup

setup(name='Collectfast',
      version='0.0.0',
      description='Custom management command that compares the MD5 sum and '
                  'etag from S3 and if the two are the same skips file copy.',
      author='Anton Agestam',
      author_email='msn@antonagestam.se',
      packages=['collectfast', 'collectfast.management',
                'collectfast.management.commands'],
)
