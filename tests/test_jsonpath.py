from __future__ import unicode_literals, print_function, absolute_import, division, generators, nested_scopes
import unittest
import json

from jsonpath_rw import jsonpath # For setting the global auto_id_field flag

from jsonpath_rw.parser import parse
from jsonpath_rw.jsonpath import *
from jsonpath_rw.lexer import JsonPathLexerError

class TestDatumInContext(unittest.TestCase):
    """
    Tests of properties of the DatumInContext and AutoIdForDatum objects
    """
    
    @classmethod
    def setup_class(cls):
        logging.basicConfig()

    def test_DatumInContext_init(self):

        test_datum1 = DatumInContext(3)
        assert test_datum1.path == This()
        assert test_datum1.full_path == This()
        
        test_datum2 = DatumInContext(3, path=Root())
        assert test_datum2.path == Root()
        assert test_datum2.full_path == Root()

        test_datum3 = DatumInContext(3, path=Fields('foo'), context='does not matter')
        assert test_datum3.path == Fields('foo')
        assert test_datum3.full_path == Fields('foo')

        test_datum3 = DatumInContext(3, path=Fields('foo'), context=DatumInContext('does not matter', path=Fields('baz'), context='does not matter'))
        assert test_datum3.path == Fields('foo')
        assert test_datum3.full_path == Fields('baz').child(Fields('foo'))

    def test_DatumInContext_in_context(self):

        assert (DatumInContext(3).in_context(path=Fields('foo'), context=DatumInContext('whatever'))
                ==
                DatumInContext(3, path=Fields('foo'), context=DatumInContext('whatever')))

        assert (DatumInContext(3).in_context(path=Fields('foo'), context='whatever').in_context(path=Fields('baz'), context='whatever')
                ==
                DatumInContext(3).in_context(path=Fields('foo'), context=DatumInContext('whatever').in_context(path=Fields('baz'), context='whatever')))

    # def test_AutoIdForDatum_pseudopath(self):
    #     assert AutoIdForDatum(DatumInContext(value=3, path=Fields('foo')), id_field='id').pseudopath == Fields('foo')
    #     assert AutoIdForDatum(DatumInContext(value={'id': 'bizzle'}, path=Fields('foo')), id_field='id').pseudopath == Fields('bizzle')

    #     assert AutoIdForDatum(DatumInContext(value={'id': 'bizzle'}, path=Fields('foo')),
    #                           id_field='id',
    #                           context=DatumInContext(value=3, path=This())).pseudopath == Fields('bizzle')

    #     assert (AutoIdForDatum(DatumInContext(value=3, path=Fields('foo')),
    #                            id_field='id').in_context(DatumInContext(value={'id': 'bizzle'}, path=This())) 
    #             ==
    #             AutoIdForDatum(DatumInContext(value=3, path=Fields('foo')),
    #                            id_field='id',
    #                            context=DatumInContext(value={'id': 'bizzle'}, path=This())))

    #     assert (AutoIdForDatum(DatumInContext(value=3, path=Fields('foo')),
    #                            id_field='id',
    #                            context=DatumInContext(value={"id": 'bizzle'}, 
    #                                                path=Fields('maggle'))).in_context(DatumInContext(value='whatever', path=Fields('miggle')))
    #             ==
    #             AutoIdForDatum(DatumInContext(value=3, path=Fields('foo')),
    #                            id_field='id',
    #                            context=DatumInContext(value={'id': 'bizzle'}, path=Fields('miggle').child(Fields('maggle')))))

    #     assert AutoIdForDatum(DatumInContext(value=3, path=Fields('foo')),
    #                           id_field='id',
    #                           context=DatumInContext(value={'id': 'bizzle'}, path=This())).pseudopath == Fields('bizzle').child(Fields('foo'))

