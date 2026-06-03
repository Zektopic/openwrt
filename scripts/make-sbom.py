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

        # Extract values directly to avoid creating intermediate objects
        p_idx = text.find("Package: ", start, end)
        if p_idx == start or (p_idx > start and text[p_idx-1] == '\n'):
            p_end = text.find("\n", p_idx, end)
            name = text[p_idx+9:p_end if p_end != -1 else end].strip()
        else:
            name = None

        v_idx = text.find("\nVersion: ", start, end)
        if v_idx != -1:
            v_end = text.find("\n", v_idx + 1, end)
            version = text[v_idx+10:v_end if v_end != -1 else end].strip()
        else:
            if start == 0 and text.startswith("Version: "):
                v_end = text.find("\n", 0, end)
                version = text[9:v_end if v_end != -1 else end].strip()
            else:
                version = None

        cpe_idx = text.find("\nCPE-ID: ", start, end)
        if cpe_idx != -1:
            cpe_end = text.find("\n", cpe_idx + 1, end)
            cpe = text[cpe_idx+9:cpe_end if cpe_end != -1 else end].strip()
        else:
            if start == 0 and text.startswith("CPE-ID: "):
                cpe_end = text.find("\n", 0, end)
                cpe = text[8:cpe_end if cpe_end != -1 else end].strip()
            else:
                cpe = None

        sec_idx = text.find("\nSection: ", start, end)
        if sec_idx != -1:
            sec_end = text.find("\n", sec_idx + 1, end)
            section = text[sec_idx+10:sec_end if sec_end != -1 else end].strip()
        else:
            if start == 0 and text.startswith("Section: "):
                sec_end = text.find("\n", 0, end)
                section = text[9:sec_end if sec_end != -1 else end].strip()
            else:
                section = None

        lic_idx = text.find("\nLicense: ", start, end)
        if lic_idx != -1:
            lic_end = text.find("\n", lic_idx + 1, end)
            license_val = text[lic_idx+10:lic_end if lic_end != -1 else end].strip()
        else:
            if start == 0 and text.startswith("License: "):
                lic_end = text.find("\n", 0, end)
                license_val = text[9:lic_end if lic_end != -1 else end].strip()
            else:
                license_val = None

        start = end + 2
        while start < text_len and text[start] == '\n':
            start += 1

        element: dict = {}
        if name:
            element.update({"name": name})
            if installed and name not in installed:
                continue

        if version:
            element.update({"version": version})

        if cpe:
            element.update({"cpe": cpe})

        if section:
            type_category: str = ''
            if type_allowed.get(section):
                type_category = type_allowed.get(section)
            if type_category:
                element.update({"type": type_category})
            else:
                element.update({"type": "application"})

        if license_val:
            licenses: list = []
            for license in license_val.split():
                licenses.append({"license": {"name": license}})
            element.update({"licenses": licenses})

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
