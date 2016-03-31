#!/usr/bin/env python

"""
distutils/setuptools install script.
"""
import os
import re
import sys

from setuptools import setup, find_packages


ROOT = os.path.dirname(__file__)
VERSION_RE = re.compile(r'''__version__ = ['"]([0-9.]+)['"]''')


requires = [
    "boto3==1.3.0"
]


def get_version():
    init = open(os.path.join(ROOT, 'apt-s3', '__init__.py')).read()
    return VERSION_RE.search(init).group(1)


setup(
    name='apt-s3',
    version=get_version(),
    description='Easily create and manage an APT repository on S3.',
    long_description=open('README.rst').read(),
    author='Jamie Cressey',
    url='https://github.com/JamieCressey/apt-s3',
    scripts=[
        "scripts/apt-s3"
    ],
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=requires,
    license="Apache License 2.0",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
)
