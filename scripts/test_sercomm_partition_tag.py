import unittest
import importlib.util
import os
import struct
from collections import namedtuple

class TestSercommPartitionTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(__file__), 'sercomm-partition-tag.py')
        spec = importlib.util.spec_from_file_location("sercomm_partition_tag", script_path)
        cls.sercomm_partition_tag = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.sercomm_partition_tag)

    def test_create_header(self):
        Args = namedtuple('Args', ['part_name', 'part_version', 'rootfs_version'])
        args = Args(part_name='kernel', part_version='1.0', rootfs_version='2.0')
        size = 1048576

        header = self.sercomm_partition_tag.create_header(args, size)

        expected = struct.pack('32s32s32s32s32s',
            b'kernel',
            b'1048576',
            b'1.0',
            b'',
            b'2.0'
        )
        self.assertEqual(header, expected)

    def test_create_header_empty_rootfs(self):
        Args = namedtuple('Args', ['part_name', 'part_version', 'rootfs_version'])
        args = Args(part_name='rootfs', part_version='1.1', rootfs_version='')
        size = 2048

        header = self.sercomm_partition_tag.create_header(args, size)

        expected = struct.pack('32s32s32s32s32s',
            b'rootfs',
            b'2048',
            b'1.1',
            b'',
            b''
        )
        self.assertEqual(header, expected)

if __name__ == '__main__':
    unittest.main()
