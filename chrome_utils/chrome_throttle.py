#!/usr/bin/python

"""Selectively throttle chromium browser renderer processes."""

from __future__ import print_function

import sys
from optparse import OptionParser
from signal import SIGSTOP, SIGCONT
import os
import stat
import re
import operator

from chrome_lib import *

def get_chromium_renderers():
    """Return list of Chromium renderer processes.

    Each list item is a 2-tuple of:
    process_ID - integer
    status     - Linux process status character
    """

    p = re.compile("^State:\s+(.)\s+\(([^)]*)\).*$")
    r = []
    pids = [proc for proc in os.listdir("/proc") if proc[0] in "123456789"]
    # no need to test  os.stat("/proc/"+proc).st_mode & stat.S_IFDIR

    for pid in pids:
        pdir = "/proc/"+pid
        with open(pdir+"/status") as f:
            status = f.readlines()
        if status[0] != "Name:\tchromium\n":
            continue
        with open(pdir+"/cmdline") as f:
            cmdline = f.readline()
        if ("/usr/lib/chromium/chromium", "--type=renderer") == \
                tuple(cmdline.split()[:2]):
            try:
                state = p.match(status[1]).group(1)
            except AttributeError:
                continue
            r.append((int(pid), state))
    return sorted(r, key=lambda pair: pair[0])

def parse_pid(s):
    """Convert processID as string to integer.

    The string may be suffixed with a status code which
    is discarded.
    """

    try:
        pid = int(s)
    except ValueError:
        pid = int(s[:-1])
    return pid

    
if __name__ == '__main__':
    op = OptionParser()
    op.add_option("--show-all",
                  action="store_true", dest="show_all", default=False,
                  help="Show all renderer processes.")
    op.add_option("--enable",
                  action="store_true", dest="enable", default=False,
                  help="Enable the specified processes.")
    op.add_option("--disable",
                  action="store_true", dest="disable", default=False,
                  help="Disable the specified processes.")
    op.add_option("--enable-all",
                  action="store_true", dest="enable_all", default=False,
                  help="Enable all renderer processes.")
    op.add_option("--disable-all",
                  action="store_true", dest="disable_all", default=False,
                  help="Disable all renderer processes.")
    
    op.disable_interspersed_args()
    
    op.epilog = """\
    Selectively enable or disable Chromium browser process instances.
    This is done by issuing SIGSTOP and SIGCONT signals.  This program
    only runs on Linux."""
    
    (opts, args) = op.parse_args()
    arg_pids = [parse_pid(arg) for arg in args]
    
    if opts.enable == True and opts.disable == True:
        op.error("Cannot mix --disable and --enable options.")
    
    if opts.enable_all == True and opts.disable_all == True:
        op.error("Cannot mix --disable-all and --enable-all options.")
    
    pid_states = get_chromium_renderers()
    avail_pids = [ps[0] for ps in pid_states]
    if len(pid_states) == 0:
        print("No Chromium renderers found.", file=sys.stderr)
        sys.exit(4)
    
    if opts.show_all:
        print(' '.join(["%s%s" % ps for ps in pid_states]))
    
    if opts.enable or opts.disable:
        if len(arg_pids) == 0:
            print("No process IDs specified.", file=sys.stderr)
            sys.exit(5)
        if reduce(operator.or_, [pid not in avail_pids for pid in arg_pids],
                False):
            print("Some process IDs you specified are not Chromium renderers.",
                  file=sys.stderr)
            sys.exit(3)
        if opts.enable:
            sig = SIGCONT
        else:
            sig = SIGSTOP
        for pid in arg_pids:
            os.kill(pid, sig)
            
    elif opts.enable_all or opts.disable_all:
        if opts.enable_all:
            sig = SIGCONT
        else:
            sig = SIGSTOP
        for pid in avail_pids:
            os.kill(pid, sig)
