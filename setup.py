import setuptools 
import io
import sys
import os.path
import subprocess

setuptools.setup(
    name='jsonpath-rw',
    version='1.3.0',
    description='A robust and significantly extended implementation of JSONPath for Python, with a clear AST for metaprogramming.',
    author='Kenneth Knowles',
    author_email='kenn.knowles@gmail.com',
    url='https://github.com/kennknowles/python-jsonpath-rw',
    license='Apache 2.0',
    long_description=io.open('README.rst', encoding='utf-8').read(),
    packages = ['jsonpath_rw'],
    entry_points = {
        'console_scripts':  ['jsonpath.py = jsonpath_rw.bin.jsonpath:entry_point'],
    },
    test_suite = 'tests',
    install_requires = [ 'ply', 'decorator', 'six' ],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)
