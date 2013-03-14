import unittest

from jsonpath_rw.parser import parse
from jsonpath_rw.jsonpath import *

class TestJsonPath(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        logging.basicConfig()

    def check_cases(self, test_cases):
        # Note that just manually building an AST would avoid this dep and isolate the tests, but that would suck a bit
        # Also, we coerce iterables, etc, into the desired target type

        for string, data, target in test_cases:
            print 'parse("%s").find(%s) =?= %s' % (string, data, target)
            result = parse(string).find(data)
            if isinstance(target, list):
                assert [r.value for r in result] == target
            else:
                assert result.value == target

    def test_fields(self):
        self.check_cases([ ('foo', {'foo': 'baz'}, ['baz']),
                           ('foo,baz', {'foo': 1, 'baz': 2}, [1, 2]),
                           ('*', {'foo': 1, 'baz': 2}, [1, 2]) ])

    def test_magic_id(self):
        self.check_cases([ 
            ('id', {'id': 'baz'}, ['baz']),
        #    ('id', {}, '@'),
        #('id', {}, '@'),
        #   ('foo.id', {'foo': {}}, ['foo']),
        #   ('foo[*].id', {'foo': {}}, 'foo[0]'),
        #   ('foo.baz.id', {'foo': {'baz': {}}}, ['foo.baz']),
        #   ('foo.id', [{'foo': {}}, {'foo': {}}], ['foo[0]', 'foo[1]']) 
        ])

    def test_index(self):
        self.check_cases([('[0]', [42], [42]),
                          ('[2]', [34, 65, 29, 59], [29])])

    def test_slice(self):
        self.check_cases([('[*]', [1, 2, 3], [1, 2, 3]),
                          ('[*]', xrange(1, 4), [1, 2, 3]),
                          ('[1:]', [1, 2, 3, 4], [2, 3, 4]),
                          ('[:2]', [1, 2, 3, 4], [1, 2])])

    def test_child(self):
        self.check_cases([('foo.baz', {'foo': {'baz': 3}}, [3]),
                          ('foo.baz', {'foo': {'baz': [3]}}, [[3]]),
                          ('foo.baz.bizzle', {'foo': {'baz': {'bizzle': 5}}}, [5])])

    def test_descendants(self):
        self.check_cases([('foo..baz', {'foo': {'baz': 1, 'bing': {'baz': 2}}}, [1, 2] )])
