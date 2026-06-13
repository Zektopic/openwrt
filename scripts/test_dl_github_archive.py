import unittest
import os
import errno
import importlib.util

class TestPathOsFunc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_github_archive.py')
        spec = importlib.util.spec_from_file_location("dl_github_archive", script_path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.Path = cls.module.Path

    def test_success(self):
        func = lambda path: f"success {path}"
        result = self.Path._os_func(func, "test/path", errno.ENOENT, default="default")
        self.assertEqual(result, "success test/path")

    def test_oserror_matching_errno(self):
        def func(path):
            e = OSError("mock error")
            e.errno = errno.ENOENT
            raise e

        result = self.Path._os_func(func, "test/path", errno.ENOENT, default="mock_default")
        self.assertEqual(result, "mock_default")

    def test_oserror_different_errno(self):
        def func(path):
            e = OSError("mock error")
            e.errno = errno.EACCES
            raise e

        with self.assertRaises(OSError) as cm:
            self.Path._os_func(func, "test/path", errno.ENOENT, default="mock_default")

        self.assertEqual(cm.exception.errno, errno.EACCES)

    def test_other_exception(self):
        def func(path):
            raise ValueError("other error")

        with self.assertRaises(ValueError):
            self.Path._os_func(func, "test/path", errno.ENOENT)

if __name__ == '__main__':
    unittest.main()
