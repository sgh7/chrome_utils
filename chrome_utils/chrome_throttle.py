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
from procfs import Proc
import time

from chrome_lib import *

JIFFIES_PER_SECOND = 100.0

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

"""
As of Linux 2.6.30-rc7  /proc/<PID>/stat  shows:
  pid           process id
  tcomm         filename of the executable
  state         state (R is running, S is sleeping, D is sleeping in an
                uninterruptible wait, Z is zombie, T is traced or stopped)
  ppid          process id of the parent process
  pgrp          pgrp of the process
  sid           session id
  tty_nr        tty the process uses
  tty_pgrp      pgrp of the tty
  flags         task flags
  min_flt       number of minor faults
  cmin_flt      number of minor faults with child's
  maj_flt       number of major faults
  cmaj_flt      number of major faults with child's
  utime         user mode jiffies
  stime         kernel mode jiffies
  cutime        user mode jiffies with child's
  cstime        kernel mode jiffies with child's
  priority      priority level
  nice          nice level
  num_threads   number of threads
  it_real_value (obsolete, always 0)
  start_time    time the process started after system boot
  vsize         virtual memory size
  rss           resident set memory size
  rsslim        current limit in bytes on the rss
  start_code    address above which program text can run
  end_code      address below which program text can run
  start_stack   address of the start of the stack
  esp           current value of ESP
  eip           current value of EIP
  pending       bitmap of pending signals
  blocked       bitmap of blocked signals
  sigign        bitmap of ignored signals
  sigcatch      bitmap of catched signals
  wchan         address where process went to sleep
  0             (place holder)
  0             (place holder)
  exit_signal   signal to send to parent thread on exit
  task_cpu      which CPU the task is scheduled on
  rt_priority   realtime priority
  policy        scheduling policy (man sched_setscheduler)
  blkio_ticks   time spent waiting for block IO
  gtime         guest time of the task in jiffies
  cgtime        guest time of the task children in jiffies
"""

def cpu_usage(pid):
    with open("/proc/%d/stat" % pid) as fd:
        # want user mode jiffies  and  kernel mode jiffies
        flds = [int(s) for s in fd.readline().split()[13:15]] 
    return flds[0]+flds[1]
    
def find_cpu_piggies(procs, time_window, threshold):
    proc = Proc()
    before_usage = [cpu_usage(pid) for pid in procs]
    time.sleep(time_window)
    # FIXME: what if processes have come and gone?
    after_usage = [cpu_usage(pid) for pid in procs]
    deltas = [after_usage[i]-before_usage[i] for i in range(len(procs))]
    divisor = JIFFIES_PER_SECOND * time_window
    deltas = [delta/divisor for delta in deltas]

    def int_diff(a, b):
        # comparison function with requisite resolution
        return int((a[0]-b[0])*divisor)

    def sort_key(a):
        return a[0]

    total_use = 0
    for d in deltas:
        total_use += d   # Python3 deprecated apply()
    ta = zip(deltas, procs)
    #ta_sorted = sorted(ta, int_diff, reverse=True)
    ta_sorted = sorted(ta, key=sort_key, reverse=True)
    return [ta for ta in ta_sorted if ta[0] >= threshold]

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
    op.add_option("--find-cpu-hogs",
                  action="store_true", dest="find_cpu_hogs", default=False,
                  help="Find heaviest CPU-using renderer processes.")
    op.add_option("--disable-cpu-hogs",
                  action="store_true", dest="disable_cpu_hogs", default=False,
                  help="Disable heaviest CPU-using renderer processes.")
    op.add_option("--time-window",
                  action="store", dest="time_window", type="float", default=1.0,
                  help="Number of seconds to sample CPU use of renderer processes.")
    op.add_option("--threshold",
                  action="store", dest="threshold", type="float", default=0.05,
                  help="Threshold for determining CPU \"piggyness\" of renderer processes.")

    
    op.disable_interspersed_args()
    
    op.epilog = """\
    Selectively enable or disable Chromium browser process instances.
    This is done by issuing SIGSTOP and SIGCONT signals.  This program
    only runs on Linux.

    The determination of "piggyness" is by sampling the CPU "jiffies"
    before and after a wait of "time_window" which defaults to one second.
    The threshold is the fraction of one CPU core equivalent and defaults
    to 0.05.
"""
    
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

    elif opts.find_cpu_hogs:
        print(find_cpu_piggies(avail_pids, opts.time_window, opts.threshold))

    elif opts.disable_cpu_hogs:
        # list of (piggyness, processID)
        piggies = find_cpu_piggies(avail_pids, opts.time_window, opts.threshold)
        for piggy in piggies:
            os.kill(piggy[1], SIGSTOP)

