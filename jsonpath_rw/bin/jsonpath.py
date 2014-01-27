#!/usr/bin/python
# encoding: utf-8
# Copyright © 2012 Felix Richter <wtfpl@syntax-fehler.de>
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See the COPYING file for more details.

from jsonpath_rw import parse
import json
import sys
import glob
if len(sys.argv) < 2:
    print("""usage: %s jsonpath [files]
path can be:
    atomics:
        $              - root object
        `this`         - current object

    operators:
        path1.path2    - same as xpath /
        path1|path2    - union
        path1..path2   - somewhere in between

    fiels:
        fieldname       - field with name
        *               - any field
        [_start_?:_end_?] - array slice
        [*]             - any array index
""")
    sys.exit(1)

expr = parse(sys.argv[1])

def find_matches_for_file(f):
    return [unicode(match.value) for match in expr.find(json.load(f))]

def print_matches(matches):
    print(u"\n".join(matches).encode("utf-8"))

if len(sys.argv) < 3:
    # stdin mode
    print_matches(find_matches_for_file(sys.stdin))
else:
    # file paths mode
    for pattern in sys.argv[2:]:
        for filename in glob.glob(pattern):
            with open(filename) as f:
                print_matches(find_matches_for_file(f))

