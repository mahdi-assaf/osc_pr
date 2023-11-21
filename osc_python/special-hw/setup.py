#!/usr/bin/python3

from codecs import open
from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='drivers',
    version='0.1',
    description='controller for open optical line system',
    long_description=long_description,
    long_description_content_type='text/x-rst; charset=UTF-8',
    author='PLANET team',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Telecommunications Industry',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='optics network fiber communication route planning optimization',
    #packages=find_packages(exclude=['examples', 'tests']),  # Required
    packages=find_packages(exclude=['tests']),  # Required
    install_requires=list(open('requirements.txt'))
)
