# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='eco.py',
    version='0.0.1',
    description='Calculate eco benefits for urban trees',
    long_description=readme,
    author='Adam Hinz',
    author_email='hinz.adam@gmail.com',
    url='https://github.com/azavea/eco.py',
    license=license,
    include_package_data = True,
    packages=find_packages(exclude=('tests', 'docs'))
)
