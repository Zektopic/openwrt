import unittest
import os
import fcntl
import importlib.util
from unittest.mock import Mock, patch, mock_open

class TestGitHubCommitTsCacheGet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_github_archive.py')
        spec = importlib.util.spec_from_file_location("dl_github_archive", script_path)
        cls.dl_github_archive = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.dl_github_archive)

    @patch('os.open')
    @patch('os.fdopen')
    @patch('fcntl.lockf')
    def test_get_exception_releases_lock(self, mock_lockf, mock_fdopen, mock_open_os):
        """Test that fcntl.LOCK_UN is called in the finally block if an exception occurs."""
        mock_open_os.return_value = 123 # Dummy fd
        mock_file = Mock()
        # Ensure we return a mock file so `with os.fdopen(fileno) as fin:` works
        mock_fdopen.return_value.__enter__.return_value = mock_file

        cache = self.dl_github_archive.GitHubCommitTsCache()

        # Patch _cache_init to raise an exception
        cache._cache_init = Mock(side_effect=ValueError("Simulated error"))

        # We expect the exception to bubble up
        with self.assertRaises(ValueError):
            cache.get('test-key')

        # lockf should have been called twice, first with LOCK_SH, then with LOCK_UN
        self.assertEqual(mock_lockf.call_count, 2)
        mock_lockf.assert_any_call(123, fcntl.LOCK_SH)
        mock_lockf.assert_any_call(123, fcntl.LOCK_UN)
from unittest.mock import patch, MagicMock
import os
import sys
import importlib.util

class TestDlGithubArchive(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("dl_github_archive", "scripts/dl_github_archive.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    @patch('fcntl.lockf')
    @patch('os.open')
    @patch('os.fdopen')
    def test_cache_get_error_handling(self, mock_fdopen, mock_open, mock_lockf):
        mock_open.return_value = 123
        mock_fin = MagicMock()
        mock_fdopen.return_value.__enter__.return_value = mock_fin

        cache = self.module.GitHubCommitTsCache()
        cache._cache_init = MagicMock(side_effect=RuntimeError("test error"))

        with self.assertRaises(RuntimeError):
            cache.get('test_key')

        mock_lockf.assert_any_call(123, self.module.fcntl.LOCK_UN)

    @patch('fcntl.lockf')
    @patch('os.open')
    @patch('os.fdopen')
    def test_cache_set_error_handling(self, mock_fdopen, mock_open, mock_lockf):
        mock_open.return_value = 123
        mock_fin = MagicMock()
        mock_fdopen.return_value.__enter__.return_value = mock_fin

        cache = self.module.GitHubCommitTsCache()
        cache._cache_init = MagicMock(side_effect=RuntimeError("test error"))

        with self.assertRaises(RuntimeError):
            cache.set('test_key', 12345)

        mock_lockf.assert_any_call(123, self.module.fcntl.LOCK_UN)

if __name__ == '__main__':
    unittest.main()
