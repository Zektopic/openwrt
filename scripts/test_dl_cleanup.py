import unittest
import os
import shutil
import sys

# Ensure the script directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_cleanup import Entry

class TestEntry(unittest.TestCase):
    def setUp(self):
        self.mock_dir = "mock_dl_test_dir"
        os.makedirs(self.mock_dir, exist_ok=True)
        # We must create physical files so Entry __init__ won't crash when it checks os.path.isdir() or os.stat() for GIT dates

    def tearDown(self):
        shutil.rmtree(self.mock_dir)

    def _create_file(self, filename):
        path = os.path.join(self.mock_dir, filename)
        with open(path, 'w') as f:
            f.write("mock")
        return path

    def test_version_ge_1234(self):
        self._create_file("pkg-1.2.3.4.tar.gz")
        self._create_file("pkg-1.2.3.3.tar.gz")

        e1 = Entry(self.mock_dir, "build_dir", "pkg-1.2.3.4.tar.gz", is_dir=False)
        e2 = Entry(self.mock_dir, "build_dir", "pkg-1.2.3.3.tar.gz", is_dir=False)
        e3 = Entry(self.mock_dir, "build_dir", "pkg-1.2.3.4.tar.gz", is_dir=False)

        self.assertTrue(e1 >= e2)
        self.assertFalse(e2 >= e1)

        # Test equality
        self.assertTrue(e1 >= e3)
        self.assertTrue(e3 >= e1)

    def test_version_ge_123(self):
        self._create_file("pkg-1.2.3a.tar.gz")
        self._create_file("pkg-1.2.3.tar.gz")
        self._create_file("pkg-1.2.3b.tar.gz")

        e_a = Entry(self.mock_dir, "build_dir", "pkg-1.2.3a.tar.gz", is_dir=False)
        e_none = Entry(self.mock_dir, "build_dir", "pkg-1.2.3.tar.gz", is_dir=False)
        e_b = Entry(self.mock_dir, "build_dir", "pkg-1.2.3b.tar.gz", is_dir=False)

        self.assertTrue(e_a >= e_none)
        self.assertFalse(e_none >= e_a)

        self.assertTrue(e_b >= e_a)
        self.assertFalse(e_a >= e_b)

        # Test equality
        e_a_2 = Entry(self.mock_dir, "build_dir", "pkg-1.2.3a.tar.gz", is_dir=False)
        self.assertTrue(e_a >= e_a_2)

    def test_version_ge_12(self):
        self._create_file("pkg-1.2a.tar.gz")
        self._create_file("pkg-1.2.tar.gz")

        e_a = Entry(self.mock_dir, "build_dir", "pkg-1.2a.tar.gz", is_dir=False)
        e_none = Entry(self.mock_dir, "build_dir", "pkg-1.2.tar.gz", is_dir=False)

        self.assertTrue(e_a >= e_none)
        self.assertFalse(e_none >= e_a)

        e_a_2 = Entry(self.mock_dir, "build_dir", "pkg-1.2a.tar.gz", is_dir=False)
        self.assertTrue(e_a >= e_a_2)

    def test_version_mixed(self):
        self._create_file("pkg-2.0.0.tar.gz")
        self._create_file("pkg-1.2.3.4.tar.gz")

        e_2 = Entry(self.mock_dir, "build_dir", "pkg-2.0.0.tar.gz", is_dir=False)
        e_1 = Entry(self.mock_dir, "build_dir", "pkg-1.2.3.4.tar.gz", is_dir=False)

        self.assertTrue(e_2 >= e_1)
        self.assertFalse(e_1 >= e_2)

if __name__ == '__main__':
    unittest.main()
