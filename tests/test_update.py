from __future__ import unicode_literals, print_function, absolute_import, division, generators, nested_scopes

import unittest
import logging

from jsonpath_rw.parser import parse


class TestUpdate(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        logging.basicConfig()

    def check_update_cases(self, test_cases):
        for original, expr_str, value, expected in test_cases:
            print('parse(%r).update(%r, %r) =?= %r'
                  % (expr_str, original, value, expected))
            expr = parse(expr_str)
            actual = expr.update(original, value)
            assert actual == expected

    def test_update_root(self):
        self.check_update_cases([
            ('foo', '$', 'bar', 'bar')
        ])

    def test_update_this(self):
        self.check_update_cases([
            ('foo', '`this`', 'bar', 'bar')
        ])

    def test_update_fields(self):
        self.check_update_cases([
            ({'foo': 1}, 'foo', 5, {'foo': 5}),
            ({}, 'foo', 1, {'foo': 1}),
            ({'foo': 1, 'bar': 2}, '$.*', 3, {'foo': 3, 'bar': 3})
        ])

    def test_update_child(self):
        self.check_update_cases([
            ({'foo': 'bar'}, '$.foo', 'baz', {'foo': 'baz'}),
            ({'foo': {'bar': 1}}, 'foo.bar', 'baz', {'foo': {'bar': 'baz'}})
        ])

    def test_update_where(self):
        self.check_update_cases([
            ({'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}},
             '*.bar where baz', 5, {'foo': {'bar': 5}, 'bar': {'baz': 2}})
        ])

    def test_update_descendants(self):
        self.check_update_cases([
            ({'foo': {'bar': 1, 'flag': 1}, 'baz': {'bar': 2}},
             '* where flag .. bar', 3,
             {'foo': {'bar': 3, 'flag': 1}, 'baz': {'bar': 2}})
        ])

    def test_update_index(self):
        self.check_update_cases([
            (['foo', 'bar', 'baz'], '[0]', 'test', ['test', 'bar', 'baz'])
        ])

    def test_update_slice(self):
        self.check_update_cases([
            (['foo', 'bar', 'baz'], '[0:2]', 'test', ['test', 'test', 'baz'])
        ])
