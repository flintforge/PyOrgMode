#!/usr/bin/env python
# -*- coding: utf-8 -*-
#+Author: Phil Estival
#+Date:   2017-03-20 14:45:40

try:
    from setuptools import setup, Feature
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, Feature


classifiers = """\
Intended Audience :: Developers
Intended Audience :: Information Technology
License :: OSI Approved :: GPL v3
Development Status :: 3 - Alpha
Natural Language :: English
Programming Language :: Python :: 2.6
Programming Language :: Python :: 3
Topic :: Documentation
"""

# Version definition in hardcode
version = '0.2.0'
description = 'Org-mode implementation'
long_description = open("README.org").read()
packages = ['pyorgmode']

setup(
    name='pyorgmode',
    version=version,
    packages=packages,
    description=description,
    long_description=long_description,
    author='Johnattan BISSON, Phil ESTIVAL',
    author_email='flint@forge.systems',
    url='https://github.com/flintforge/pyorgmode',
    license='http://www.apache.org/licenses/LICENSE-2.0',
    classifiers=filter(None, classifiers.split('\n')),
    keywords=[
        "org-mode", "pyorgmode"
    ],
    zip_safe=False,
)
