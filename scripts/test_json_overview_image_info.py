import sys
import os
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json
import shutil

class TestJsonOverviewImageInfo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir_obj = tempfile.TemporaryDirectory()
        cls.test_dir = Path(cls.test_dir_obj.name)
        cls.output_file = cls.test_dir / "output.json"

        cls.orig_argv = sys.argv
        sys.argv = ["json_overview_image_info.py", str(cls.output_file)]

        cls.orig_environ = dict(os.environ)
        os.environ["WORK_DIR"] = str(cls.test_dir)

        spec = importlib.util.spec_from_file_location("json_overview", "scripts/json_overview_image_info.py")
        cls.module = importlib.util.module_from_spec(spec)

        with patch('sys.stdout', new=MagicMock()):
            spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        sys.argv = cls.orig_argv
        os.environ.clear()
        os.environ.update(cls.orig_environ)
        cls.test_dir_obj.cleanup()

    def setUp(self):
        self.module.output = {}
        if self.module.output_path.exists():
            self.module.output_path.unlink()
        for f in self.module.output_dir.glob("*"):
            if f.is_file():
                f.unlink()

    def test_get_initial_output_no_existing_file(self):
        image_info = {"version_code": "123", "data": "test"}
        result = self.module.get_initial_output(image_info)
        self.assertEqual(result, image_info)

    def test_get_initial_output_existing_file_matching_version(self):
        profiles = {"version_code": "123", "profiles": {"test": {}}}
        self.module.output_path.write_text(json.dumps(profiles))

        image_info = {"version_code": "123", "data": "test"}
        result = self.module.get_initial_output(image_info)
        self.assertEqual(result, profiles)

    def test_get_initial_output_existing_file_different_version(self):
        profiles = {"version_code": "456", "profiles": {"test": {}}}
        self.module.output_path.write_text(json.dumps(profiles))

        image_info = {"version_code": "123", "data": "test"}
        result = self.module.get_initial_output(image_info)
        self.assertEqual(result, image_info)

    def test_add_artifact(self):
        artifact_name1 = "openwrt-imagebuilder-22.03-Linux-x86_64.tar.xz"
        artifact_name2 = "openwrt-imagebuilder-22.03-Linux-aarch64.tar.xz"

        (self.module.output_dir / artifact_name1).touch()
        (self.module.output_dir / artifact_name2).touch()

        self.module.add_artifact("imagebuilder")

        self.assertIn("imagebuilder", self.module.output)
        self.assertIn("x86_64", self.module.output["imagebuilder"])
        self.assertIn("aarch64", self.module.output["imagebuilder"])
        self.assertEqual(self.module.output["imagebuilder"]["x86_64"], artifact_name1)
        self.assertEqual(self.module.output["imagebuilder"]["aarch64"], artifact_name2)

    def test_add_artifact_no_prefix(self):
        artifact_name = "llvm-bpf-15.0-Linux-x86_64.tar.xz"
        (self.module.output_dir / artifact_name).touch()

        self.module.add_artifact("llvm-bpf", prefix="")

        self.assertIn("llvm-bpf", self.module.output)
        self.assertIn("x86_64", self.module.output["llvm-bpf"])
        self.assertEqual(self.module.output["llvm-bpf"]["x86_64"], artifact_name)

    def test_add_artifact_no_match(self):
        self.module.add_artifact("sdk")
        self.assertNotIn("sdk", self.module.output)

if __name__ == '__main__':
    unittest.main()
