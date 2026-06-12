import importlib.util
import sys
import unittest
import json

# Import the script with hyphens
spec = importlib.util.spec_from_file_location("make_sbom", "scripts/make-sbom.py")
make_sbom = importlib.util.module_from_spec(spec)
sys.modules["make_sbom"] = make_sbom
spec.loader.exec_module(make_sbom)

class TestMakeSbom(unittest.TestCase):
    def test_get_apk_sbom_basic(self):
        data = {
            "packages": [
                {
                    "name": "base-files",
                    "version": "1.2-r3",
                    "tags": ["openwrt:cpe=cpe:/a:openwrt:base-files", "openwrt:section=base"],
                    "license": "GPL-2.0-only MIT"
                }
            ]
        }
        text = json.dumps(data)
        result = make_sbom.get_apk_sbom(text, set())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "base-files")
        self.assertEqual(result[0]["version"], "1.2-r3")
        self.assertEqual(result[0]["cpe"], "cpe:/a:openwrt:base-files")
        self.assertEqual(result[0]["type"], "application")
        self.assertEqual(result[0]["licenses"], [
            {"license": {"name": "GPL-2.0-only"}},
            {"license": {"name": "MIT"}}
        ])

    def test_get_apk_sbom_types(self):
        data = {
            "packages": [
                {"name": "p1", "tags": ["openwrt:section=kernel"]},
                {"name": "p2", "tags": ["openwrt:section=firmware"]},
                {"name": "p3", "tags": ["openwrt:section=libs"]},
                {"name": "p4", "tags": ["openwrt:section=unknown"]},
                {"name": "p5"}
            ]
        }
        text = json.dumps(data)
        result = make_sbom.get_apk_sbom(text, set())
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["type"], "operating-system")
        self.assertEqual(result[1]["type"], "firmware")
        self.assertEqual(result[2]["type"], "library")
        self.assertEqual(result[3]["type"], "application")
        self.assertEqual(result[4]["type"], "application")

    def test_get_apk_sbom_installed_filter(self):
        data = {
            "packages": [
                {"name": "p1", "version": "1.0"},
                {"name": "p2", "version": "2.0"}
            ]
        }
        text = json.dumps(data)

        # Test with installed set populated
        result = make_sbom.get_apk_sbom(text, {"p1"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "p1")

        # Test with empty installed set
        result_empty = make_sbom.get_apk_sbom(text, set())
        self.assertEqual(len(result_empty), 2)

    def test_get_apk_sbom_missing_fields(self):
        data = {
            "packages": [
                {
                    "version": "1.0"
                }
            ]
        }
        text = json.dumps(data)
        result = make_sbom.get_apk_sbom(text, set())
        self.assertEqual(len(result), 1)
        self.assertNotIn("name", result[0])
        self.assertEqual(result[0]["version"], "1.0")
        self.assertEqual(result[0]["type"], "application")

if __name__ == '__main__':
    unittest.main()
