import unittest
import importlib.util
import os
import struct
from collections import namedtuple

class TestCfeBinHeader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(__file__), 'cfe-bin-header.py')
        spec = importlib.util.spec_from_file_location("cfe_bin_header", script_path)
        cls.cfe_bin_header = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cfe_bin_header)

    def test_auto_int(self):
        self.assertEqual(self.cfe_bin_header.auto_int('0x10'), 16)
        self.assertEqual(self.cfe_bin_header.auto_int('16'), 16)
        self.assertEqual(self.cfe_bin_header.auto_int('0o10'), 8)
        self.assertEqual(self.cfe_bin_header.auto_int('0b10'), 2)

        with self.assertRaises(ValueError):
            self.cfe_bin_header.auto_int('invalid')

    def test_create_header(self):
        Args = namedtuple('Args', ['entry_addr', 'load_addr'])
        args = Args(entry_addr=0x80010000, load_addr=0x80010000)
        size = 1024
        header = self.cfe_bin_header.create_header(args, size)

        expected = struct.pack('>III', 0x80010000, 0x80010000, 1024)
        self.assertEqual(header, expected)

    def test_create_header_different_values(self):
        Args = namedtuple('Args', ['entry_addr', 'load_addr'])
        args = Args(entry_addr=0x12345678, load_addr=0xabcdef01)
        size = 0
        header = self.cfe_bin_header.create_header(args, size)

        expected = struct.pack('>III', 0x12345678, 0xabcdef01, 0)
        self.assertEqual(header, expected)

if __name__ == '__main__':
    unittest.main()
