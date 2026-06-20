import unittest
import importlib.util
import os
import sys
from unittest.mock import patch, MagicMock

class TestCameoTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mock_args = MagicMock()
        mock_args.uimage_file.tell.return_value = 100
        mock_args.rootfs_start = 50
        mock_args.uimage_file.read.return_value = b""

        with patch('argparse.ArgumentParser.parse_args', return_value=mock_args):
            script_path = os.path.join(os.path.dirname(__file__), 'cameo-tag.py')
            spec = importlib.util.spec_from_file_location("cameo_tag", script_path)
            cls.cameo_tag = importlib.util.module_from_spec(spec)
            sys.modules["cameo_tag"] = cls.cameo_tag
            spec.loader.exec_module(cls.cameo_tag)

    @classmethod
    def tearDownClass(cls):
        if "cameo_tag" in sys.modules:
            del sys.modules["cameo_tag"]

    def test_cameosum_empty(self):
        self.assertEqual(self.cameo_tag.cameosum(b""), b'\x00\x00\x00\x00')

    def test_cameosum_simple(self):
        self.assertEqual(self.cameo_tag.cameosum(b"\x01\x02\x03"), b'\x00\x00\x00\x06')

    def test_cameosum_large(self):
        buf = b"\xff" * 16843010
        self.assertEqual(self.cameo_tag.cameosum(buf), b'\x00\x00\x00\xfe')

    def test_invertcrc_empty(self):
        self.assertEqual(self.cameo_tag.invertcrc(b""), b'\xff\xff\xff\xff')

    def test_invertcrc_simple(self):
        self.assertEqual(self.cameo_tag.invertcrc(b"Hello, World!"), b'\x2f\x3c\xb5\x13')

    def test_checksum_header(self):
        buf = bytearray(b'\x00' * 64)
        result = self.cameo_tag.checksum_header(buf)

        self.assertEqual(result[32:44], b'OpenWrt\x00\x00\x00\x00\x00')
        self.assertEqual(result[44:56], b'CAMEOTAG\x00\x00\x00\x01')

        self.assertEqual(result[4:8], b'\xff\xff\xff\xff')

        sum_val = self.cameo_tag.cameosum(result[0:56])
        self.assertEqual(result[56:60], sum_val)

        buf_for_inv = bytearray(result[0:60])
        buf_for_inv[4:8] = b'\x00\x00\x00\x00'
        expected_inv = self.cameo_tag.invertcrc(buf_for_inv)
        self.assertEqual(result[60:64], expected_inv)

if __name__ == '__main__':
    unittest.main()
