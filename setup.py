#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'pydomus',
    version = '0.1',
    description = 'Unofficial interface to LifeDomus',
    author = 'Philippe Biondi',
    author_email = 'phil@secdev.org',
    packages = [
        'pydomus',
        'pydomus.api',
        'pydomus.cli',
    ],
    scripts = [ 'bin/pydomus' ],
    install_requires=[
          "zeep",
          "typer[all]",
      ],
)
