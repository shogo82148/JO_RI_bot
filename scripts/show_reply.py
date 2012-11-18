#!/usr/bin/env python

import anydbm
db = anydbm.open('reply.db')

items = [(int(value), key) for key, value in db.iteritems() if '\n' in key]
items.sort(reverse=True)

for value, key in items:
    print '\t'.join(key.split('\n')), '\t', value

