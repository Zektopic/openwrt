import unittest
import importlib.util
import os
import sys
import struct
import io
import argparse

class TestCameoImghdr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(__file__), 'cameo-imghdr.py')
        spec = importlib.util.spec_from_file_location("cameo_imghdr", script_path)
        cls.cameo_imghdr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cameo_imghdr)

    def run_script(self, args_dict):
        # Create an argparse.Namespace from the dictionary
        args = argparse.Namespace(**args_dict)
        self.cameo_imghdr.generate_header(args)

    def test_happy_path(self):
        source_file = io.BytesIO(b"Hello World")
        dest_file = io.BytesIO()

        args = {
            'source_file': source_file,
            'dest_file': dest_file,
            'model': "MODEL_XYZ",
            'signature': "sig",
            'partition': 1,
            'customer_signature': 2,
            'board_version': 3,
            'linux_loadaddr': None
        }

        self.run_script(args)

        data = dest_file.getvalue()

        self.assertEqual(len(data), 64 + len(b"Hello World"))

        header = data[:64]
        payload = data[64:]
        self.assertEqual(payload, b"Hello World")

        unpacked = struct.unpack('!I20s16sBBBBII10s2x', header)

        checksum = sum(b"Hello World") % (1<<32)

        self.assertEqual(unpacked[0], checksum)
        self.assertEqual(unpacked[1].decode("ascii").rstrip('\x00'), "MODEL_XYZ")
        self.assertEqual(unpacked[2].decode("ascii").rstrip('\x00'), "sig")
        self.assertEqual(unpacked[3], 1)
        self.assertEqual(unpacked[4], 0x40)
        self.assertEqual(unpacked[5], 0x00)
        self.assertEqual(unpacked[6], 2)
        self.assertEqual(unpacked[7], 3)
        self.assertEqual(unpacked[8], len(b"Hello World"))
        self.assertEqual(unpacked[9].decode("ascii").rstrip('\x00'), "")

    def test_os_signature_with_loadaddr(self):
        source_file = io.BytesIO(b"Kernel Data")
        dest_file = io.BytesIO()

        args = {
            'source_file': source_file,
            'dest_file': dest_file,
            'model': "MODEL_OS",
            'signature': "os",
            'partition': 5,
            'customer_signature': 6,
            'board_version': 7,
            'linux_loadaddr': "0x12345678"
        }

        self.run_script(args)

        data = dest_file.getvalue()

        header = data[:64]
        unpacked = struct.unpack('!I20s16sBBBBII10s2x', header)

        self.assertEqual(unpacked[1].decode("ascii").rstrip('\x00'), "MODEL_OS")
        self.assertEqual(unpacked[2].decode("ascii").rstrip('\x00'), "os")
        self.assertEqual(unpacked[3], 5)
        self.assertEqual(unpacked[6], 6)
        self.assertEqual(unpacked[7], 7)
        self.assertEqual(unpacked[9].decode("ascii").rstrip('\x00'), "0x12345678")

    def test_os_signature_missing_loadaddr(self):
        args = {
            'source_file': io.BytesIO(),
            'dest_file': io.BytesIO(),
            'model': "MODEL_OS",
            'signature': "os",
            'partition': 5,
            'customer_signature': 6,
            'board_version': 7,
            'linux_loadaddr': None
        }
        with self.assertRaises(ValueError) as context:
            self.run_script(args)
        self.assertIn("linux_loadaddr is required for signature 'os'", str(context.exception))

    def test_model_too_long(self):
        args = {
            'source_file': io.BytesIO(),
            'dest_file': io.BytesIO(),
            'model': "A" * 21,
            'signature': "sig",
            'partition': 1,
            'customer_signature': 2,
            'board_version': 3,
            'linux_loadaddr': None
        }
        with self.assertRaises(ValueError) as context:
            self.run_script(args)
        self.assertIn("is greater than 20 bytes", str(context.exception))

    def test_signature_too_long(self):
        args = {
            'source_file': io.BytesIO(),
            'dest_file': io.BytesIO(),
            'model': "M",
            'signature': "B" * 17,
            'partition': 1,
            'customer_signature': 2,
            'board_version': 3,
            'linux_loadaddr': None
        }
        with self.assertRaises(ValueError) as context:
            self.run_script(args)
        self.assertIn("is greater than", str(context.exception))
        self.assertIn("16 bytes", str(context.exception))

    def test_loadaddr_too_long(self):
        args = {
            'source_file': io.BytesIO(),
            'dest_file': io.BytesIO(),
            'model': "M",
            'signature': "os",
            'partition': 1,
            'customer_signature': 2,
            'board_version': 3,
            'linux_loadaddr': "0x123456789"
        }
        with self.assertRaises(ValueError) as context:
            self.run_script(args)
        self.assertIn("is greater", str(context.exception))
        self.assertIn("than 10 bytes", str(context.exception))

    def test_loadaddr_invalid_prefix(self):
        args = {
            'source_file': io.BytesIO(),
            'dest_file': io.BytesIO(),
            'model': "M",
            'signature': "os",
            'partition': 1,
            'customer_signature': 2,
            'board_version': 3,
            'linux_loadaddr': "1x12345678"
        }
        with self.assertRaises(ValueError) as context:
            self.run_script(args)
        self.assertIn("must use", str(context.exception))
        self.assertIn("the 0x789ABCDE format", str(context.exception))

if __name__ == '__main__':
    unittest.main()
