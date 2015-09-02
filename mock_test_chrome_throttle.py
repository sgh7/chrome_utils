#!/usr/bin/env python

"""Test the mock test framework."""

import sys
import os

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

def my_listdir(path):
    return mpl.listdir()

print mpl.listdir()

head_file(mpl, "/etc/passwd", 1)
head_file(mpl, "/proc/1000/cmdline")
head_file(mpl, "/proc/1000/status")

os.real_listdir = os.listdir
os.listdir = my_listdir
print get_chromium_renderers()

print "Done."
