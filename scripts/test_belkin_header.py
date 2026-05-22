import unittest
import importlib.util
import os

class TestBelkinHeader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Dynamically import the script due to the hyphen in the filename
        script_path = os.path.join(os.path.dirname(__file__), 'belkin-header.py')
        spec = importlib.util.spec_from_file_location("belkin_header", script_path)
        cls.belkin_header = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.belkin_header)

    def test_xcrc32_empty(self):
        # zlib.crc32(b'', 0xffffffff) is 0xffffffff. 0xffffffff - 0xffffffff is 0.
        self.assertEqual(self.belkin_header.xcrc32(b""), b'\x00\x00\x00\x00')

    def test_xcrc32_string(self):
        # zlib.crc32(b'Hello, World!', 0xffffffff) is 0x1cc17aad
        # 0xffffffff - 0x1cc17aad is 0xe33e8552
        self.assertEqual(self.belkin_header.xcrc32(b"Hello, World!"), b'\xe3\x3e\x85\x52')

    def test_xcrc32_val_zero(self):
        self.assertEqual(self.belkin_header.xcrc32_val(0), b'\xff\xff\xff\xff')

    def test_xcrc32_val_max(self):
        self.assertEqual(self.belkin_header.xcrc32_val(0xffffffff), b'\x00\x00\x00\x00')

    def test_xcrc32_val_random(self):
        self.assertEqual(self.belkin_header.xcrc32_val(0x1cc17aad), b'\xe3\x3e\x85\x52')

if __name__ == '__main__':
    unittest.main()
