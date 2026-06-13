import unittest
import os
import sys
import importlib.util
from unittest.mock import patch, MagicMock, call

class TestDlGithubArchive(unittest.TestCase):
    def setUp(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dl_github_archive.py')
        spec = importlib.util.spec_from_file_location("dl_github_archive", script_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules['dl_github_archive'] = self.module
        spec.loader.exec_module(self.module)

    def tearDown(self):
        if 'dl_github_archive' in sys.modules:
            del sys.modules['dl_github_archive']

    @patch('dl_github_archive.Path.rm_all')
    @patch('dl_github_archive.Path.tar')
    @patch('dl_github_archive.Path.untar')
    @patch('dl_github_archive.os.rename')
    @patch('dl_github_archive.DownloadGitHubTarball._fetch')
    @patch('dl_github_archive.DownloadGitHubTarball._init_commit_ts')
    def test_download_hash_check_exception(self, mock_init_commit_ts, mock_fetch, mock_rename, mock_untar, mock_tar, mock_rm_all):
        # Setup mock args
        args = MagicMock()
        args.dl_dir = '/tmp/dl'
        args.version = 'master'
        args.subdir = 'test-subdir'
        args.source = 'test-source.tar.gz'
        args.submodules = ['skip']
        args.url = 'https://github.com/openwrt/openwrt'
        args.hash = '0' * 64

        mock_untar.return_value = 'test-subdir-prefix'

        instance = self.module.DownloadGitHubTarball(args)

        # We want to trigger the exception in _hash_check
        instance._hash_check = MagicMock(side_effect=Exception("hash check failed"))

        with self.assertRaises(Exception) as context:
            instance.download()

        self.assertEqual(str(context.exception), "hash check failed")

        # Verify Path.rm_all was called with the correct argument
        expected_into = os.path.join(self.module.TMPDIR_DL, args.source)
        self.assertIn(call(expected_into), mock_rm_all.call_args_list)

if __name__ == '__main__':
    unittest.main()
