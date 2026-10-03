#!/usr/bin/env python3
"""Resolve all supported target configurations without changing .config.

Run `make defconfig` first to build Kconfig and generate package metadata.
This checks configuration availability; it does not compile firmware.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="Target/subtarget pairs; default: all")
    parser.add_argument("--output", type=Path, default=Path("logs/target-configs"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    for path in ["scripts/config/conf", "tmp/.config-target.in", "tmp/.config-package.in"]:
        if not (root / path).is_file():
            parser.error("Run make defconfig first (missing %s)" % path)

    targets = subprocess.run(
        ["perl", "scripts/dump-target-info.pl", "targets"], cwd=root,
        check=True, capture_output=True, text=True,
    )
    available = {line.split()[0] for line in targets.stdout.splitlines() if line.strip()}
    selected = sorted(set(args.targets) if args.targets else available)
    if not selected or set(selected) - available:
        parser.error("Unknown targets: %s" % ", ".join(sorted(set(selected) - available)))

    output.mkdir(parents=True, exist_ok=True)
    (output / "target-discovery.log").write_text(targets.stderr)
    results = []
    for pair in selected:
        target, subtarget = pair.split("/")
        config = output / (pair.replace("/", "-") + ".config")
        config.write_text(
            f"CONFIG_TARGET_{target}=y\nCONFIG_TARGET_{target}_{subtarget}=y\n"
            "CONFIG_TARGET_MULTI_PROFILE=y\nCONFIG_TARGET_ALL_PROFILES=y\n"
            "CONFIG_TARGET_PER_DEVICE_ROOTFS=y\n"
        )
        run = subprocess.run(
            ["scripts/config/conf", "--defconfig=" + str(config), "Config.in"],
            cwd=root, env=dict(os.environ, KCONFIG_CONFIG=str(config), TOPDIR=str(root)),
            capture_output=True, text=True,
        )
        config.with_suffix(".log").write_text(run.stdout + run.stderr)
        settings = config.read_text().splitlines()
        passed = run.returncode == 0 and f"CONFIG_TARGET_{target}_{subtarget}=y" in settings
        profiles = sum(
            line.startswith(f"CONFIG_TARGET_DEVICE_{target}_{subtarget}_DEVICE_") and line.endswith("=y")
            for line in settings
        )
        results.append({"target": pair, "pass": passed, "profiles": profiles})
        print(f"{'PASS' if passed else 'FAIL'} {pair}: {profiles} device profiles", flush=True)

    (output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    passed = sum(result["pass"] for result in results)
    print(f"{passed}/{len(results)} configurations passed. Results: {output}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
