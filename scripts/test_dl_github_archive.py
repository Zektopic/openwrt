import unittest
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

if __name__ == '__main__':
    unittest.main()
