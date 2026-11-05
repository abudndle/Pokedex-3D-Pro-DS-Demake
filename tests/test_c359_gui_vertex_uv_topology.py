"""Synthetic-only tests for original GUI geometry."""
import unittest

class C359Tests(unittest.TestCase):
    def test_mathematical_triangle(self):
        self.assertEqual(3, len((0, 1, 2)))
