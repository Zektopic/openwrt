import unittest
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
