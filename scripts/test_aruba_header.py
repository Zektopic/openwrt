import unittest
import importlib.util
import os
import array
import sys

class TestArubaHeader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(__file__), 'aruba-header.py')
        spec = importlib.util.spec_from_file_location("aruba_header", script_path)
        cls.aruba_header = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.aruba_header)

    def test_make_header_valid(self):
        data = b'testdata'
        build = 'build123'
        version = '1.0.0'
        oem = 'myoem'
        imageType = self.aruba_header.ImageType.ELF
        machineType = self.aruba_header.MACHINE_TYPES['MSWITCH']

        header = self.aruba_header.make_header(data, build, version, oem, imageType, machineType)

        self.assertEqual(len(header), 512)

        # Verify payload size (bytes 0-3)
        self.assertEqual(int.from_bytes(header[0:4], 'big'), len(data))

        # Verify format version (bytes 4-7)
        self.assertEqual(int.from_bytes(header[4:8], 'big'), self.aruba_header.FormatVersion.CURRENT)

        # Verify magic (bytes 12-19)
        self.assertEqual(header[12:20], self.aruba_header.HEADER_MAGIC)

        # Verify build string (bytes 20-275)
        build_bytes = header[20:20+256]
        self.assertTrue(build_bytes.startswith(b'build123\0'))
        self.assertEqual(len(build_bytes), 256)

        # Verify version string (bytes 276-299)
        version_bytes = header[276:276+24]
        self.assertTrue(version_bytes.startswith(b'1.0.0\0'))
        self.assertEqual(len(version_bytes), 24)

        # Verify valid flag (byte 300)
        self.assertEqual(header[300], self.aruba_header.ValidFlag.YES)

        # Verify image type (byte 301)
        self.assertEqual(header[301], imageType)

        # Verify compression type (byte 302)
        self.assertEqual(header[302], self.aruba_header.CompressionType.NONE)

        # Verify machine type (byte 303)
        self.assertEqual(header[303], machineType)

        # Verify OEM string (bytes 384-415)
        oem_bytes = header[384:384+32]
        self.assertTrue(oem_bytes.startswith(b'myoem\0'))
        self.assertEqual(len(oem_bytes), 32)

        # Verify checksum
        header_words = array.array('I', header)
        data_words = array.array('I', data)
        if sys.byteorder == 'little':
            header_words.byteswap()
            data_words.byteswap()

        total_sum = (sum(header_words) + sum(data_words)) % 0x100000000
        self.assertEqual(total_sum, 0)

    def test_make_header_exact_bytes(self):
        data = b'testdata'
        build = 'build123'
        version = '1.0.0'
        oem = 'myoem'
        imageType = self.aruba_header.ImageType.ELF
        machineType = self.aruba_header.MACHINE_TYPES['MSWITCH']

        header = self.aruba_header.make_header(data, build, version, oem, imageType, machineType)

        expected_header = (
            b'\x00\x00\x00\x08' +
            b'\x00\x00\x00\x02' +
            b'\xa1\x98\x87\xa5' +
            b'ARUBA\x00\x00\x00' +
            b'build123' + b'\x00' * 248 +
            b'1.0.0' + b'\x00' * 19 +
            b'\x01' +
            b'\x00' +
            b'\x00' +
            b'\x00' +
            b'\x00\x00\x00\x08' +
            b'\x00\x00\x00\x00' +
            b'\x00' * 16 +
            b'\x00' * 4 +
            b'\x00\x00\x00\x00' +
            b'\x00' * 12 +
            b'\x00' * 36 +
            b'myoem' + b'\x00' * 27 +
            b'\x00' * 96
        )

        self.assertEqual(header, expected_header)

    def test_make_header_too_long_strings(self):
        data = b'testdata'

        # Build string too long (>= 256)
        with self.assertRaises(AssertionError):
            self.aruba_header.make_header(data, 'a' * 256, '1.0', 'oem', 0, 0)

        # Version string too long (>= 24)
        with self.assertRaises(AssertionError):
            self.aruba_header.make_header(data, 'build', 'a' * 24, 'oem', 0, 0)

        # OEM string too long (>= 32)
        with self.assertRaises(AssertionError):
            self.aruba_header.make_header(data, 'build', '1.0', 'a' * 32, 0, 0)

    def test_make_header_data_not_multiple_of_4(self):
        data = b'123'
        with self.assertRaises(AssertionError):
            self.aruba_header.make_header(data, 'build', '1.0', 'oem', 0, 0)

if __name__ == '__main__':
    unittest.main()
