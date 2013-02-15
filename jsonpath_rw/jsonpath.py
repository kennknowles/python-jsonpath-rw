import logging
import six
from itertools import *

logger = logging.getLogger(__name__)

class JSONPath(object):
    """
    The base class for JSONPath abstract syntax; those
    methods stubbed here are the interface to supported 
    JSONPath semantics.
    """

    def find(self, data):
        "All JSONPath"
        raise NotImplementedError()

    def update(self, data, val):
        "Returns `data` with the specified path replaced by `val`"
        raise NotImplementedError()

class Root(JSONPath):
    """
    The JSONPath referring to the root object. Concrete syntax is '$'.

    WARNING! Currently synonymous with '@' because this library does not
    keep track of parent pointers or any such thing.
    """

    def find(self, data):
        return [data] 

    def update(self, data, val):
        return val

    def __str__(self):
        return '$'

class This(JSONPath):
    """
    The JSONPath referring to the current datum. Concrete syntax is '@'.
    """

    def find(self, data):
        return [data]

    def update(self, data, val):
        return val

    def __str__(self):
        return '@'

class Child(JSONPath):
    """
    JSONPath that first matches the left, then the right.
    Concrete syntax is <left> '.' <right>
    """
    
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def find(self, data):
        return chain(*[self.right.find(subdata) for subdata in self.left.find(data)])

    def __eq__(self, other):
        return isinstance(other, Child) and self.left == other.left and self.right == other.right

    def __str__(self):
        return '%s.%s' % (self.left, self.right)

class Where(JSONPath):
    """
    JSONPath that first matches the left, and then
    filters for only those nodes that have
    a match on the right.

    WARNING: Subject to change. May want to have "contains"
    or some other better word for it.
    """
    
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def find(self, data):
        return [subdata for subdata in self.left.find(data) if self.right.find(data)]

    def __str__(self):
        return '%s where %s' % (self.left, self.right)

    def __eq__(self, other):
        return isinstance(other, Where) and other.left == self.left and other.right == self.right

class Descendants(JSONPath):
    """
    JSONPath that matches first the left expression then any descendant
    of it which matches the right expression.
    """
    
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def find(self, data):
        # <left> .. <right> ==> <left> . (<right> | *..<right> | [*]..<right>)
        #
        # With with a wonky caveat that since Slice() has funky coercions
        # we cannot just delegate to that equivalence or we'll hit an 
        # infinite loop. So right here we implement the coercion-free version.

        # Get all left matches into a list
        left_matches = self.left.find(data)
        if not isinstance(left_matches, list):
            left_matches = [left_matches]

        def match_recursively(data):
            right_matches = self.right.find(data)

            # Manually do the * or [*] to avoid coercion and recurse just the right-hand pattern
            if isinstance(data, list):
                recursive_matches = chain(*[match_recursively(subdata) for subdata in data])
            elif isinstance(data, dict):
                recursive_matches = chain(*[match_recursively(subdata) for subdata in data.values()])
            else:
                recursive_matches = []

            return right_matches + list(recursive_matches)
                
        # TODO: repeatable iterator instead of list?
        return list(chain(*[match_recursively(left_match) for left_match in left_matches]))
            
    def is_singular():
        return False

    def __str__(self):
        return '%s..%s' % (self.left, self.right)

    def __eq__(self, other):
        return isinstance(other, Descendants) and self.left == other.left and self.right == other.right

class Union(JSONPath):
    """
    JSONPath that returns the union of the results of each match.
    This is pretty shoddily implemented for now. The nicest semantics
    in case of mismatched bits (list vs atomic) is to put
    them all in a list, but I haven't done that yet.

    WARNING: Any appearance of this being the _concatenation_ is
    coincidence. It may even be a bug! (or laziness)
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def is_singular(self):
        return False

    def find(self, data):
        return self.left.find(data) + self.right.find(data)

class Intersect(JSONPath):
    """
    JSONPath for bits that match *both* patterns.

    This can be accomplished a couple of ways. The most
    efficient is to actually build the intersected
    AST as in building a state machine for matching the
    intersection of regular languages. The next
    idea is to build a filtered data and match against
    that.
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def is_singular(self):
        return False

    def find(self, data):
        raise NotImplementedError()

class Fields(JSONPath):
    """
    JSONPath referring to some field of the current object.
    Concrete syntax ix comma-separated field names.

    WARNING: If '*' is any of the field names, then they will
    all be returned.
    """
    
    def __init__(self, *fields):
        self.fields = fields

    def safe_get(self, val, field):
        try:
            return val.get(field)
        except AttributeError:
            return None

    def find(self, data):
        if '*' in self.fields:
            try:
                return data.values()
            except AttributeError:
                return []
        else:
            return filter(lambda x: x != None, [self.safe_get(data, field) for field in self.fields])

    def __str__(self):
        return ','.join(self.fields)

    def __eq__(self, other):
        return isinstance(other, Fields) and self.fields == other.fields


class Index(JSONPath):
    """
    JSONPath that matches indices of the current datum, or none if not large enough.
    Concrete syntax is brackets. 

    WARNING: If the datum is not long enough, it will not crash but will not match anything.
    NOTE: For the concrete syntax of `[*]`, the abstract syntax is a Slice() with no parameters (equiv to `[:]`
    """

    # TODO: multiple and/or range slices
    def __init__(self, index):
        self.index = index

    def find(self, data):
        if len(data) > self.index:
            return [data[self.index]]
        else:
            return []

    def __eq__(self, other):
        return isinstance(other, Index) and self.index == other.index

class Slice(JSONPath):
    """
    JSONPath matching a slice of an array. 

    Because of a mismatch between JSON and XML when schema-unaware,
    this always returns an iterable; if the incoming data
    was not a list, then it returns a one element list _containing_ that
    data.

    Consider these two docs, and their schema-unaware translation to JSON:
    
    <a><b>hello</b></a> ==> {"a": {"b": "hello"}}
    <a><b>hello</b><b>goodbye</b></a> ==> {"a": {"b": ["hello", "goodbye"]}}

    If there were a schema, it would be known that "b" should always be an
    array (unless the schema were wonky, but that is too much to fix here)
    so when querying with JSON if the one writing the JSON knows that it
    should be an array, they can write a slice operator and it will coerce
    a non-array value to an array.

    This may be a bit unfortunate because it would be nice to always have
    an iterator, but dictionaries and other objects may also be iterable,
    so this is the compromise.
    """
    def __init__(self, start=None, end=None, step=None):
        self.start = start
        self.end = end
        self.step = step
    
    def find(self, data):
        # Here's the hack. If it is a dictionary or some kind of constant,
        # put it in a single-element list
        if (isinstance(data, dict) or isinstance(data, six.integer_types) 
                                   or isinstance(data, six.string_types)):

            return self.find([data])

        # Some iterators do not support slicing but we can still
        # at least work for '*'
        if self.start == None and self.end == None and self.step == None:
            return data
        else:
            return data[self.start:self.end:self.step]

    def __str__(self):
        if self.start == None and self.end == None and self.step == None:
            return '[*]'
        else:
            return '[%s%s%s]' % (self.start or '', 
                                   ':%d'%self.end if self.end else '',
                                   ':%d'%self.step if self.step else '')

    def __eq__(self, other):
        return isinstance(other, Slice) and other.start == self.start and self.end == other.end and other.step == self.step
