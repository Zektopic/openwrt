import unittest
import importlib.util

spec = importlib.util.spec_from_file_location("sercomm_crypto", "scripts/sercomm-crypto.py")
sercomm_crypto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sercomm_crypto)

class TestSercommCrypto(unittest.TestCase):
    def test_create_header(self):
        key = b"1234567890"
        version = b"1.0.0"
        iv = b"iv_data"
        random = b"random_data"
        size = b"1024"

        header = sercomm_crypto.create_header(key, version, iv, random, size)

        self.assertEqual(len(header), 160) # 5 * 32

        self.assertEqual(header[0:32], key.ljust(32, b'\0'))
        self.assertEqual(header[32:64], version.ljust(32, b'\0'))
        self.assertEqual(header[64:96], iv.ljust(32, b'\0'))
        self.assertEqual(header[96:128], random.ljust(32, b'\0'))
        self.assertEqual(header[128:160], size.ljust(32, b'\0'))
