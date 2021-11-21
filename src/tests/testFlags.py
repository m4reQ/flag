import flag
import unittest

class TestIntFlag(unittest.TestCase):
    _flag = flag.IntFlag('test_int_flag', 2137, '')

    def test_default_value(self):
        self.assertEqual(self._flag.default, 2137)
    
    def test_is_default(self):
        self.assertTrue(self._flag.is_default)
    
    def test_is_equal(self):
        self.assertEqual(self._flag, 2137)
    
    def test_is_not_equal(self):
        self.assertNotEqual(self._flag, 9999)
    
    def test_is_greater(self):
        self.assertGreater(self._flag, 0)
    
    def test_is_less(self):
        self.assertLess(self._flag, 9999)