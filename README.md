Python JSONPath Read/Write
==========================

https://github.com/kennknowles/python-jsonpath-rw

This package provides a robust implementation of JSONPath with read and
update capability as well as additional operators, described below.

This package differs from other JSONPath implementations in that it
is a full _language_ implementation, meaning the JSONPath expressions 
are first class objects, easy to analyze, transform, parse, print, 
and extend. (You can also execute them :-)


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
 - `[`_n_`]`                           | array index (may be comma-separated list)
 - `[`_start_`?:`_end_`?]`             | array slicing (note that _step_ is unimplemented only due to lack of need thus far)
 - `[*]`                               | any array index


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
