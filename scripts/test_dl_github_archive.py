import unittest
from unittest.mock import patch, MagicMock
import os
import errno
import importlib.util

spec = importlib.util.spec_from_file_location("dl_github_archive", "scripts/dl_github_archive.py")
dl_github_archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dl_github_archive)

class TestDownloadGitHubTarballHasSubmodule(unittest.TestCase):
    def setUp(self):
        class DummyArgs:
            pass
        self.args = DummyArgs()
        self.args.dl_dir = '/tmp'
        self.args.url = 'https://github.com/owner/repo'
        self.args.subdir = 'repo-1.0'
        self.args.version = '1.0'
        self.args.source = 'repo-1.0.tar.gz'
        self.args.hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' # Valid SHA256 format
        self.args.submodules = []

        self.instance = dl_github_archive.DownloadGitHubTarball(self.args)

    @patch('os.stat')
    def test_has_submodule_exists_and_not_empty(self, mock_stat):
        mock_st = MagicMock()
        mock_st.st_size = 10
        mock_stat.return_value = mock_st
        self.assertTrue(self.instance._has_submodule('/some/dir'))

    @patch('os.stat')
    def test_has_submodule_exists_and_empty(self, mock_stat):
        mock_st = MagicMock()
        mock_st.st_size = 0
        mock_stat.return_value = mock_st
        self.assertFalse(self.instance._has_submodule('/some/dir'))

    @patch('os.stat')
    def test_has_submodule_not_exists(self, mock_stat):
        mock_stat.side_effect = OSError(errno.ENOENT, 'No such file or directory')
        self.assertFalse(self.instance._has_submodule('/some/dir'))

    @patch('os.stat')
    def test_has_submodule_other_oserror(self, mock_stat):
        mock_stat.side_effect = OSError(errno.EACCES, 'Permission denied')
        self.assertTrue(self.instance._has_submodule('/some/dir'))

if __name__ == '__main__':
    unittest.main()
