import unittest
import sys
import importlib.util
from unittest.mock import patch, MagicMock
import json

def load_module():
    # Setup import mock to avoid the global code executing during import
    with patch("sys.argv", ["json_overview_image_info.py", "output.json"]):
        with patch("os.getenv", side_effect=lambda key: "/tmp" if key == "WORK_DIR" else None):
            with patch("pathlib.Path.glob", return_value=[]):
                with patch("builtins.print"):
                    with patch("subprocess.run"):
                        with patch("pathlib.Path.write_text"):
                            spec = importlib.util.spec_from_file_location("json_overview_image_info", "scripts/json_overview_image_info.py")
                            module = importlib.util.module_from_spec(spec)
                            sys.modules["json_overview_image_info"] = module
                            spec.loader.exec_module(module)
                            return module

json_overview_image_info = load_module()

class TestGetInitialOutput(unittest.TestCase):
    def test_get_initial_output_no_file(self):
        """Test behavior when output_path is not a file"""
        image_info = {"version_code": "1.0", "id": "test_id"}

        # We need to mock the is_file method on the actual output_path instance
        mock_output_path = MagicMock()
        mock_output_path.is_file.return_value = False

        with patch("json_overview_image_info.output_path", mock_output_path):
            result = json_overview_image_info.get_initial_output(image_info)
            self.assertEqual(result, image_info)

    def test_get_initial_output_existing_matching_version(self):
        """Test behavior when file exists and version_code matches"""
        image_info = {"version_code": "1.0", "id": "test_id"}
        existing_profiles = {"version_code": "1.0", "id": "existing_id"}

        mock_output_path = MagicMock()
        mock_output_path.is_file.return_value = True
        mock_output_path.read_text.return_value = json.dumps(existing_profiles)

        with patch("json_overview_image_info.output_path", mock_output_path):
            result = json_overview_image_info.get_initial_output(image_info)
            self.assertEqual(result, existing_profiles)

    def test_get_initial_output_existing_different_version(self):
        """Test behavior when file exists but version_code is different"""
        image_info = {"version_code": "2.0", "id": "test_id"}
        existing_profiles = {"version_code": "1.0", "id": "existing_id"}

        mock_output_path = MagicMock()
        mock_output_path.is_file.return_value = True
        mock_output_path.read_text.return_value = json.dumps(existing_profiles)

        with patch("json_overview_image_info.output_path", mock_output_path):
            result = json_overview_image_info.get_initial_output(image_info)
            self.assertEqual(result, image_info)

if __name__ == '__main__':
    unittest.main()
