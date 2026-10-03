"""Prerequisite failures must stop make and remain visible to the caller."""

import os
from pathlib import Path
import subprocess


PREREQ = Path(__file__).resolve().parents[1] / "include" / "prereq.mk"


def test_failed_prerequisite_is_reported_and_can_recover(tmp_path):
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "TMP_DIR := $(CURDIR)\n"
        "ORIG_PATH := $(PATH)\n"
        "NO_TRACE_MAKE = $(MAKE) --no-print-directory\n"
        f"include {PREREQ}\n"
        "$(eval $(call TestHostCommand,fixture,fixture dependency unavailable,$(COMMAND)))\n"
        "FORCE:\n"
        ".PHONY: FORCE\n"
    )
    env = os.environ.copy()
    for key in ["FORCE", "MAKEFLAGS", "MFLAGS", "MAKELEVEL"]:
        env.pop(key, None)

    def run(command):
        return subprocess.run(
            ["make", "--no-print-directory", "prereq", f"COMMAND={command}"],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15,
        )

    failed = run("false")
    assert failed.returncode != 0
    assert "fixture dependency unavailable" in failed.stdout
    assert not (tmp_path / ".prereq-error").exists()
    recovered = run("true")
    assert recovered.returncode == 0, recovered.stderr
    assert "ok." in recovered.stdout
