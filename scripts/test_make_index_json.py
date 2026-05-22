import importlib.util
import sys
import unittest
import json

# Import the script with hyphens
spec = importlib.util.spec_from_file_location("make_index_json", "scripts/make-index-json.py")
make_index_json = importlib.util.module_from_spec(spec)
sys.modules["make_index_json"] = make_index_json
spec.loader.exec_module(make_index_json)

class TestMakeIndexJson(unittest.TestCase):
    def test_parse_apk_array(self):
        # Format from apk query (JSON array)
        data = [
            {
                "name": "base-files",
                "version": "1.2-r3"
            },
            {
                "name": "libssl1.1",
                "version": "1.1.1-r1",
                "tags": ["openwrt:abiversion=1.1"]
            },
            {
                "name": "libc",
                "version": "1.2.3",
                "tags": ["other-tag"]
            }
        ]
        text = json.dumps(data)
        result = make_index_json.parse_apk(text)
        self.assertEqual(result, {
            "base-files": "1.2-r3",
            "libssl": "1.1.1-r1",
            "libc": "1.2.3"
        })

    def test_parse_apk_dict(self):
        # Format from apk adbdump (JSON dict with 'packages' key)
        data = {
            "packages": [
                {
                    "name": "test-pkg",
                    "version": "1.0-r1"
                }
            ]
        }
        text = json.dumps(data)
        result = make_index_json.parse_apk(text)
        self.assertEqual(result, {
            "test-pkg": "1.0-r1"
        })

    def test_parse_apk_empty(self):
        text = json.dumps([])
        result = make_index_json.parse_apk(text)
        self.assertEqual(result, {})

        text2 = json.dumps({"packages": []})
        result2 = make_index_json.parse_apk(text2)
        self.assertEqual(result2, {})

    def test_parse_opkg(self):
        text = """Package: base-files
Version: 1.2-r3
Depends: libc

Package: libssl1.1
Version: 1.1.1-r1
ABIVersion: 1.1

Package: libc
Version: 1.2.3
"""
        result = make_index_json.parse_opkg(text)
        self.assertEqual(result, {
            "base-files": "1.2-r3",
            "libssl": "1.1.1-r1",
            "libc": "1.2.3"
        })

if __name__ == '__main__':
    unittest.main()
