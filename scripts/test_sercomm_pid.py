import unittest
import importlib.util
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("sercomm_pid", "scripts/sercomm-pid.py")
sercomm_pid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sercomm_pid)

class TestSercommPid(unittest.TestCase):
    def test_get_pid_no_hw_id(self):
        args = Mock()
        args.hw_version = "HW_V"
        args.hw_id = None
        args.sw_version = "SW_V"
        args.extra_padd_size = 0
        args.extra_padd_byte = 0

        pid = sercomm_pid.get_pid(args)

        self.assertEqual(len(pid), sercomm_pid.PID_SIZE)
        # 14s rjust
        self.assertEqual(pid[0:14], b'0000000000HW_V')
        # 4s sw_version rjust at 0x64 (100)
        self.assertEqual(pid[100:104], b'SW_V')
        # Padding should be PADDING (0x30 = '0')
        self.assertEqual(pid[14:100], b'0' * (100 - 14))

    def test_get_pid_with_hw_id(self):
        args = Mock()
        args.hw_version = "HW_V"
        args.hw_id = "ID"
        args.sw_version = "SW_V"
        args.extra_padd_size = 0
        args.extra_padd_byte = 0

        pid = sercomm_pid.get_pid(args)

        self.assertEqual(len(pid), sercomm_pid.PID_SIZE)
        self.assertEqual(pid[0:8], b'0000HW_V')

        # hw_id is hexlified and upper
        # "ID".encode() -> b"ID" -> hexlify -> b"4944"
        self.assertEqual(pid[8:14], b'4944\0\0')

        self.assertEqual(pid[100:104], b'SW_V')

    def test_get_pid_extra_padd_no_byte_no_hw_id(self):
        args = Mock()
        args.hw_version = "HW_V"
        args.hw_id = None
        args.sw_version = "SW_V"
        args.extra_padd_size = 4
        args.extra_padd_byte = 0

        pid = sercomm_pid.get_pid(args)

        self.assertEqual(len(pid), sercomm_pid.PID_SIZE + 4)

        self.assertEqual(pid[-4:], bytearray([0x0D, 0x0A, 0x00, 0x00]))

    def test_get_pid_extra_padd_with_byte(self):
        args = Mock()
        args.hw_version = "HW_V"
        args.hw_id = "ID"
        args.sw_version = "SW_V"
        args.extra_padd_size = 4
        args.extra_padd_byte = 0x12345678

        pid = sercomm_pid.get_pid(args)

        self.assertEqual(len(pid), sercomm_pid.PID_SIZE + 4)

        # Little endian 4 byte integer
        self.assertEqual(pid[-4:], b'\x78\x56\x34\x12')

if __name__ == '__main__':
    unittest.main()
