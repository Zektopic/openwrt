import unittest
import re
import sys
import os
import importlib.util
from unittest.mock import Mock

class TestDlCleanupParseVerYmdGitShasum(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the module using importlib to handle any script execution environment cleanly
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_cleanup.py')
        spec = importlib.util.spec_from_file_location("dl_cleanup", script_path)
        cls.dl_cleanup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.dl_cleanup)

    def setUp(self):
        # Extract the specific regex used for parseVer_ymd_GIT_SHASUM
        self.regex = None
        for regex, func in self.dl_cleanup.versionRegex:
            if func.__name__ == 'parseVer_ymd_GIT_SHASUM':
                self.regex = regex
                break
        self.assertIsNotNone(self.regex, "Regex for parseVer_ymd_GIT_SHASUM not found")

    def test_valid_format_with_hyphens(self):
        """Test extraction with standard YYYY-MM-DD format."""
        filename = "openwrt-package-2023-10-25-abcdef1234567890"
        match = self.regex.search(filename)
        self.assertIsNotNone(match)

        progname, progversion = self.dl_cleanup.parseVer_ymd_GIT_SHASUM(match, filename)

        self.assertEqual(progname, "openwrt-package")
        expected_version = (2023 << 64) | (10 << 48) | (25 << 32)
        self.assertEqual(progversion, expected_version)

    def test_valid_format_without_hyphens(self):
        """Test extraction with YYYYMMDD format without internal hyphens."""
        filename = "another_pkg_20231025-abcdef"
        match = self.regex.search(filename)
        self.assertIsNotNone(match)

        progname, progversion = self.dl_cleanup.parseVer_ymd_GIT_SHASUM(match, filename)

        self.assertEqual(progname, "another_pkg")
        expected_version = (2023 << 64) | (10 << 48) | (25 << 32)
        self.assertEqual(progversion, expected_version)

    def test_malformed_string_regex_rejection(self):
        """Test that malformed version strings do not match the regex, gracefully bypassing."""
        # Non-numeric year
        self.assertIsNone(self.regex.search("pkg-YYYY-10-25-abcdef"))
        # Invalid month length
        self.assertIsNone(self.regex.search("pkg-2023-1-25-abcdef"))
        # Missing trailing hyphen before the SHASUM component (required by regex '(\d\d)-')
        self.assertIsNone(self.regex.search("pkg-2023-10-25"))

    def test_malformed_match_object_value_error(self):
        """Test parseVer_ymd_GIT_SHASUM gracefully fails if group contains non-int data."""
        mock_match = Mock()
        # group(1) = progname, group(2) = year, group(3) = month, group(4) = day
        mock_match.group.side_effect = lambda idx: {1: "pkg", 2: "notint", 3: "10", 4: "25"}[idx]

        with self.assertRaises(ValueError):
            self.dl_cleanup.parseVer_ymd_GIT_SHASUM(mock_match, "dummy_path")

    def test_malformed_match_object_index_error(self):
        """Test parseVer_ymd_GIT_SHASUM gracefully fails if match has missing groups."""
        mock_match = Mock()
        def side_effect(idx):
            if idx > 2:
                raise IndexError("No such group")
            return {1: "pkg", 2: "2023"}[idx]
        mock_match.group.side_effect = side_effect

        with self.assertRaises(IndexError):
            self.dl_cleanup.parseVer_ymd_GIT_SHASUM(mock_match, "dummy_path")


class TestDlCleanupParseVer12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_cleanup.py')
        spec = importlib.util.spec_from_file_location("dl_cleanup", script_path)
        cls.dl_cleanup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.dl_cleanup)

    def test_parseVer_12_index_error_on_patchlevel(self):
        """Test parseVer_12 exception handling when group(4) raises IndexError."""
        mock_match = Mock()
        def side_effect(idx):
            if idx == 4:
                raise IndexError("No such group")
            return {1: "prog", 2: "1", 3: "2"}[idx]
        mock_match.group.side_effect = side_effect

        progname, progversion = self.dl_cleanup.parseVer_12(mock_match, "dummy_path")

        self.assertEqual(progname, "prog")
        expected_version = (1 << 64) | (2 << 48) | 0
        self.assertEqual(progversion, expected_version)

class TestDlCleanupParseVer123(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_cleanup.py')
        spec = importlib.util.spec_from_file_location("dl_cleanup", script_path)
        cls.dl_cleanup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.dl_cleanup)

    def test_parseVer_123_index_error_on_patchlevel(self):
        """Test parseVer_123 exception handling when group(5) raises IndexError."""
    def test_missing_patchlevel_index_error(self):
        """Test parseVer_123 gracefully handles IndexError when match group 5 is missing."""
        mock_match = Mock()
        def side_effect(idx):
            if idx == 5:
                raise IndexError("No such group")
            return {1: "prog", 2: "1", 3: "2", 4: "3"}[idx]
            return {1: "pkg", 2: "1", 3: "2", 4: "3"}[idx]
        mock_match.group.side_effect = side_effect

        progname, progversion = self.dl_cleanup.parseVer_123(mock_match, "dummy_path")

        self.assertEqual(progname, "prog")
        self.assertEqual(progname, "pkg")
        expected_version = (1 << 64) | (2 << 48) | (3 << 32) | 0
        self.assertEqual(progversion, expected_version)


class TestDlCleanupParseVer1234(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_cleanup.py')
        spec = importlib.util.spec_from_file_location('dl_cleanup', script_path)
        cls.dl_cleanup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.dl_cleanup)

    def setUp(self):
        self.regex = None
        for regex, func in self.dl_cleanup.versionRegex:
            if func.__name__ == 'parseVer_1234':
                self.regex = regex
                break
        self.assertIsNotNone(self.regex, 'Regex for parseVer_1234 not found')

    def test_valid_format_with_hyphens(self):
        filename = 'some-package-1.2.3.4'
        match = self.regex.search(filename)
        self.assertIsNotNone(match)

        progname, progversion = self.dl_cleanup.parseVer_1234(match, filename)

        self.assertEqual(progname, 'some-package')
        expected_version = (1 << 64) | (2 << 48) | (3 << 32) | (4 << 16)
        self.assertEqual(progversion, expected_version)

    def test_valid_format_with_underscores(self):
        filename = 'another_pkg_5.6.7.8'
        match = self.regex.search(filename)
        self.assertIsNotNone(match)

        progname, progversion = self.dl_cleanup.parseVer_1234(match, filename)

        self.assertEqual(progname, 'another_pkg')
        expected_version = (5 << 64) | (6 << 48) | (7 << 32) | (8 << 16)
        self.assertEqual(progversion, expected_version)

    def test_malformed_match_object_value_error(self):
        mock_match = Mock()
        mock_match.group.side_effect = lambda idx: {1: 'pkg', 2: 'notint', 3: '2', 4: '3', 5: '4'}[idx]

        with self.assertRaises(ValueError):
            self.dl_cleanup.parseVer_1234(mock_match, 'dummy_path')

    def test_malformed_match_object_index_error(self):
        mock_match = Mock()
        def side_effect(idx):
            if idx > 3:
                raise IndexError('No such group')
            return {1: 'pkg', 2: '1', 3: '2'}[idx]
        mock_match.group.side_effect = side_effect

        with self.assertRaises(IndexError):
            self.dl_cleanup.parseVer_1234(mock_match, 'dummy_path')

if __name__ == '__main__':
    unittest.main()
