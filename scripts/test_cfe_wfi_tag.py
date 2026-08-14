import importlib.util
import os
import unittest
from unittest.mock import patch, MagicMock

# Load the module dynamically
spec = importlib.util.spec_from_file_location("cfe_wfi_tag", "scripts/cfe-wfi-tag.py")
cfe_wfi_tag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfe_wfi_tag)

class TestCfeWfiTag(unittest.TestCase):
    def setUp(self):
        self.args = MagicMock()
        self.args.input_file = "input.bin"
        self.args.output_file = "output.bin"
        self.args.tag_version = 0x5732
        self.args.chip_id = 0x6328
        self.args.flash_type = 1
        self.args.flags = 0

    @patch("shutil.copyfile")
    @patch("builtins.open")
    def test_create_output_ioerror(self, mock_open, mock_copyfile):
        mock_open.side_effect = IOError("Mocked IOError")
        with self.assertRaises(IOError):
            cfe_wfi_tag.create_output(self.args)

    @patch("shutil.copyfile")
    @patch("builtins.open")
    def test_create_output_success(self, mock_open, mock_copyfile):
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.side_effect = [b"dummy data", b""]

        cfe_wfi_tag.create_output(self.args)

        mock_file.read.assert_called()
        mock_file.write.assert_called()

    @patch("shutil.copyfile")
    @patch("builtins.open")
    def test_create_output_same_file(self, mock_open, mock_copyfile):
        self.args.input_file = "same.bin"
        self.args.output_file = "same.bin"

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.side_effect = [b"dummy data", b""]

        cfe_wfi_tag.create_output(self.args)

        mock_copyfile.assert_not_called()

if __name__ == "__main__":
    unittest.main()
