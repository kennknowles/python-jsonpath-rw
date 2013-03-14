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
        """
        All `JSONPath` types support `find()`, which returns an iterable of `DatumAtPath`s.
        They keep track of the path followed to the current location, so if the calling code
        has some opinion about that, it can be passed in here as a starting point.
        """
        raise NotImplementedError()

    def update(self, data, val):
        "Returns `data` with the specified path replaced by `val`"
        raise NotImplementedError()

class DatumAtPath(object):
    """
    Represents a single datum along with the path followed to locate it.

    For quick-and-dirty work, this proxies any non-special attributes
    to the underlying datum, but the actual datum can (and usually should)
    be retrieved via the `value` attribute.

    To place `datum` within a path, use `datum.in_context(path)`, which prepends
    `path` to that already stored.
    """
    def __init__(self, value, path):
        self.value = value
        self.path = path

    def __getattr__(self, attr):
        if attr == 'id' and not hasattr(self.value, 'id'):
            return str(self.path)
        else:
            return getattr(self.value, attr)

    def __str__(self):
        return str(self.value)

    def in_context(self, context_path):
        return DatumAtPath(self.value, path=self.path if isinstance(context_path, This) else Child(context_path, self.path))

class Root(JSONPath):
    """
    The JSONPath referring to the root object. Concrete syntax is '$'.

    WARNING! Currently synonymous with '@' because this library does not
    keep track of parent pointers or any such thing.
    """

    def find(self, data):
        return [DatumAtPath(data, path=Root())]

    def update(self, data, val):
        return val

    def __str__(self):
        return '$'

class This(JSONPath):
    """
    The JSONPath referring to the current datum. Concrete syntax is '@'.
    """

    def find(self, data):
        return [DatumAtPath(data, path=This())]

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
        return [submatch.in_context(subdata.path)
                for subdata in self.left.find(data)
                for submatch in self.right.find(subdata.value)]

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
                recursive_matches = [submatch.in_context(Index(i))
                                     for submatch in match_recursively(data[i])
                                     for i in xrange(0, len(data))]

            elif isinstance(data, dict):
                recursive_matches = [submatch.in_context(Fields(field))
                                     for field in data.keys()
                                     for submatch in match_recursively(data[field])]

            else:
                recursive_matches = []

            return right_matches + list(recursive_matches)
                
        # TODO: repeatable iterator instead of list?
        return [submatch.in_context(left_match.path)
                for left_match in left_matches
                for submatch in match_recursively(left_match.value)]
            
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
                return [DatumAtPath(data[field], path=Fields(field)) for field in data.keys()]
            except AttributeError:
                return []
        else:
            result = [DatumAtPath(val, path=Fields(field))
                      for field, val in [(field, self.safe_get(data, field)) for field in self.fields]
                      if val is not None]

            return result

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

    def __init__(self, index):
        self.index = index

    def find(self, data):
        if len(data) > self.index:
            return [DatumAtPath(data[self.index], path=self)]
        else:
            return []

    def __eq__(self, other):
        return isinstance(other, Index) and self.index == other.index

    def __str__(self):
        return '[%i]' % self.index

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
            return [DatumAtPath(data[i], Index(i)) for i in xrange(0, len(data))]
        else:
            return [DatumAtPath(data[i], Index(i)) for i in range(0, len(data))[self.start:self.end:self.step]]

    def __str__(self):
        if self.start == None and self.end == None and self.step == None:
            return '[*]'
        else:
            return '[%s%s%s]' % (self.start or '', 
                                   ':%d'%self.end if self.end else '',
                                   ':%d'%self.step if self.step else '')

    def __eq__(self, other):
        return isinstance(other, Slice) and other.start == self.start and self.end == other.end and other.step == self.step
