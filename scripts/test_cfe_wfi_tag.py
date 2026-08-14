import unittest
import importlib.util
import os
import struct
import tempfile
import binascii

class TestCfeWfiTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the module dynamically due to dashes in the filename
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cfe-wfi-tag.py")
        spec = importlib.util.spec_from_file_location("cfe_wfi_tag", script_path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_auto_int(self):
        self.assertEqual(self.module.auto_int("0x10"), 16)
        self.assertEqual(self.module.auto_int("10"), 10)

    def test_create_tag(self):
        class Args:
            tag_version = 0x00005732
            chip_id = 0x00006328
            flash_type = 2
            flags = 1

        args = Args()
        crc = 0x12345678

        tag = self.module.create_tag(args, crc)

        expected_crc = ~crc & 0xFFFFFFFF

        self.assertEqual(len(tag), 20)
        unpacked = struct.unpack(">IIIII", tag)
        self.assertEqual(unpacked[0], expected_crc)
        self.assertEqual(unpacked[1], args.tag_version)
        self.assertEqual(unpacked[2], args.chip_id)
        self.assertEqual(unpacked[3], args.flash_type)
        self.assertEqual(unpacked[4], args.flags)

    def test_create_output_same_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"hello world")
            tf_name = tf.name

        try:
            class Args:
                input_file = tf_name
                output_file = tf_name
                tag_version = 0x00005732
                chip_id = 0x00006328
                flash_type = 2
                flags = 1

            args = Args()

            self.module.create_output(args)

            with open(tf_name, "rb") as f:
                content = f.read()

            original_data = b"hello world"
            self.assertTrue(content.startswith(original_data))

            tag = content[len(original_data):]
            self.assertEqual(len(tag), 20)

            crc = binascii.crc32(original_data, 0)
            expected_crc = ~crc & 0xFFFFFFFF
            unpacked = struct.unpack(">IIIII", tag)
            self.assertEqual(unpacked[0], expected_crc)

        finally:
            if os.path.exists(tf_name):
                os.remove(tf_name)

    def test_create_output_different_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf_in:
            tf_in.write(b"different file test")
            tf_in_name = tf_in.name

        tf_out_name = tf_in_name + "_out"

        try:
            class Args:
                input_file = tf_in_name
                output_file = tf_out_name
                tag_version = 0x00005732
                chip_id = 0x00006328
                flash_type = 2
                flags = 1

            args = Args()

            self.module.create_output(args)

            with open(tf_out_name, "rb") as f:
                content = f.read()

            original_data = b"different file test"
            self.assertTrue(content.startswith(original_data))

            tag = content[len(original_data):]
            self.assertEqual(len(tag), 20)

            crc = binascii.crc32(original_data, 0)
            expected_crc = ~crc & 0xFFFFFFFF
            unpacked = struct.unpack(">IIIII", tag)
            self.assertEqual(unpacked[0], expected_crc)

        finally:
            if os.path.exists(tf_in_name):
                os.remove(tf_in_name)
            if os.path.exists(tf_out_name):
                os.remove(tf_out_name)

if __name__ == '__main__':
    unittest.main()
