import setuptools 
import os.path
import subprocess

# Build README.txt from README.md if not present
if not os.path.exists('README.txt'):
    subprocess.call(['pandoc', '--to=rst', '--smart', '--output=README.txt', 'README.md'])

setuptools.setup(
    name='jsonpath-rw',
    version='0.2',
    description='A robust and extended implementation of JSONPath with read and update capability, and a clear AST',
    author='Kenneth Knowles',
    author_email='kenn.knowles@gmail.com',
    url='https://github.com/kennknowles/python-jsonpath-rw',
    license='Apache 2.0',
    long_description=open('README.txt').read(),
    packages = ['jsonpath_rw'],
    test_suite = 'tests',
    install_requires = [ 'ply', 'decorator', 'six' ],
)
