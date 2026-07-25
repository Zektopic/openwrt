import unittest
import importlib.util
from unittest.mock import Mock
import os
import tempfile
import hashlib

spec = importlib.util.spec_from_file_location("sercomm_payload", "scripts/sercomm-payload.py")
sercomm_payload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sercomm_payload)

class TestSercommPayload(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_file = os.path.join(self.test_dir.name, "input.bin")
        self.output_file = os.path.join(self.test_dir.name, "output.bin")
        self.pid_file = os.path.join(self.test_dir.name, "pid.bin")

        self.input_data = b"Hello World" * 100000
        with open(self.input_file, "wb") as f:
            f.write(self.input_data)

        self.pid_data = b"PIDDATA123"
        with open(self.pid_file, "wb") as f:
            f.write(self.pid_data)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_create_output_with_pid_file(self):
        args = Mock()
        args.input_file = self.input_file
        args.output_file = self.output_file
        args.pid_file = self.pid_file
        args.pid = None

        sercomm_payload.create_output(args)

        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file, "rb") as f:
            out_data = f.read()

        sha256_hash = hashlib.sha256(self.input_data).digest()

        expected_output = self.pid_data + sha256_hash + self.input_data

        self.assertEqual(out_data, expected_output)

    def test_create_output_with_pid_hex(self):
        args = Mock()
        args.input_file = self.input_file
        args.output_file = self.output_file
        args.pid_file = None
        args.pid = "1234abcd"

        sercomm_payload.create_output(args)

        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file, "rb") as f:
            out_data = f.read()

        sha256_hash = hashlib.sha256(self.input_data).digest()
        pid_data = bytes.fromhex(args.pid)

        expected_output = pid_data + sha256_hash + self.input_data

        self.assertEqual(out_data, expected_output)

if __name__ == '__main__':
    unittest.main()
