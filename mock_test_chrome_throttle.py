#!/usr/bin/env python

"""Test the mock test framework for chrome_throttle."""

import sys
import os
from signal import SIGSTOP, SIGCONT

try:
    from test_chrome_throttle import *
except ImportError:
    sys.path.insert(0, '.')
    from chrome_utils.test.test_chrome_throttle import *

def head_file(mpl, fname, max_lines=3):
    try:
        #with mpl.open(fname) as fd:
        with open(fname) as fd:
            print ''.join(fd.readlines()[:max_lines])
    except Exception, e:
        print "***", str(e)

mpl = MockProcList(
      (1000, CMD_BASH, 'S'),
      (2000, CMD_STRACE, 'R'),
      (3000, CMD_CR_PASSWD, 'S'),
      (3001, CMD_CR_PASSWD, 'S'),
      (3002, CMD_CR_ZYGOTE, 'S'),
      (3003, CMD_CR_ZYGOTE, 'S'),
      (3004, CMD_CR_SANDBOX, 'S'),
      (4000, CMD_CR_RENDERER, 'S'),
      (4001, CMD_CR_RENDERER, 'S'),
      (4002, CMD_CR_RENDERER, 'S'),
      (4003, CMD_CR_RENDERER, 'S'),
      (4004, CMD_CR_RENDERER, 'R'),
      (4005, CMD_CR_RENDERER, 'S'))

print os.listdir("/proc")
print os.listdir("/")

head_file(mpl, "/etc/passwd", 1)
head_file(mpl, "/proc/1000/cmdline")
head_file(mpl, "/proc/1000/status")

print get_chromium_renderers()
os.kill(3000, SIGSTOP)
os.kill(4001, SIGSTOP)
os.kill(4002, SIGSTOP)
print get_chromium_renderers()
os.kill(4001, SIGCONT)
print get_chromium_renderers()

try:
    os.kill(5000, SIGSTOP)
except OSError, e:
    print "kill of unknown process got", e

print "Done."
