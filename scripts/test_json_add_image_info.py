import unittest
from unittest import mock
import os
import importlib.util
import tempfile

class TestJsonAddImageInfo(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.dummy_file = os.path.join(self.test_dir.name, "dummy.bin")
        self.output_json = os.path.join(self.test_dir.name, "out.json")
        with open(self.dummy_file, "wb") as f:
            f.write(b"dummy")

        self.env_patcher = mock.patch.dict(os.environ, {
            "FILE_DIR": self.test_dir.name,
            "FILE_NAME": "dummy.bin",
            "TARGET": "target",
            "SUBTARGET": "subtarget",
            "VERSION_CODE": "1.0",
            "VERSION_NUMBER": "1",
            "SOURCE_DATE_EPOCH": "1234567890",
            "DEVICE_ID": "dev1",
            "DEVICE_IMG_PREFIX": "img_",
            "FILE_TYPE": "sysupgrade",
            "DEVICE_PACKAGES": "pkg1 pkg2",
            "SUPPORTED_DEVICES": "dev1 dev2"
        })
        self.env_patcher.start()
        self.argv_patcher = mock.patch('sys.argv', ['script.py', self.output_json])
        self.argv_patcher.start()

        spec = importlib.util.spec_from_file_location("json_add_image_info", "scripts/json_add_image_info.py")
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def tearDown(self):
        self.env_patcher.stop()
        self.argv_patcher.stop()
        self.test_dir.cleanup()

    def test_get_titles_default(self):
        with mock.patch.dict(os.environ, {"DEVICE_TITLE": "My Device"}):
            titles = self.mod.get_titles()
            self.assertEqual(len(titles), 1)
            self.assertEqual(titles[0]["title"], "My Device")

    def test_get_titles_vendor_model_variant(self):
        with mock.patch.dict(os.environ, {
            "DEVICE_VENDOR": "MyVendor",
            "DEVICE_MODEL": "MyModel",
            "DEVICE_VARIANT": "MyVariant"
        }):
            titles = self.mod.get_titles()
            self.assertEqual(len(titles), 1)
            self.assertEqual(titles[0]["vendor"], "MyVendor")
            self.assertEqual(titles[0]["model"], "MyModel")
            self.assertEqual(titles[0]["variant"], "MyVariant")

    def test_get_titles_multiple_alts(self):
        with mock.patch.dict(os.environ, {
            "DEVICE_VENDOR": "MyVendor",
            "DEVICE_MODEL": "MyModel",
            "DEVICE_ALT0_VENDOR": "Alt0Vendor",
            "DEVICE_ALT0_MODEL": "Alt0Model",
            "DEVICE_ALT2_VENDOR": "Alt2Vendor",
            "DEVICE_ALT2_MODEL": "Alt2Model"
        }):
            titles = self.mod.get_titles()
            self.assertEqual(len(titles), 3)
            self.assertEqual(titles[0]["vendor"], "MyVendor")
            self.assertEqual(titles[0]["model"], "MyModel")
            self.assertEqual(titles[1]["vendor"], "Alt0Vendor")
            self.assertEqual(titles[1]["model"], "Alt0Model")
            self.assertEqual(titles[2]["vendor"], "Alt2Vendor")
            self.assertEqual(titles[2]["model"], "Alt2Model")

    def test_get_numerical_size(self):
        self.assertEqual(self.mod.get_numerical_size("10g"), 10 * 1024 * 1024 * 1024)
        self.assertEqual(self.mod.get_numerical_size("5m"), 5 * 1024 * 1024)
        self.assertEqual(self.mod.get_numerical_size("2k"), 2 * 1024)
        self.assertEqual(self.mod.get_numerical_size("1024"), 1024)
        self.assertEqual(self.mod.get_numerical_size("0"), 0)

if __name__ == "__main__":
    unittest.main()
