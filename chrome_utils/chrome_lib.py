#!/usr/bin/python

"""Extract information from chromium browser history."""

import datetime
import sqlite3

class OrderSpecificationError(Exception):
    pass

class CrHistory(object):
    """Mapping to Chromium browser history."""

    def __init__(self, fname):
        self.fname = fname
        self.conn = sqlite3.connect(fname)

    FIELDS = [
        "visits.id", "visits.url", "visit_time", "from_visit",
        "urls.url", "title", "visit_count", "last_visit_time", "hidden",
    ]

    def _vfy_orderings(self, orderings):
        """Verify that user-specified orderings are actual fields."""
        
        for o in orderings:
            oa = o.split()
            if len(oa) > 2:
                raise OrderSpecificationError("need commas between order sort fields")
            elif len(oa) == 2:
                if oa[1].lower() != "desc":
                    raise OrderSpecificationError("invalid sort order modifier "+oa[1])
            elif len(oa) == 1:
                if oa[0].lower() not in CrHistory.FIELDS:
                    raise OrderSpecificationError("unknown sort order field "+oa[0])
            else:
                raise OrderSpecificationError("empty sort order field")

    def geturl_visits(self, filters, orderings):
        cur = self.conn.cursor()
        selections = ','.join(CrHistory.FIELDS)
        stmt = "select "+selections+" from visits, urls on visits.url=urls.id"
        if filters:
            stmt += " where " + " and ".join(filters)
        if orderings:
            self._vfy_orderings(orderings)
            stmt += " order by " + ",".join(orderings)
        return cur.execute(stmt).fetchall()

def parse_int(s, default=0):
    if len(s) == 0:
        return default
    return int(s)

class CrTimeStamp(object):
    """Conversion to/from Chromium browser timestamps.

    Time is represented as a count of microseconds since an
    epoch of Jan. 1, 1601 0h UTC.
    """

    epoch = datetime.datetime(1601, 1, 1)
    
    @staticmethod
    def parse_tstamp(s):
        """Convert date/time to count of microseconds since the epoch.
    
        The date/time is a digit string of format YYYY[MM[DD[HH[MM[SS]]]]].
        """
    
        # there may be a more pythonic way of doing this...
        yyyy = parse_int(s[:4], None)
        month = parse_int(s[4:6], 1)
        dd = parse_int(s[6:8], 1)
        hh = parse_int(s[8:10])
        mm = parse_int(s[10:12])
        ss = parse_int(s[12:14])
        delta = datetime.datetime(yyyy, month, dd, hh, mm, ss) - \
                CrTimeStamp.epoch
        return delta.total_seconds() * 1000000
        
    @staticmethod
    def fmt_tstamp(ts):
        """Convert microseconds count since epoch to date/time string.
    
        This is the inverse of the parse_tstamp function.
        """
    
        t = CrTimeStamp.epoch + datetime.timedelta(microseconds=ts)
        parts = ["year", "month", "day", "hour", "minute", "second"]
        return ''.join(["%02d" % getattr(t, k) for k in parts])
    

def reduce(function, iterable, initial=None): 
    """reduce(function, iterable[, initial]) -> value

    Apply a left-associative dyadic function cumulatively
    to a iterable sequence, returning a single value.  For
    example, reduce(lambda x, y: x*y, [1, 2, 3, 4, 5, 6])
    returns 6 factorial.  The initial value, if present,
    is placed before the beginning of the results of the
    iterable in the calculation.
    """

    def op(a,b):
        return function(a, b)

    iterator = iter(iterable)
    if initial is not None:
        value = initial
    else:
        try:
            value = iterator.next()
        except StopIteration:
            raise TypeError("reduce() of empty sequence with no initial value")
    for right in iterator:
        value = op(value, right)
    return value

