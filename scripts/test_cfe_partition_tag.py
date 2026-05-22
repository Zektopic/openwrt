import unittest
import importlib.util
import struct
import os

# Ensure the path is correct whether run from repo root or scripts/
script_path = "scripts/cfe-partition-tag.py"
if not os.path.exists(script_path):
    script_path = "cfe-partition-tag.py"

# Load module
spec = importlib.util.spec_from_file_location("cfe_partition_tag", script_path)
cfe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfe)

class MockArgs:
    def __init__(self, part_id, part_flags, part_name, part_version):
        self.part_id = part_id
        self.part_flags = part_flags
        self.part_name = part_name
        self.part_version = part_version

class TestCfePartitionTag(unittest.TestCase):
    def test_auto_int(self):
        self.assertEqual(cfe.auto_int("123"), 123)
        self.assertEqual(cfe.auto_int("0x10"), 16)
        self.assertEqual(cfe.auto_int("0b10"), 2)

    def test_create_tag_normal(self):
        args = MockArgs(
            part_id=1234,
            part_flags=5678,
            part_name="TestName",
            part_version="1.0.0"
        )
        crc = 0x12345678
        size = 1024

        tag = cfe.create_tag(args, crc, size)

        # JAM CRC32 is bitwise not and unsigned
        expected_crc = ~crc & 0xFFFFFFFF

        b_name = b"TestName"
        b_version = b"1.0.0"
        expected = struct.pack(
            f">IIH33s21sI",
            1234,
            1024,
            5678,
            b_name,
            b_version,
            expected_crc
        )

        self.assertEqual(tag, bytearray(expected))

    def test_create_tag_long_name_and_version(self):
        args = MockArgs(
            part_id=1,
            part_flags=2,
            part_name="A"*50,
            part_version="B"*50
        )
        crc = 0x87654321
        size = 2048

        tag = cfe.create_tag(args, crc, size)

        expected_crc = ~crc & 0xFFFFFFFF

        # Strings are truncated to size-1 and then null terminated
        b_name = (b"A" * 32) + b'\x00'
        b_version = (b"B" * 20) + b'\x00'

        expected = struct.pack(
            f">IIH33s21sI",
            1,
            2048,
            2,
            b_name,
            b_version,
            expected_crc
        )

        self.assertEqual(tag, bytearray(expected))

if __name__ == '__main__':
    unittest.main()
