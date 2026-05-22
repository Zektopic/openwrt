import unittest
import importlib.util
import struct

spec = importlib.util.spec_from_file_location("moxa_encode_fw", "scripts/moxa-encode-fw.py")
moxa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(moxa)

class TestMoxaEncodeFw(unittest.TestCase):
    def test_add_fw_header_happy(self):
        data = b"hello"
        magic = 0x1234567812345678 # 'Q' allows up to 64-bit unsigned
        hwid = 0x1111 # 'I' allows up to 32-bit unsigned
        build_id = 0x2222 # 'I' allows up to 32-bit unsigned
        offsets = [10, 20]
        res = moxa.add_fw_header(data, magic, hwid, build_id, offsets)
        self.assertTrue(len(res) > len(data))

    def test_add_fw_header_invalid_type(self):
        data = b"hello"
        magic = "not an int"
        hwid = 0x1111
        build_id = 0x2222
        offsets = [10, 20]
        with self.assertRaises(struct.error):
            moxa.add_fw_header(data, magic, hwid, build_id, offsets)

    def test_add_fw_header_invalid_size(self):
        data = b"hello"
        magic = 0x1234567812345678
        hwid = 0xfffffffff # > 32 bit, 'I' expects unsigned int which is 32-bit max
        build_id = 0x2222
        offsets = [10, 20]
        with self.assertRaises(struct.error):
            moxa.add_fw_header(data, magic, hwid, build_id, offsets)

    def test_add_fw_header_invalid_magic_size(self):
        data = b"hello"
        magic = 0xfffffffffffffffff # > 64 bit, 'Q' expects unsigned long long which is 64-bit max
        hwid = 0x1111
        build_id = 0x2222
        offsets = [10, 20]
        with self.assertRaises(struct.error):
            moxa.add_fw_header(data, magic, hwid, build_id, offsets)

if __name__ == '__main__':
    unittest.main()
