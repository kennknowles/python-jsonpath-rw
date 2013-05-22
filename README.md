Python JSONPath RW
==================

https://github.com/kennknowles/python-jsonpath-rw

[![Build Status](https://travis-ci.org/kennknowles/python-jsonpath-rw.png?branch=master)](https://travis-ci.org/kennknowles/python-jsonpath-rw)
[![Test coverage](https://coveralls.io/repos/kennknowles/python-jsonpath-rw/badge.png?branch=master)](https://coveralls.io/r/kennknowles/python-jsonpath-rw)
[![PyPi version](https://pypip.in/v/jsonpath-rw/badge.png)](https://pypi.python.org/pypi/jsonpath-rw)
[![PyPi downloads](https://pypip.in/d/jsonpath-rw/badge.png)](https://pypi.python.org/pypi/jsonpath-rw)

This library provides a robust and significantly extended implementation of JSONPath for Python.
It is tested with Python 2.6, 2.7, 3.2, and 3.3.

This library differs from other JSONPath implementations in that it
is a full _language_ implementation, meaning the JSONPath expressions 
are first class objects, easy to analyze, transform, parse, print, 
and extend. (You can also execute them :-)

Quick Start
-----------

To install, use pip:

```
$ pip install jsonpath-rw
```

Then:

```python
$ python

>>> from jsonpath_rw import jsonpath, parse

# A robust parser, not just a regex. (Makes powerful extensions possible; see below)
>>> jsonpath_expr = parse('foo[*].baz')

# Extracting values is easy
>>> [match.value for match in jsonpath_expr.find({'foo': [{'baz': 1}, {'baz': 2}]})]
[1, 2]

# Matches remember where they came from
>>> [str(match.full_path) for match in jsonpath_expr.find({'foo': [{'baz': 1}, {'baz': 2}]})]
['foo.[0].baz', 'foo.[1].baz']

# And this can be useful for automatically providing ids for bits of data that do not have them (currently a global switch)
>>> jsonpath.auto_id_field = 'id'
>>> [match.value for match in parse('foo[*].id').find({'foo': [{'id': 'bizzle'}, {'baz': 3}]})]
['foo.bizzle', 'foo.[1]']

# You can also build expressions directly quite easily 
>>> jsonpath_expr_direct = Fields('foo').child(Slice('*')).child(Fields('baz'))  # This is equivalent
```


JSONPath Syntax
---------------

The JSONPath syntax supported by this library includes some additional
features and omits some problematic features (those that make it unportable).
In particular, some new operators such as `|` and `where` are available, and parentheses
are used for grouping not for callbacks into Python, since with these changes
the language is not trivially associative. Also, fields may be quoted whether or 
not they are contained in brackets.

Atomic expressions:

Syntax                        | Meaning
------------------------------|-------------------
`$`                           | The root object
`` `this` ``                  | The "current" object.
`` `foo` ``                   | More generally, this syntax allows "named operators" to extend JSONPath is arbitrary ways
_field_                       | Specified field(s), described below
`[` _field_ `]`               | Same as _field_
`[` _idx_ `]`                 | Array access, described below (this is always unambiguous with field access)

Jsonpath operators:

Syntax                                 | Meaning
---------------------------------------|---------------------------------------------------------------------
_jsonpath1_ `.` _jsonpath2_            | All nodes matched by _jsonpath2_ starting at any node matching _jsonpath1_
_jsonpath_ `[` _whatever_ `]`          | Same as _jsonpath_`.`_whatever_
_jsonpath1_ `..`	 _jsonpath2_       | All nodes matched by _jsonpath2_ that descend from any node matching _jsonpath1_
_jsonpath1_ `where` _jsonpath2_        | Any nodes matching _jsonpath1_ with a child matching _jsonpath2_

Also _jsonpath1_ `|` _jsonpath2_ for union (but I have not convinced Github-Flavored Markdown to allow
me to put that in a table)

Field specifiers ( _field_ ):

Syntax                      | Meaning
----------------------------|----------------------------------------
`fieldname`                 | the field `fieldname` (from the "current" object)
`"fieldname"`               | same as above, for allowing special characters in the fieldname
`'fieldname'`               | ditto
`*`	                        | any field
_field_ `,` _field_         | either of the named fields (you can always build equivalent jsonpath using `|`)

Array specifiers ( _idx_ ):

Syntax                                 | Meaning
---------------------------------------|----------------------------------------
 `[`_n_`]`                             | array index (may be comma-separated list)
 `[`_start_`?:`_end_`?]`               | array slicing (note that _step_ is unimplemented only due to lack of need thus far)
 `[*]`                                 | any array index


Programmatic JSONPath
---------------------

If you are programming in Python and would like a more robust way to create JSONPath
expressions that does not depend on a parser, it is very easy to do so directly, 
and here are some examples:

 - `Root()`
 - `Slice(start=0, end=None, step=None)`
 - `Fields('foo', 'bar')`
 - `Index(42)`
 - `Child(Fields('foo'), Index(42))`
 - `Where(Slice(), Fields('subfield'))`
 - `Descendants(jsonpath, jsonpath)`


Extensions
----------

 - _Path data_: The result of `JsonPath.find` provide detailed context and path
   data so it is easy to traverse to parent objects, print full paths to pieces
   of data, and generate automatic ids.
 - _Automatic Ids_: If you set `jsonpath_rw.auto_id_field` to a value other than 
   None, then for any piece of data missing that field, it will be replaced by 
   the JSONPath to it, giving automatic unique ids to any piece of data. These ids will
   take into account any ids already present as well.
 - _Named operators_: Instead of using `@` to reference the currently object, this library
   uses `` `this` ``. In general, any string contained in backquotes can be made to be
   a new operator, currently by extending the library.


More to explore
---------------

There are way too many jsonpath implementations out there to discuss.
Some are robust, some are toy projects that still work fine, some are 
exercises. There will undoubtedly be many more. This one is made
for use in released, maintained code, and in particular for
programmatic access to the abstract syntax and extension. But 
JSONPath at its simplest just isn't that complicated, so
you can probably use any of them successfully. Why not this one?

The original proposal, as far as I know:

 * [JSONPath - XPath for JSON](http://goessner.net/articles/JSONPath/) by Stefan Goessner.


Contributors
------------

 * [Kenn Knowles](https://github.com/kennknowles) ([@kennknowles](https://twitter.com/KennKnowles))


Copyright and License
---------------------

Copyright 2013- Kenneth Knowles

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
