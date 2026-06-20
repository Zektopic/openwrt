import unittest
import importlib.util
import os
import tempfile
import sys
import struct
import binascii

spec = importlib.util.spec_from_file_location("sercomm_kernel_header", os.path.join(os.path.dirname(__file__), "sercomm-kernel-header.py"))
sercomm_kernel_header = importlib.util.module_from_spec(spec)
sys.modules['sercomm_kernel_header'] = sercomm_kernel_header
spec.loader.exec_module(sercomm_kernel_header)

class TestSercommKernelHeader(unittest.TestCase):
    def test_auto_int(self):
        self.assertEqual(sercomm_kernel_header.auto_int("0x10"), 16)
        self.assertEqual(sercomm_kernel_header.auto_int("10"), 10)
        self.assertEqual(sercomm_kernel_header.auto_int("0o10"), 8)

    def test_get_kernel_header(self):
        class DummyArgs:
            pass

        args = DummyArgs()
        args.kernel_offset = 0x1000
        args.rootfs_offset = 0x20000
        args.rootfs_file = None
        args.rootfs_checking_size = None

        with tempfile.NamedTemporaryFile() as kernel_f:
            kernel_data = b"fake kernel data"*1024
            kernel_f.write(kernel_data)
            kernel_f.flush()
            args.kernel_file = kernel_f.name

            header = sercomm_kernel_header.get_kernel_header(args)

            self.assertEqual(len(header), sercomm_kernel_header.KERNEL_HEADER_SIZE)

            # verify padding
            self.assertEqual(header[0x38:], bytearray([sercomm_kernel_header.PADDING] * (sercomm_kernel_header.KERNEL_HEADER_SIZE - 0x38)))

            # Verify basic fields
            magic = struct.unpack_from('<L', header, 0x0)[0]
            self.assertEqual(magic, 0x726553)

            kernel_end_offset = struct.unpack_from('<L', header, 0x4)[0]
            self.assertEqual(kernel_end_offset, args.kernel_offset + len(kernel_data))

            # Just test magic values that are fixed
            self.assertEqual(struct.unpack_from('<L', header, 0xc)[0], 0xffffff02)
            self.assertEqual(struct.unpack_from('<L', header, 0x10)[0], args.kernel_offset)
            self.assertEqual(struct.unpack_from('<L', header, 0x14)[0], len(kernel_data))

            # kernel crc
            kernel_crc = binascii.crc32(kernel_data) & 0xffffffff
            self.assertEqual(struct.unpack_from('<L', header, 0x18)[0], kernel_crc)

            self.assertEqual(struct.unpack_from('<L', header, 0x1c)[0], 0x0)
            self.assertEqual(struct.unpack_from('<L', header, 0x28)[0], args.rootfs_offset)

            # rootfs without rootfs_file
            self.assertEqual(struct.unpack_from('<L', header, 0x2c)[0], len(sercomm_kernel_header.ROOTFS_FAKE_HEADER))
            fake_rootfs_crc = binascii.crc32(sercomm_kernel_header.ROOTFS_FAKE_HEADER.encode()) & 0xffffffff
            self.assertEqual(struct.unpack_from('<L', header, 0x30)[0], fake_rootfs_crc)

            self.assertEqual(struct.unpack_from('<L', header, 0x34)[0], 0x0)

            # Check header CRC
            header_no_crc = bytearray(header)
            # The CRC of the header is calculated BEFORE writing the CRC itself
            struct.pack_into('<L', header_no_crc, 0x8, 0)
            struct.pack_into('<L', header_no_crc, 0x8, 0xffffffff) # padding
            struct.pack_into('<L', header_no_crc, 0x0, 0xffffffff) # padding as magic wasn't set!

            expected_header_crc = binascii.crc32(header_no_crc) & 0xffffffff
            self.assertEqual(struct.unpack_from('<L', header, 0x8)[0], expected_header_crc)

    # def tearDown(self):
        # if "sercomm_kernel_header" in sys.modules:
            # del sys.modules["sercomm_kernel_header"]
    def test_get_kernel_header_with_rootfs(self):
        class DummyArgs:
            pass

        args = DummyArgs()
        args.kernel_offset = 0x1000
        args.rootfs_offset = 0x20000

        with tempfile.NamedTemporaryFile() as kernel_f, tempfile.NamedTemporaryFile() as rootfs_f:
            kernel_data = b"fake kernel data"*1024
            kernel_f.write(kernel_data)
            kernel_f.flush()
            args.kernel_file = kernel_f.name

            rootfs_data = b"fake rootfs data"*2048
            rootfs_f.write(rootfs_data)
            rootfs_f.flush()
            args.rootfs_file = rootfs_f.name
            args.rootfs_checking_size = None

            header = sercomm_kernel_header.get_kernel_header(args)

            # rootfs with rootfs_file
            self.assertEqual(struct.unpack_from('<L', header, 0x2c)[0], len(rootfs_data))
            rootfs_crc = binascii.crc32(rootfs_data) & 0xffffffff
            self.assertEqual(struct.unpack_from('<L', header, 0x30)[0], rootfs_crc)

    def test_get_kernel_header_with_rootfs_checking_size(self):
        class DummyArgs:
            pass

        args = DummyArgs()
        args.kernel_offset = 0x1000
        args.rootfs_offset = 0x20000

        with tempfile.NamedTemporaryFile() as kernel_f, tempfile.NamedTemporaryFile() as rootfs_f:
            kernel_data = b"fake kernel data"*1024
            kernel_f.write(kernel_data)
            kernel_f.flush()
            args.kernel_file = kernel_f.name

            rootfs_data = b"fake rootfs data"*2048
            rootfs_f.write(rootfs_data)
            rootfs_f.flush()
            args.rootfs_file = rootfs_f.name
            args.rootfs_checking_size = 100

            header = sercomm_kernel_header.get_kernel_header(args)

            # rootfs with rootfs_checking_size
            self.assertEqual(struct.unpack_from('<L', header, 0x2c)[0], 100)
            rootfs_crc = binascii.crc32(rootfs_data[:100]) & 0xffffffff
            self.assertEqual(struct.unpack_from('<L', header, 0x30)[0], rootfs_crc)

    def test_create_kernel_header(self):
        class DummyArgs:
            pass

        args = DummyArgs()
        args.kernel_offset = 0x1000
        args.rootfs_offset = 0x20000
        args.rootfs_file = None
        args.rootfs_checking_size = None

        with tempfile.NamedTemporaryFile() as kernel_f, tempfile.NamedTemporaryFile() as header_f:
            kernel_data = b"fake kernel data"*1024
            kernel_f.write(kernel_data)
            kernel_f.flush()
            args.kernel_file = kernel_f.name
            args.header_file = header_f.name

            sercomm_kernel_header.create_kernel_header(args)

            with open(header_f.name, 'rb') as f:
                header = f.read()

            self.assertEqual(len(header), sercomm_kernel_header.KERNEL_HEADER_SIZE)
            magic = struct.unpack_from('<L', header, 0x0)[0]
            self.assertEqual(magic, 0x726553)
if __name__ == '__main__':
    unittest.main()