class TestJsonPath(unittest.TestCase):
    """
    Tests of the actual jsonpath functionality
    """
    
    @classmethod
    def setup_class(cls):
        logging.basicConfig(format = '%(levelname)s:%(funcName)s:%(message)s',
                            level = logging.DEBUG)

    #
    # Check that the data value returned is good
    #
    def check_cases(self, test_cases):
        # Note that just manually building an AST would avoid this dep and isolate the tests, but that would suck a bit
        # Also, we coerce iterables, etc, into the desired target type

        for string, data, target in test_cases:
            logging.debug('parse("%s").find(%s) =?= %s' % (string, data, target))
            result = parse(string).find(data)
            if isinstance(target, list):
                assert [r.value for r in result] == target
            elif isinstance(target, set):
                assert set([r.value for r in result]) == target
            else:
                assert result.value == target

    def test_fields_value(self):
        jsonpath.auto_id_field = None
        self.check_cases([
            ('foo', {'foo': 'baz'}, ['baz']),
            ('foo,baz', {'foo': 1, 'baz': 2}, [1, 2]),
            ('@foo', {'@foo': 1}, [1]),
            ('*', {'foo': 1, 'baz': 2}, set([1, 2]))
        ])

        jsonpath.auto_id_field = 'id'
        self.check_cases([ ('*', {'foo': 1, 'baz': 2}, set([1, 2, '`this`'])) ])

    def test_root_value(self):
        jsonpath.auto_id_field = None
        self.check_cases([ 
            ('$', {'foo': 'baz'}, [{'foo':'baz'}]),
            ('foo.$', {'foo': 'baz'}, [{'foo':'baz'}]),
            ('foo.$.foo', {'foo': 'baz'}, ['baz']),
        ])

    def test_this_value(self):
        jsonpath.auto_id_field = None
        self.check_cases([ 
            ('`this`', {'foo': 'baz'}, [{'foo':'baz'}]),
            ('foo.`this`', {'foo': 'baz'}, ['baz']),
            ('foo.`this`.baz', {'foo': {'baz': 3}}, [3]),
        ])

    def test_index_value(self):
        self.check_cases([
            ('[0]', [42], [42]),
            ('[5]', [42], []),
            ('[2]', [34, 65, 29, 59], [29]),
            ('[0]', None, [])
        ])

    def test_slice_value(self):
        self.check_cases([('[*]', [1, 2, 3], [1, 2, 3]),
                          ('[*]', xrange(1, 4), [1, 2, 3]),
                          ('[1:]', [1, 2, 3, 4], [2, 3, 4]),
                          ('[:2]', [1, 2, 3, 4], [1, 2])])

        # Funky slice hacks
        self.check_cases([
            ('[*]', 1, [1]), # This is a funky hack
            ('[0:]', 1, [1]), # This is a funky hack
            ('[*]', {'foo':1}, [{'foo': 1}]), # This is a funky hack
            ('[*].foo', {'foo':1}, [1]), # This is a funky hack
        ])

    def test_child_value(self):
        self.check_cases([('foo.baz', {'foo': {'baz': 3}}, [3]),
                          ('foo.baz', {'foo': {'baz': [3]}}, [[3]]),
                          ('foo.baz.bizzle', {'foo': {'baz': {'bizzle': 5}}}, [5])])

    def test_descendants_value(self):
        self.check_cases([ 
            ('foo..baz', {'foo': {'baz': 1, 'bing': {'baz': 2}}}, [1, 2] ),
            ('foo..baz', {'foo': [{'baz': 1}, {'baz': 2}]}, [1, 2] ), 
        ])

    def test_union_value(self):
        self.check_cases([
            ('foo | bar', {'foo': 1, 'bar': 2}, [1, 2])
        ])

    def test_parent_value(self):
        self.check_cases([('foo.baz.`parent`', {'foo': {'baz': 3}}, [{'baz': 3}]),
                          ('foo.`parent`.foo.baz.`parent`.baz.bizzle', {'foo': {'baz': {'bizzle': 5}}}, [5])])

    def test_hyphen_key(self):
        self.check_cases([('foo.bar-baz', {'foo': {'bar-baz': 3}}, [3]),
            ('foo.[bar-baz,blah-blah]', {'foo': {'bar-baz': 3, 'blah-blah':5}},
                [3,5])])
        self.assertRaises(JsonPathLexerError, self.check_cases,
                [('foo.-baz', {'foo': {'-baz': 8}}, [8])])




    #
    # Check that the paths for the data are correct.
    # FIXME: merge these tests with the above, since the inputs are the same anyhow
    #
    def check_paths(self, test_cases):
        # Note that just manually building an AST would avoid this dep and isolate the tests, but that would suck a bit
        # Also, we coerce iterables, etc, into the desired target type

        for string, data, target in test_cases:
            logging.debug('parse("%s").find(%s).paths =?= %s' % (string, data, target))
            result = parse(string).find(data)
            if isinstance(target, list):
                assert [str(r.full_path) for r in result] == target
            elif isinstance(target, set):
                assert set([str(r.full_path) for r in result]) == target
            else:
                assert str(result.path) == target

    def test_fields_paths(self):
        jsonpath.auto_id_field = None
        self.check_paths([ ('foo', {'foo': 'baz'}, ['foo']),
                           ('foo,baz', {'foo': 1, 'baz': 2}, ['foo', 'baz']),
                           ('*', {'foo': 1, 'baz': 2}, set(['foo', 'baz'])) ])

        jsonpath.auto_id_field = 'id'
        self.check_paths([ ('*', {'foo': 1, 'baz': 2}, set(['foo', 'baz', 'id'])) ])

    def test_root_paths(self):
        jsonpath.auto_id_field = None
        self.check_paths([ 
            ('$', {'foo': 'baz'}, ['$']),
            ('foo.$', {'foo': 'baz'}, ['$']),
            ('foo.$.foo', {'foo': 'baz'}, ['foo']),
        ])

    def test_this_paths(self):
        jsonpath.auto_id_field = None
        self.check_paths([ 
            ('`this`', {'foo': 'baz'}, ['`this`']),
            ('foo.`this`', {'foo': 'baz'}, ['foo']),
            ('foo.`this`.baz', {'foo': {'baz': 3}}, ['foo.baz']),
        ])

    def test_index_paths(self):
        self.check_paths([('[0]', [42], ['[0]']),
                          ('[2]', [34, 65, 29, 59], ['[2]'])])

    def test_slice_paths(self):
        self.check_paths([ ('[*]', [1, 2, 3], ['[0]', '[1]', '[2]']),
                           ('[1:]', [1, 2, 3, 4], ['[1]', '[2]', '[3]']) ])

    def test_child_paths(self):
        self.check_paths([('foo.baz', {'foo': {'baz': 3}}, ['foo.baz']),
                          ('foo.baz', {'foo': {'baz': [3]}}, ['foo.baz']),
                          ('foo.baz.bizzle', {'foo': {'baz': {'bizzle': 5}}}, ['foo.baz.bizzle'])])

    def test_descendants_paths(self):
        self.check_paths([('foo..baz', {'foo': {'baz': 1, 'bing': {'baz': 2}}}, ['foo.baz', 'foo.bing.baz'] )])


    #
    # Check the "auto_id_field" feature
    #
    def test_fields_auto_id(self):
        jsonpath.auto_id_field = "id"
        self.check_cases([ ('foo.id', {'foo': 'baz'}, ['foo']),
                           ('foo.id', {'foo': {'id': 'baz'}}, ['baz']),
                           ('foo,baz.id', {'foo': 1, 'baz': 2}, ['foo', 'baz']),
                           ('*.id', 
                            {'foo':{'id': 1},
                             'baz': 2},
                             set(['1', 'baz'])) ])

    def test_root_auto_id(self):
        jsonpath.auto_id_field = 'id'
        self.check_cases([ 
            ('$.id', {'foo': 'baz'}, ['$']), # This is a wonky case that is not that interesting
            ('foo.$.id', {'foo': 'baz', 'id': 'bizzle'}, ['bizzle']), 
            ('foo.$.baz.id', {'foo': 4, 'baz': 3}, ['baz']),
        ])

    def test_this_auto_id(self):
        jsonpath.auto_id_field = 'id'
        self.check_cases([ 
            ('id', {'foo': 'baz'}, ['`this`']), # This is, again, a wonky case that is not that interesting
            ('foo.`this`.id', {'foo': 'baz'}, ['foo']),
            ('foo.`this`.baz.id', {'foo': {'baz': 3}}, ['foo.baz']),
        ])

    def test_index_auto_id(self):
        jsonpath.auto_id_field = "id"
        self.check_cases([('[0].id', [42], ['[0]']),
                          ('[2].id', [34, 65, 29, 59], ['[2]'])])

    def test_slice_auto_id(self):
        jsonpath.auto_id_field = "id"
        self.check_cases([ ('[*].id', [1, 2, 3], ['[0]', '[1]', '[2]']),
                           ('[1:].id', [1, 2, 3, 4], ['[1]', '[2]', '[3]']) ])

    def test_child_auto_id(self):
        jsonpath.auto_id_field = "id"
        self.check_cases([('foo.baz.id', {'foo': {'baz': 3}}, ['foo.baz']),
                          ('foo.baz.id', {'foo': {'baz': [3]}}, ['foo.baz']),
                          ('foo.baz.id', {'foo': {'id': 'bizzle', 'baz': 3}}, ['bizzle.baz']),
                          ('foo.baz.id', {'foo': {'baz': {'id': 'hi'}}}, ['foo.hi']),
                          ('foo.baz.bizzle.id', {'foo': {'baz': {'bizzle': 5}}}, ['foo.baz.bizzle'])])

    def test_descendants_auto_id(self):
        jsonpath.auto_id_field = "id"
        self.check_cases([('foo..baz.id', 
                           {'foo': {
                               'baz': 1, 
                               'bing': {
                                   'baz': 2
                                }
                             } },
                             ['foo.baz', 
                              'foo.bing.baz'] )])

    def check_update_cases(self, test_cases):
        for original, expr_str, value, expected in test_cases:
            logger.debug('parse(%r).update(%r, %r) =?= %r'
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
            ('foo', '`this`', 'bar', 'bar'),
            # TODO: fixme
            # ({'foo': 'bar'}, 'foo.`this`', 'baz', {'foo': 'baz'}),
            ({'foo': {'bar': 'baz'}}, 'foo.`this`.bar', 'foo', {'foo': {'bar': 'foo'}})
        ])

    def test_update_fields(self):
        self.check_update_cases([
            ({'foo': 1}, 'foo', 5, {'foo': 5}),
            ({'foo': 1, 'bar': 2}, '$.*', 3, {'foo': 3, 'bar': 3})
        ])

    def test_update_child(self):
        self.check_update_cases([
            ({'foo': 'bar'}, '$.foo', 'baz', {'foo': 'baz'}),
            ({'foo': {'bar': 1}}, 'foo.bar', 'baz', {'foo': {'bar': 'baz'}})
        ])

    def test_update_union(self):
        self.check_update_cases([
            ({'foo': 1, 'bar': 2}, 'foo | bar', 3, {'foo': 3, 'bar': 3})
        ])

    def test_update_where(self):
        self.check_update_cases([
            ({'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}},
             '*.bar where baz', 5, {'foo': {'bar': 5}, 'bar': {'baz': 2}})
        ])

    def test_update_descendants_where(self):
        self.check_update_cases([
            ({'foo': {'bar': 1, 'flag': 1}, 'baz': {'bar': 2}},
             '(* where flag) .. bar', 3,
             {'foo': {'bar': 3, 'flag': 1}, 'baz': {'bar': 2}})
        ])

    def test_update_descendants(self):
        self.check_update_cases([
            ({'somefield': 1}, '$..somefield', 42, {'somefield': 42}),
            ({'outer': {'nestedfield': 1}}, '$..nestedfield', 42, {'outer': {'nestedfield': 42}}),
            ({'outs': {'bar': 1, 'ins': {'bar': 9}}, 'outs2': {'bar': 2}},
             '$..bar', 42,
             {'outs': {'bar': 42, 'ins': {'bar': 42}}, 'outs2': {'bar': 42}})
        ])

    def test_update_index(self):
        self.check_update_cases([
            (['foo', 'bar', 'baz'], '[0]', 'test', ['test', 'bar', 'baz'])
        ])

    def test_update_slice(self):
        self.check_update_cases([
            (['foo', 'bar', 'baz'], '[0:2]', 'test', ['test', 'test', 'baz'])
        ])

    def check_exclude_cases(self, test_cases):
        for original, string, expected in test_cases:
            logging.debug('parse("%s").exclude(%s) =?= %s' % (string, original, expected))
            actual = parse(string).exclude(original)
            assert actual == expected

    def test_exclude_fields(self):
        jsonpath.auto_id_field = None
        self.check_exclude_cases([
            ({'foo': 'baz'}, 'foo', {}),
            ({'foo': 1, 'baz': 2}, 'foo', {'baz': 2}),
            ({'foo': 1, 'baz': 2}, 'foo,baz', {}),
            ({'@foo': 1}, '@foo', {}),
            ({'@foo': 1, 'baz': 2}, '@foo', {'baz': 2}),
            ({'foo': 1, 'baz': 2}, '*', {})
        ])

    def test_exclude_root(self):
        self.check_exclude_cases([
            ('foo', '$', None),
        ])

    def test_exclude_this(self):
        self.check_exclude_cases([
            ('foo', '`this`', None),
            ({}, '`this`', None),
            ({'foo': 1}, '`this`', None),
            # TODO: fixme
            #({'foo': 1}, 'foo.`this`', {}),
            ({'foo': {'bar': 1}}, 'foo.`this`.bar', {'foo': {}}),
            ({'foo': {'bar': 1, 'baz': 2}}, 'foo.`this`.bar', {'foo': {'baz': 2}})
        ])

    def test_exclude_child(self):
        self.check_exclude_cases([
            ({'foo': 'bar'}, '$.foo', {}),
            ({'foo': 'bar'}, 'foo', {}),
            ({'foo': {'bar': 1}}, 'foo.bar', {'foo': {}}),
            ({'foo': {'bar': 1}}, 'foo.$.foo.bar', {'foo': {}})
        ])

    def test_exclude_where(self):
        self.check_exclude_cases([
            ({'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}},
             '*.bar where none', {'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}}),

            ({'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}},
             '*.bar where baz', {'foo': {}, 'bar': {'baz': 2}})
        ])

    def test_exclude_descendants(self):
        self.check_exclude_cases([
            ({'somefield': 1}, '$..somefield', {}),
            ({'outer': {'nestedfield': 1}}, '$..nestedfield', {'outer': {}}),
            ({'outs': {'bar': 1, 'ins': {'bar': 9}}, 'outs2': {'bar': 2}},
             '$..bar',
             {'outs': {'ins': {}}, 'outs2': {}})
        ])

    def test_exclude_descendants_where(self):
        self.check_exclude_cases([
            ({'foo': {'bar': 1, 'flag': 1}, 'baz': {'bar': 2}},
             '(* where flag) .. bar',
             {'foo': {'flag': 1}, 'baz': {'bar': 2}})
        ])

    def test_exclude_union(self):
        self.check_exclude_cases([
            ({'foo': 1, 'bar': 2}, 'foo | bar', {}),
            ({'foo': 1, 'bar': 2, 'baz': 3}, 'foo | bar', {'baz': 3}),
        ])

    def test_exclude_index(self):
        self.check_exclude_cases([
            ([42], '[0]', []),
            ([42], '[5]', [42]),
            ([34, 65, 29, 59], '[2]', [34, 65, 59]),
            (None, '[0]', None),
            ([], '[0]', []),
            (['foo', 'bar', 'baz'], '[0]', ['bar', 'baz']),
        ])

    def test_exclude_slice(self):
        self.check_exclude_cases([
            (['foo', 'bar', 'baz'], '[0:2]', ['baz']),
            (['foo', 'bar', 'baz'], '[0:1]', ['bar', 'baz']),
            (['foo', 'bar', 'baz'], '[0:]', []),
            (['foo', 'bar', 'baz'], '[:2]', ['baz']),
            (['foo', 'bar', 'baz'], '[:3]', [])
        ])

    def check_include_cases(self, test_cases):
        for original, string, expected in test_cases:
            logging.debug('parse("%s").include(%s) =?= %s' % (string, original, expected))
            actual = parse(string).include(original)
            assert actual == expected

    def test_include_fields(self):
        self.check_include_cases([
            ({'foo': 'baz'}, 'foo', {'foo': 'baz'}),
            ({'foo': 1, 'baz': 2}, 'foo', {'foo': 1}),
            ({'foo': 1, 'baz': 2}, 'foo,baz', {'foo': 1, 'baz': 2}),
            ({'@foo': 1}, '@foo', {'@foo': 1}),
            ({'@foo': 1, 'baz': 2}, '@foo', {'@foo': 1}),
            ({'foo': 1, 'baz': 2}, '*', {'foo': 1, 'baz': 2}),
        ])

    def test_include_index(self):
        self.check_include_cases([
            ([42], '[0]', [42]),
            ([42], '[5]', []),
            ([34, 65, 29, 59], '[2]', [29]),
            (None, '[0]', None),
            ([], '[0]', []),
            (['foo', 'bar', 'baz'], '[0]', ['foo']),
        ])

    def test_include_slice(self):
        self.check_include_cases([
            (['foo', 'bar', 'baz'], '[0:2]', ['foo', 'bar']),
            (['foo', 'bar', 'baz'], '[0:1]', ['foo']),
            (['foo', 'bar', 'baz'], '[0:]', ['foo', 'bar', 'baz']),
            (['foo', 'bar', 'baz'], '[:2]', ['foo', 'bar']),
            (['foo', 'bar', 'baz'], '[:3]', ['foo', 'bar', 'baz']),
            (['foo', 'bar', 'baz'], '[0:0]', []),
        ])

    def test_include_root(self):
        self.check_include_cases([
            ('foo', '$', 'foo'),
            ({}, '$', {}),
            ({'foo': 1}, '$', {'foo': 1})
        ])

    def test_include_this(self):
        self.check_include_cases([
            ('foo', '`this`', 'foo'),
            ({}, '`this`', {}),
            ({'foo': 1}, '`this`', {'foo': 1}),
            # TODO: fixme
            #({'foo': 1}, 'foo.`this`', {}),
            ({'foo': {'bar': 1}}, 'foo.`this`.bar', {'foo': {'bar': 1}}),
            ({'foo': {'bar': 1, 'baz': 2}}, 'foo.`this`.bar', {'foo': {'bar': 1}})
        ])

    def test_include_child(self):
        self.check_include_cases([
            ({'foo': 'bar'}, '$.foo', {'foo': 'bar'}),
            ({'foo': 'bar'}, 'foo', {'foo': 'bar'}),
            ({'foo': {'bar': 1}}, 'foo.bar', {'foo': {'bar': 1}}),
            ({'foo': {'bar': 1}}, 'foo.$.foo.bar', {'foo': {'bar': 1}}),
            ({'foo': {'bar': 1, 'baz': 2}}, 'foo.$.foo.bar', {'foo': {'bar': 1}}),
            ({'foo': {'bar': 1, 'baz': 2}}, '*', {'foo': {'bar': 1, 'baz': 2}}),
            ({'foo': {'bar': 1, 'baz': 2}}, 'non', {}),
        ])

    def test_exclude_not_exists(self):
        self.check_exclude_cases([
            (
                {
                    'foo': [
                        {'bar': 'bar'},
                        {'baz': None}
                    ]
                },
                'foo.[*].baz.not_exist_key',
                {
                    'foo': [
                        {'bar': 'bar'},
                        {'baz': None}
                    ]
                },
             ),
        ])

    """
    def test_include_where(self):
        self.check_include_cases([
            #({'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}},
            # '*.bar where none', {}),

            ({'foo': {'bar': {'baz': 1}}, 'bar': {'baz': 2}},
             '*.bar where baz', {'foo': {'bar': {'baz': 1}}})
        ])
    """

    """
    def test_include_descendants(self):
        self.check_include_cases([
            ({'somefield': 1}, '$..somefield', {'somefield': 1}),
            ({'outer': {'nestedfield': 1}}, '$..nestedfield', {'outer': {'nestedfield': 1}}),
            ({'outs': {'bar': 1, 'ins': {'bar': 9}}, 'outs2': {'bar': 2}},
             '$..bar',
             {'outs': {'bar': 1, 'ins': {'bar': 9}}, 'outs2': {'bar': 2}})
        ])
    """
