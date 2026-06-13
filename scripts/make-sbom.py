#!/usr/bin/env python3
"""
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Parse the native package index files into a json file for use by
# downstream tools.
#
"""

import datetime
import json
import uuid


def parse_args():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    # fmt: off

    parser.add_argument(dest="source",
                        help="File name for input, '-' for stdin")
    parser.add_argument("-f", "--source-format", required=True,
                        choices=['apk', 'opkg'],
                        help=("Required source format of"
                              " input: 'apk' or 'opkg'"))
    parser.add_argument("-m", "--manifest",
                        help=("File includes the packages to"
                              " be included in the output"))

    # fmt: on
    args = parser.parse_args()
    return args


def get_apk_sbom(text: str, installed: set) -> list:
    packages: dict = json.loads(text)
    components: list = []

    type_allowed: dict = {
        "kernel": "operating-system",
        "firmware": "firmware",
        "libs": "library"
    }

    for package in packages["packages"]:
        element: dict = {}

        # required
        if 'name' in package:
            name: str = package['name']
            element.update({"name": name})
            if installed:
                if name not in installed:
                    continue

        if 'version' in package:
            element.update({"version": package["version"]})

        for tag in package.get("tags", []):
            if tag.startswith("openwrt:cpe="):
                cpe: str = tag.split("=")[-1]
                element.update({"cpe": cpe})

        # required
        type_category: str = ''

        for tag in package.get("tags", []):
            if tag.startswith("openwrt:section="):
                category: str = tag.split("=")[-1]
                if type_allowed.get(category):
                    type_category = type_allowed.get(category)
        if type_category:
            element.update({"type": type_category})
        else:
            element.update({"type": "application"})

        if 'license' in package:
            licenses: list = []
            for license in package["license"].split():
                licenses.append({"license": {"name": license}})
            element.update({"licenses": licenses})

        components.append(element)

    return components


def get_opkg_sbom(text: str, installed: set) -> list:
    components: list = []

    type_allowed: dict = {
        "kernel": "operating-system",
        "firmware": "firmware",
        "libs": "library"
    }

    # Optimization: use string find to locate chunks instead of splitting the entire text
    # on "\n\n" at once. This avoids allocating a massive intermediate list of strings
    # while preserving exact dictionary-based parsing for robustness.
    start = 0
    text_len = len(text)

    while start < text_len:
        end = text.find("\n\n", start)
        if end == -1:
            end = text_len

        element: dict = {}

        name_idx = text.find("\nPackage: ", max(0, start - 1), end)
        name_found = False
        if name_idx != -1:
            name_idx += 10
            name_found = True
        elif text.startswith("Package: ", start):
            name_idx = start + 9
            name_found = True
        if name_found:
            name_end = text.find("\n", name_idx)
            if name_end == -1 or name_end > end: name_end = end
            name = text[name_idx:name_end].strip()
            element.update({"name": name})
            if installed and name not in installed:
                # Move to next block
                start = end + 2
                while start < text_len and text[start] == '\n':
                    start += 1
                continue

        ver_idx = text.find("\nVersion: ", max(0, start - 1), end)
        ver_found = False
        if ver_idx != -1:
            ver_idx += 10
            ver_found = True
        elif text.startswith("Version: ", start):
            ver_idx = start + 9
            ver_found = True
        if ver_found:
            ver_end = text.find("\n", ver_idx)
            if ver_end == -1 or ver_end > end: ver_end = end
            element.update({"version": text[ver_idx:ver_end].strip()})

        cpe_idx = text.find("\nCPE-ID: ", max(0, start - 1), end)
        cpe_found = False
        if cpe_idx != -1:
            cpe_idx += 9
            cpe_found = True
        elif text.startswith("CPE-ID: ", start):
            cpe_idx = start + 8
            cpe_found = True
        if cpe_found:
            cpe_end = text.find("\n", cpe_idx)
            if cpe_end == -1 or cpe_end > end: cpe_end = end
            element.update({"cpe": text[cpe_idx:cpe_end].strip()})

        sec_idx = text.find("\nSection: ", max(0, start - 1), end)
        sec_found = False
        if sec_idx != -1:
            sec_idx += 10
            sec_found = True
        elif text.startswith("Section: ", start):
            sec_idx = start + 9
            sec_found = True
        if sec_found:
            sec_end = text.find("\n", sec_idx)
            if sec_end == -1 or sec_end > end: sec_end = end
            section = text[sec_idx:sec_end].strip()
            type_category: str = ''
            if type_allowed.get(section):
                type_category = type_allowed.get(section)
            if type_category:
                element.update({"type": type_category})
            else:
                element.update({"type": "application"})

        lic_idx = text.find("\nLicense: ", max(0, start - 1), end)
        lic_found = False
        if lic_idx != -1:
            lic_idx += 10
            lic_found = True
        elif text.startswith("License: ", start):
            lic_idx = start + 9
            lic_found = True
        if lic_found:
            lic_end = text.find("\n", lic_idx)
            if lic_end == -1 or lic_end > end: lic_end = end
            licenses: list = []
            for license in text[lic_idx:lic_end].strip().split():
                licenses.append({"license": {"name": license}})
            element.update({"licenses": licenses})

        start = end + 2
        while start < text_len and text[start] == '\n':
            start += 1

        if element:
            components.append(element)

    return components


if __name__ == "__main__":
    import sys

    args = parse_args()

    input = sys.stdin if args.source == "-" else open(args.source, "r")
    with input:
        text: str = input.read()

    # Read manifest file (installed packages)
    packages: set = set()
    if args.manifest:
        with open(args.manifest, 'r') as file:
            for line in file:
                packages.add(line.split(' - ')[0].strip())

    components: list = []
    if args.source_format == "apk":
        components = get_apk_sbom(text, packages)
    elif args.source_format == "opkg":
        components = get_opkg_sbom(text, packages)
    else:
        print("Source format unknown")
        raise SystemExit

    timestamp: str = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cyclonedx: dict = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "serialNumber": "urn:uuid:" + str(uuid.uuid4()),
        "version": "1",
        "metadata": {
            "timestamp": timestamp,
        },
        "components": components,
    }

    print(json.dumps(cyclonedx, indent=2))
