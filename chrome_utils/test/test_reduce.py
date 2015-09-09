#!/usr/bin/env python

import unittest
import sys
import os

import operator

from ..chrome_lib import reduce

class ReduceTest(unittest.TestCase):
    """test re-implementation of reduce()

    Guido deprecated reduce() in Python 3.
    """

    def test_reduce_empty_none(self):
        with self.assertRaises(TypeError):
            junk = reduce(lambda x,y: x+y, [], None)
   
    def test_reduce_empty_default(self):
        with self.assertRaises(TypeError):
            junk = reduce(lambda x,y: x+y, [])

    def test_reduce_add_1_to_5(self):
        self.assertEqual(reduce(lambda x,y: x+y, [1, 2, 3, 4, 5]), 15)

    def test_reduce_add_2_to_5_default_1(self):
        self.assertEqual(reduce(lambda x,y: x+y, [2, 3, 4, 5], 1), 15)

    def test_reduce_xor_0_to_255(self):
        """each bit position should be a 1 128 times"""
        self.assertEqual(reduce(operator.xor, range(256)), 0)
   


if __name__ == '__main__':
    unittest.main()

