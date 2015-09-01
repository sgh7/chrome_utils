#!/usr/bin/env python

import unittest
import sys
import os

from ..chrome_lib import CrTimeStamp

class ChromeHistoryTest(unittest.TestCase):
   
    def test_CrTimeStamp_None(self):
        with self.assertRaises(TypeError):
            junk = CrTimeStamp.parse_tstamp(None)

    def test_CrTimeStamp_EmptyString(self):
        with self.assertRaises(TypeError):
            junk = CrTimeStamp.parse_tstamp('')

    def test_CrTimeStamp_None_Numeric_String(self):
        with self.assertRaises(ValueError):
            junk = CrTimeStamp.parse_tstamp('No way is this a date.')

    def test_CrTimeStamp_1601(self):
        self.assertEqual(CrTimeStamp.parse_tstamp("1601"), 0.0)

    def test_CrTimeStamp_diff_one_hour(self):
        self.assertEqual(
                 CrTimeStamp.parse_tstamp("1601010101") -
                 CrTimeStamp.parse_tstamp("1601010100"),
                 3600*1000000.0)

    def test_CrTimeStamp_diff_one_minute(self):
        self.assertEqual(
                 CrTimeStamp.parse_tstamp("160101010001") -
                 CrTimeStamp.parse_tstamp("160101010000"),
                 60*1000000.0)

 
    def test_CrTimeStamp_diff_one_second(self):
        self.assertEqual(
                 CrTimeStamp.parse_tstamp("16010101000001") -
                 CrTimeStamp.parse_tstamp("16010101000000"),
                 1*1000000.0)

    def test_CrTimeStamp_elide_time(self):
        self.assertEqual(
                 CrTimeStamp.parse_tstamp("1601"),
                 CrTimeStamp.parse_tstamp("16010101000000"))

    def test_CrTimeStamp_diff_one_year(self):
        self.assertEqual(
                 CrTimeStamp.parse_tstamp("2015") -
                 CrTimeStamp.parse_tstamp("2014"),
                 365*24*3600*1000000.0)



if __name__ == '__main__':
    unittest.main()

