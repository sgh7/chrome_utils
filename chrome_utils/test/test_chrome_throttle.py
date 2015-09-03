#!/usr/bin/env python

"""
Mock code to support testing of chrome_throttle.
"""

import unittest
import sys
import os
from signal import SIGSTOP, SIGCONT
import io
import re

from ..chrome_throttle import get_chromium_renderers

"""
 2 /usr/lib/chromium/chromium --password-store=detect
 2 /usr/lib/chromium/chromium --type=zygote
 1 /usr/lib/chromium/chromium-sandbox /usr/lib/chromium/chromium --type=zygote
15 /usr/lib/chromium/chromium --type=renderer --lang=en-US 
"""

CMD_CR_PASSWD   = "/usr/lib/chromium/chromium --password-store=detect"
CMD_CR_ZYGOTE   = "/usr/lib/chromium/chromium --type=zygote"
CMD_CR_SANDBOX  = "/usr/lib/chromium/chromium-sandbox /usr/lib/chromium/chromium --type=zygote"
CMD_CR_RENDERER = "/usr/lib/chromium/chromium --type=renderer --lang=en-US"
CMD_BASH        = "/bin/bash"
CMD_STRACE      = "/usr/bin/strace /usr/lib/chromium/chromium"

class MockProcess(object):
    def __init__(self, pid, cmdline, status='S'):
        self.pid = pid
        self.cmdline = cmdline
        self.cmd = cmdline.split()[0].split('/')[-1]
        self.status = status

    def pause(self):
        self.status = 'T'

    def unpause(self):
        self.sleep()

    def run(self):
        self.status = 'R'

    def sleep(self):
        self.status = 'S'

    def status_file(self):
        status_str = {'S': 'sleeping', 'T': 'stopped', 'R': 'running'}[self.status]
        return "Name:\t{0}\nState:\t{1} ({2})\n".format(
                self.cmd, self.status, status_str)

class StringFile(io.BytesIO):
    pass


class MockProcListException(Exception):
    "Used to ensure only a single instance is active."

class MockProcList(object):

    @staticmethod
    def do_system_mocks():
        try:
            __builtins__['real_open']
        except KeyError:
            __builtins__['real_open'] = __builtins__['open']
            __builtins__['open'] = MockProcList.open

        try:
            os.real_listdir
        except AttributeError:
            os.real_listdir = os.listdir
            os.listdir = MockProcList.listdir

        try:
            os.real_kill
        except AttributeError:
            os.real_kill = os.kill
            os.kill = MockProcList.kill

    
    @staticmethod
    def listdir(dir_name):
        procs = MockProcList.procs
        if dir_name == "/proc":
            return sorted([str(i) for i in procs.keys()] + ["acpi", "self", "sys"])
        return os.real_listdir(dir_name)

    @staticmethod
    def kill(pid, sig):
        procs = MockProcList.procs
        try:
            if sig == SIGSTOP:
                procs[pid].pause()
            elif sig == SIGCONT:
                procs[pid].unpause()
        except KeyError:
            raise OSError, "[Errno 1] Operation not permitted"

    
    @staticmethod
    def open(fname, mode='r'):   # FIXME: there is a buffered argument
        procs = MockProcList.procs
        try:
            try:
                pid = int(re.compile("/proc/(\d+)/status").match(fname).groups(0)[0])
                return StringFile(procs[pid].status_file())
            except AttributeError:
                pass
            try:
                pid = int(re.compile("/proc/(\d+)/cmdline").match(fname).groups(0)[0])
                return StringFile(procs[pid].cmdline)
            except AttributeError:
                pass

        except KeyError:
            raise IOError, "IOError: [Errno 2] No such file or directory: '{}'".format(fname)
        
        return real_open(fname, mode)

    procs = None

    def __init__(self, *args):
        if MockProcList.procs is not None:
            raise MockProcListException, "only one instance allowed at a time"
        MockProcList.do_system_mocks()
        self.procs = {t[0]: apply(MockProcess, t) for t in args}
        MockProcList.procs = self.procs

    def reset(self):
        for k in list(self.procs):
            del self.procs[k]
        self.procs = None
        MockProcList.procs = self.procs
 

class ChromeThrottleTest(unittest.TestCase):

    def setUp(self):
        self.mpl = MockProcList(
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


    def tearDown(self):
        self.mpl.reset()
   
    def test_placeholder(self):
        self.assertEqual(1, 1)

    def test_procs_baseline(self):
        self.assertEqual(get_chromium_renderers(),
             [(4000, 'S'), (4001, 'S'), (4002, 'S'),
              (4003, 'S'), (4004, 'R'), (4005, 'S')])

    def test_procs_stop_non_renderer(self):
        os.kill(3000, SIGSTOP)
        self.assertEqual(get_chromium_renderers(),
             [(4000, 'S'), (4001, 'S'), (4002, 'S'),
              (4003, 'S'), (4004, 'R'), (4005, 'S')])

    def test_procs_stop_two_renderers(self):
        os.kill(4001, SIGSTOP)
        os.kill(4002, SIGSTOP)
        self.assertEqual(get_chromium_renderers(),
             [(4000, 'S'), (4001, 'T'), (4002, 'T'),
              (4003, 'S'), (4004, 'R'), (4005, 'S')])

    def test_procs_stop_two_renderers_and_continue_one(self):
        os.kill(4001, SIGSTOP)
        os.kill(4002, SIGSTOP)
        os.kill(4001, SIGCONT)
        self.assertEqual(get_chromium_renderers(),
             [(4000, 'S'), (4001, 'S'), (4002, 'T'),
              (4003, 'S'), (4004, 'R'), (4005, 'S')])

    def test_procs_stop_non_existent_process(self):
        self.assertRaises(OSError, os.kill, 5000, SIGSTOP)

if __name__ == '__main__':
    unittest.main()

