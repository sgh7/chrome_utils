#!/usr/bin/env python

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


class MockProcList(object):

    class __impl(object):
        def __init__(self, *args):
            self.procs = {t[0]: apply(MockProcess, t) for t in args}
            try:
                __builtins__['real_open']
            except KeyError:
                __builtins__['real_open'] = __builtins__['open']
                __builtins__['open'] = self.open
    
    
        def listdir(self):
            return sorted([str(i) for i in self.procs.keys()] + ["acpi", "self", "sys"])
    
        def kill(self, pid, sig):
            try:
                if sig == SIGSTOP:
                    self.procs[pid].pause()
                elif sig == SIGCONT:
                    self.procs[pid].unpause()
            except KeyError:
                raise OSError, "[Errno 1] Operation not permitted"
    
        
        @staticmethod
        def open(fname, mode='r'):
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
            
            return real_open(fname)

    __instance = None
    procs = None

    def __init__(self, *args):
        if MockProcList.__instance is None:
            MockProcList.__instance = MockProcList.__impl(*args)

        #self.__instance = MockProcList.__instance
        self.__dict__['_MockProcList__instance'] = MockProcList.__instance
        MockProcList.procs = self.__instance.procs

       
 
    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)
 
    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


class ChromeThrottleTest(unittest.TestCase):
   
    def test_placeholder(self):
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()

