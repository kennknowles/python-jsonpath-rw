from __future__ import unicode_literals, print_function, absolute_import, division, generators, nested_scopes
import unittest

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
        logging.basicConfig()

    #
    # Check that the data value returned is good
    #
    def check_cases(self, test_cases):
        # Note that just manually building an AST would avoid this dep and isolate the tests, but that would suck a bit
        # Also, we coerce iterables, etc, into the desired target type

        for string, data, target in test_cases:
            print('parse("%s").find(%s) =?= %s' % (string, data, target))
            result = parse(string).find(data)
            if isinstance(target, list):
                assert [r.value for r in result] == target
            elif isinstance(target, set):
                assert set([r.value for r in result]) == target
            else:
                assert result.value == target

    def test_fields_value(self):
        jsonpath.auto_id_field = None
        self.check_cases([ ('foo', {'foo': 'baz'}, ['baz']),
                           ('foo,baz', {'foo': 1, 'baz': 2}, [1, 2]),
                           ('@foo', {'@foo': 1}, [1]),
                           ('*', {'foo': 1, 'baz': 2}, set([1, 2])) ])

        jsonpath.auto_id_field = 'id'
        self.check_cases([ ('*', {'foo': 1, 'baz': 2}, set([1, 2, '`this`'])) ])

    def test_sort_value(self):
        jsonpath.auto_id_field = None
        self.check_cases([
            ('objects[/cow]', {'objects': [{'cat': 1, 'cow': 2}, {'cat': 2, 'cow': 1}, {'cat': 3, 'cow': 3}]},
             [{'cat': 2, 'cow': 1}, {'cat': 1, 'cow': 2}, {'cat': 3, 'cow': 3}]),
            ('objects[\cat]', {'objects': [{'cat': 2}, {'cat': 1}, {'cat': 3}]},
             [{'cat': 3}, {'cat': 2}, {'cat': 1}]),
            ('objects[/cow,\cat]', {'objects': [{'cat': 1, 'cow': 2}, {'cat': 2, 'cow': 1}, {'cat': 3, 'cow': 1}, {'cat': 3, 'cow': 3}]},
             [{'cat': 3, 'cow': 1}, {'cat': 2, 'cow': 1}, {'cat': 1, 'cow': 2}, {'cat': 3, 'cow': 3}]),
            ('objects[\cow , /cat]', {'objects': [{'cat': 1, 'cow': 2}, {'cat': 2, 'cow': 1}, {'cat': 3, 'cow': 1}, {'cat': 3, 'cow': 3}]},
             [{'cat': 3, 'cow': 3}, {'cat': 1, 'cow': 2}, {'cat': 2, 'cow': 1}, {'cat': 3, 'cow': 1}]),
            ('objects[/cat.cow]', {'objects': [{'cat': {'dog': 1, 'cow': 2}}, {'cat': {'dog': 2, 'cow': 1}}, {'cat': {'dog': 3, 'cow': 3}}]},
             [{'cat': {'dog': 2, 'cow': 1}}, {'cat': {'dog': 1, 'cow': 2}}, {'cat': {'dog': 3, 'cow': 3}}]),
            ('objects[/cat.(cow,bow)]', {'objects': [{'cat': {'dog': 1, 'bow': 3}}, {'cat': {'dog': 2, 'cow': 1}}, {'cat': {'dog': 2, 'bow': 2}}, {'cat': {'dog': 3, 'cow': 2}}]},
             [{'cat': {'dog': 2, 'cow': 1}}, {'cat': {'dog': 2, 'bow': 2}}, {'cat': {'dog': 3, 'cow': 2}}, {'cat': {'dog': 1, 'bow': 3}}]),
        ])

    def test_filter_value(self):
        jsonpath.auto_id_field = None
        self.check_cases([
            ('objects[?cow]', {'objects': [{'cow': 'moo'}, {'cat': 'neigh'}]}, [{'cow': 'moo'}]),
            ('objects[?@.cow]', {'objects': [{'cow': 'moo'}, {'cat': 'neigh'}]}, [{'cow': 'moo'}]),
            ('objects[?(@.cow)]', {'objects': [{'cow': 'moo'}, {'cat': 'neigh'}]}, [{'cow': 'moo'}]),
            ('objects[?(@."cow!?cat")]', {'objects': [{'cow!?cat': 'moo'}, {'cat': 'neigh'}]}, [{'cow!?cat': 'moo'}]),
            ('objects[?cow="moo"]', {'objects': [{'cow': 'moo'}, {'cow': 'neigh'}, {'cat': 'neigh'}]}, [{'cow': 'moo'}]),
            ('objects[?(@.["cow"]="moo")]', {'objects': [{'cow': 'moo'}, {'cow': 'neigh'}, {'cat': 'neigh'}]}, [{'cow': 'moo'}]),
            ('objects[?cow=="moo"]', {'objects': [{'cow': 'moo'}, {'cow': 'neigh'}, {'cat': 'neigh'}]}, [{'cow': 'moo'}]),
            ('objects[?cow>5]', {'objects': [{'cow': 8}, {'cow': 7}, {'cow': 5}, {'cow': 'neigh'}]}, [{'cow': 8}, {'cow': 7}]),
            ('objects[?cow>5&cat=2]', {'objects': [{'cow': 8, 'cat': 2}, {'cow': 7, 'cat': 2}, {'cow': 2, 'cat': 2}, {'cow': 5, 'cat': 3}, {'cow': 8, 'cat': 3}]}, [{'cow': 8, 'cat': 2}, {'cow': 7, 'cat': 2}]),
        ])

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
            ('[2]', [34, 65, 29, 59], [29])
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
            print('parse("%s").find(%s).paths =?= %s' % (string, data, target))
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
