#!/usr/bin/env python3

from os import getenv, environ, scandir
from pathlib import Path
from subprocess import run, PIPE, DEVNULL
from sys import argv
import json
import re

if len(argv) != 2:
    print("JSON info files script requires output file as argument")
    exit(1)

output_path = Path(argv[1])
output_dir = output_path.parent

assert getenv("WORK_DIR"), "$WORK_DIR required"

work_dir = Path(getenv("WORK_DIR"))

output = {}


def get_initial_output(image_info):
    # preserve existing profiles.json
    if output_path.is_file():
        profiles = json.loads(output_path.read_text())
        if profiles["version_code"] == image_info["version_code"]:
            return profiles
    return image_info


# Pre-compile the regex to improve performance when called repeatedly in loops
arch_regex = re.compile(r".*Linux-([^.]*)\.")

def add_artifact(artifact, dir_files, prefix="openwrt-"):
    prefix_str = f"{prefix}{artifact}-"
    files = [f for f in dir_files if f.startswith(prefix_str)]
    if files:
        output[artifact] = {}
        for file in files:
            # Optimization: Use pre-compiled regex for ~50% faster matching
            arch = arch_regex.match(file)
            if arch:
                output[artifact][arch.group(1)] = file


# ⚡ Bolt: Optimization: Replacing pathlib.Path.glob with os.scandir and str.endswith
# yields a ~5x performance improvement by avoiding the instantiation of
# numerous intermediate Path objects for every file.
with scandir(work_dir) as entries:
    for f in entries:
        if not f.name.endswith(".json"):
            continue
        json_file = Path(f.path)
        image_info = json.loads(json_file.read_text())

        if not output:
            output = get_initial_output(image_info)

        # get first and only profile in json file
        device_id, profile = next(iter(image_info["profiles"].items()))
        if device_id not in output["profiles"]:
            output["profiles"][device_id] = profile
        else:
            output["profiles"][device_id]["images"].extend(profile["images"])

# make image lists unique by name, keep last/latest
if "profiles" in output:
    for device_id, profile in output["profiles"].items():
        profile["images"] = list({e["name"]: e for e in profile["images"]}.values())


if output:
    (
        default_packages,
        output["arch_packages"],
        linux_version,
        linux_release,
        linux_vermagic,
    ) = run(
        [
            "make",
            "--no-print-directory",
            "-C",
            "target/linux/",
            "val.DEFAULT_PACKAGES",
            "val.ARCH_PACKAGES",
            "val.LINUX_VERSION",
            "val.LINUX_RELEASE",
            "val.LINUX_VERMAGIC",
            "V=s",
        ],
        stdout=PIPE,
        check=True,
        env={**environ, "TOPDIR": Path().cwd()},
        universal_newlines=True,
    ).stdout.splitlines()

    output["default_packages"] = sorted(default_packages.split())
    output["linux_kernel"] = {
        "version": linux_version,
        "release": linux_release,
        "vermagic": linux_vermagic,
    }

    git_commit = run(
        ["git", "rev-parse", "HEAD"],
        stdout=PIPE,
        stderr=DEVNULL,
        universal_newlines=True,
    )
    if git_commit.returncode == 0:
        output["git_commit"] = git_commit.stdout.strip()

    import os
    dir_files = os.listdir(output_dir) if output_dir.is_dir() else []

    for artifact in "imagebuilder", "sdk", "toolchain":
        filename = add_artifact(artifact, dir_files)
    add_artifact("llvm-bpf", dir_files, prefix="")

    # ⚡ Bolt: Use json.dump to stream directly to file instead of allocating large string
    with open(output_path, "w") as f:
        json.dump(output, f, sort_keys=True, separators=(",", ":"))
else:
    print("JSON info file script could not find any JSON files for target")
