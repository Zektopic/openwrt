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

    def test_xcrc32_known_value(self):
        # Check against a pre-calculated value
        self.assertEqual(self.belkin_header.xcrc32(b"OpenWrt"), b'\x10\xd8\xe6\x38')

    def test_xcrc32_val_zero(self):
        self.assertEqual(self.belkin_header.xcrc32_val(0), b'\xff\xff\xff\xff')

    def test_xcrc32_val_max(self):
        self.assertEqual(self.belkin_header.xcrc32_val(0xffffffff), b'\x00\x00\x00\x00')

    def test_xcrc32_val_random(self):
        self.assertEqual(self.belkin_header.xcrc32_val(0x1cc17aad), b'\xe3\x3e\x85\x52')

    def test_encode_model_rtl83xx(self):
        expected = bytes.fromhex('0c55dfdc796244f3c000')
        self.assertEqual(self.belkin_header.encode_model("BKS-RTL83xx"), expected)

    def test_encode_model_rtl93xx(self):
        expected = bytes.fromhex('0c55dfdc796284f3c000')
        self.assertEqual(self.belkin_header.encode_model("BKS-RTL93xx"), expected)

    def test_create_header(self):
        from unittest.mock import patch

        with patch('time.time', return_value=1700000000):
            # size=1024, crc=0x12345678, belkin_header='0x07800001', belkin_model='BKS-RTL83xx'
            header = self.belkin_header.create_header(1024, 0x12345678, '0x07800001', 'BKS-RTL83xx')

            self.assertEqual(len(header), 64)
            self.assertEqual(header[:4], b'\x07\x80\x00\x01')  # Belkin header
            self.assertEqual(header[8:12], b'\x65\x53\xf1\x00') # time (1700000000)
            self.assertEqual(header[12:16], b'\x00\x00\x04\x00') # size (1024)
            self.assertEqual(header[16:24], b'belkin\x00\x00') # company
            self.assertEqual(header[24:28], b'\xed\xcb\xa9\x87') # xcrc32_val of crc 0x12345678 (0xffffffff - 0x12345678)
            self.assertEqual(header[28:32], b'\x01\x01\x02\x02') # versions
            self.assertEqual(header[32:46], b'IMG-1.01.02.02') # mod
            self.assertEqual(header[47:57], bytes.fromhex('0c55dfdc796244f3c000')) # model

if __name__ == '__main__':
    unittest.main()
