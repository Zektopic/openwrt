import unittest
import importlib.util
import os
import tempfile
import sys
import struct
import hashlib

spec = importlib.util.spec_from_file_location("sercomm_payload", os.path.join(os.path.dirname(__file__), "sercomm-payload.py"))
sercomm_payload = importlib.util.module_from_spec(spec)
sys.modules['sercomm_payload'] = sercomm_payload
spec.loader.exec_module(sercomm_payload)

class TestSercommPayload(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.input_file = os.path.join(self.tmp_dir.name, "input.bin")
        self.output_file = os.path.join(self.tmp_dir.name, "output.bin")
        self.pid_file = os.path.join(self.tmp_dir.name, "pid.bin")

        self.input_data = b"some test data here"
        with open(self.input_file, "wb") as f:
            f.write(self.input_data)

        self.pid_data = b"PID_FILE_DATA"
        with open(self.pid_file, "wb") as f:
            f.write(self.pid_data)

        class DummyArgs:
            pass
        self.args = DummyArgs()
        self.args.input_file = self.input_file
        self.args.output_file = self.output_file
        self.args.pid_file = None
        self.args.pid = None

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_create_output_with_pid_hex(self):
        self.args.pid = "deadbeef"
        sercomm_payload.create_output(self.args)

        with open(self.output_file, "rb") as f:
            out_data = f.read()

        pid_bytes = bytes.fromhex("deadbeef")
        sha256 = hashlib.sha256(self.input_data).digest()

        expected_out = pid_bytes + sha256 + self.input_data
        self.assertEqual(out_data, expected_out)

    def test_create_output_with_pid_file(self):
        self.args.pid_file = self.pid_file
        sercomm_payload.create_output(self.args)

        with open(self.output_file, "rb") as f:
            out_data = f.read()

        sha256 = hashlib.sha256(self.input_data).digest()

        expected_out = self.pid_data + sha256 + self.input_data
        self.assertEqual(out_data, expected_out)

if __name__ == '__main__':
    unittest.main()
