# -*- coding: utf-8 -*-
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:

    def iteritems(d, **kw):
        return iter(d.items(**kw))

    xrange = range
    basestring = str
    unicode = str
    long = int
else:

    def iteritems(d, **kw):
        return d.iteritems(**kw)

    xrange = xrange
    basestring = basestring
    unicode = unicode
    long = long
