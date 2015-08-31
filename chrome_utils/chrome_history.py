#!/usr/bin/python

"""Extract information from chromium browser history."""

from __future__ import print_function

import sys
from optparse import OptionParser
import os
import stat
import re
import operator
from chrome_lib import *
import sqlite3


# allow UTF-8 encoding if stdout going to a file
import codecs, locale     
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)


op = OptionParser()
op.add_option("--after", "-A",
              action="store", type="string", dest="after_time",
              help="Restrict visit times to after AFTER_TIME.")
op.add_option("--before", "-B",
              action="store", type="string", dest="before_time",
              help="Restrict visit times to before BEFORE_TIME.")
op.add_option("--use-last",
              action="store_true", dest="use_last", default=False,
              help="Use last visit time instead of first to restrict" \
                   " times.")
op.add_option("--report-raw-times",
              action="store_true", dest="report_raw_times", default=False,
              help="Report raw times as microseconds since epoch.")
op.add_option("--order-by",
              action="store", type="string", dest="order_by",
              help="Specify sort order of results.  " \
                   "Available fields are: "+", ".join(CrHistory.FIELDS) + \
                   ". Follow a field name with a space and 'desc' "
                   "to sort in descending order (You may need to quote the"
                   " entire string for the shell).  More than one sort"
                   " field may be used by delimiting them with commas (,).")
op.add_option("--show-visit-id",
              action="store_true", dest="show_visit_id", default=False,
              help="Show the visit ID.")
op.add_option("--show-url-id",
              action="store_true", dest="show_url_id", default=False,
              help="Show the URL ID.")
op.add_option("--show-visit-time",
              action="store_true", dest="show_visit_time", default=False,
              help="Show the (first) visit time.")
op.add_option("--show-url",
              action="store_true", dest="show_url", default=False,
              help="Show the entire URL.")
op.add_option("--show-urlbase",
              action="store_true", dest="show_urlbase", default=False,
              help="Show the URL scheme, host and port number.")
op.add_option("--show-title",
              action="store_true", dest="show_title", default=False,
              help="Show the page title.")
op.add_option("--show-visit-count",
              action="store_true", dest="show_visit_count", default=False,
              help="Show the number of visits for the URL.")
op.add_option("--show-last-visit-time",
              action="store_true", dest="show_last_visit_time", default=False,
              help="Show the last visit time.")

op.disable_interspersed_args()

op.epilog = """\
Examine URL visit history for the Chromium browser.

BEFORE_TIME and AFTER_TIME are specified as decimal digit strings of
format  YYYY[MM[DD[HH[MM[SS]]]]]
"""

(opts, args) = op.parse_args()
if len(args) < 1:
    print("Path to history file not specified.", file=sys.stderr)
    sys.exit(3)

fname = args[0]
filters = []
if opts.order_by:
    orderings = opts.order_by.split(',')
else:
    orderings = ["last_visit_time desc"]

if opts.use_last:
    restrict_var = "last_visit_time"
else:
    restrict_var = "visit_time"

if opts.after_time:
    ts = CrTimeStamp.parse_tstamp(opts.after_time)
    filters.append("%s>%d" % (restrict_var, ts))
if opts.before_time:
    ts = CrTimeStamp.parse_tstamp(opts.before_time)
    filters.append("%s<%d" % (restrict_var, ts))

if not os.access(fname, os.R_OK):
    print("Cannot open file "+fname, file=sys.stderr)
    sys.exit(5)

url_scheme_netloc = re.compile("^(\S+?://[^/]*/).*$")

opts_d = opts.__dict__
show_specific_items = any([opts_d[k] for k in opts_d if k.startswith("show_")])

crh = CrHistory(fname)

try:
    visits = crh.geturl_visits(filters, orderings)
    for visit in visits:
        if show_specific_items:
            if opts.show_visit_id:
                print(visit[0], end=' ')
            if opts.show_url_id:
                print(visit[1], end=' ')
            if opts.show_visit_time:
                if opts.report_raw_times:
                    print(visit[2], end=' ')
                else:
                    print(CrTimeStamp.fmt_tstamp(visit[2]), end=' ')
            if opts.show_url:
                print(visit[4], end=' ')
            if opts.show_urlbase:
                print(url_scheme_netloc.match(visit[4]).group(1), end=' ')
            if opts.show_title:
                print(visit[5], end=' ')
            if opts.show_visit_count:
                print(visit[6], end=' ')
            if opts.show_last_visit_time:
                if opts.report_raw_times:
                    print(visit[8], end=' ')
                else:
                    print(CrTimeStamp.fmt_tstamp(visit[8]), end=' ')
            print()
        else:
            print(visit)
except sqlite3.OperationalError as e:
    print("Error (%s) accessing %s as sqlite database." % (e, fname), file=sys.stderr)
    sys.exit(6)
except OrderSpecificationError as e:
    print(e, file=sys.stderr)
    sys.exit(7)
