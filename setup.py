import setuptools 
import io
import sys
import os.path
import subprocess


# Build README.txt from README.md if not present, and if we are actually building for distribution to pypi
if not os.path.exists('README.txt') and 'sdist' in sys.argv:
    subprocess.call(['pandoc', '--to=rst', '--smart', '--output=README.txt', 'README.md'])

# But use the best README around; never fail - there are some Windows locales that seem to die on smartquotes,
# even with the explicit encoding
try:
    readme = 'README.txt' if os.path.exists('README.txt') else 'README.md'
    long_description = io.open(readme, encoding='utf-8').read()
except:
    long_description = 'Could not read README.txt'

setuptools.setup(
    name='jsonpath-rw',
    version='1.1.1',
    description='A robust and significantly extended implementation of JSONPath for Python, with a clear AST for metaprogramming.',
    author='Kenneth Knowles',
    author_email='kenn.knowles@gmail.com',
    url='https://github.com/kennknowles/python-jsonpath-rw',
    license='Apache 2.0',
    long_description=long_description,
    packages = ['jsonpath_rw'],
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
