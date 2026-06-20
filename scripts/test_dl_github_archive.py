import unittest
import os
import fcntl
import importlib.util
from unittest.mock import Mock, patch, mock_open

class TestGitHubCommitTsCacheGet(unittest.TestCase):
import errno
import importlib.util

class TestPathOsFunc(unittest.TestCase):
from unittest.mock import patch, MagicMock
import importlib.util
import os
import sys
from io import StringIO

class TestDlGithubArchive(unittest.TestCase):
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
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    @patch('sys.stderr', new_callable=StringIO)
    def test_main_error_handling(self, mock_stderr):
        with patch('sys.argv', ['dl_github_archive.py', '--source', 'test.tar.gz', '--url', 'http://test.url']):
            with patch.object(self.module, 'DownloadGitHubTarball') as mock_DownloadGitHubTarball:
                mock_instance = mock_DownloadGitHubTarball.return_value
                mock_instance.download.side_effect = Exception("Test Exception")

                with self.assertRaises(SystemExit) as cm:
                    self.module.main()

                self.assertEqual(cm.exception.code, 1)

                stderr_output = mock_stderr.getvalue()
                self.assertIn('test.tar.gz: Download from http://test.url failed', stderr_output)
                self.assertIn('Test Exception', stderr_output)
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
