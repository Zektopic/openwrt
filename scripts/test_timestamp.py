"""Exercise dependency decisions through the Perl script's public CLI."""

import os
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).with_name("timestamp.pl")
EPOCH_NS = 1_700_000_000_000_000_000


def touch(path, offset=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("test\n")
    os.utime(path, ns=(EPOCH_NS + offset, EPOCH_NS + offset))
    return path


def timestamp(*args, cwd):
    return subprocess.run(
        ["perl", str(SCRIPT), *map(str, args)], cwd=cwd,
        capture_output=True, text=True, timeout=10,
    )


@pytest.mark.parametrize("offset, expected", [(-100_000_000, 0), (0, 0), (100_000_000, 1)])
def test_dependency_timestamp_precision(tmp_path, offset, expected):
    stamp = touch(tmp_path / "stamp", 500_000_000)
    source = touch(tmp_path / "source", 500_000_000 + offset)
    result = timestamp("-n", stamp, source, cwd=tmp_path)
    assert result.returncode == expected, result.stderr


def test_missing_stamp_requires_rebuild(tmp_path):
    result = timestamp("-n", tmp_path / "missing", cwd=tmp_path)
    assert result.returncode == 1


@pytest.mark.parametrize("mode", ["-n", "-p", "-F"])
def test_paths_and_exclusions_are_not_shell_commands(tmp_path, mode):
    stamp = touch(tmp_path / "stamp", 1_000_000_000)
    source = touch(tmp_path / "source'; touch INJECTED; echo '", 2_000_000_000)
    excluded = touch(tmp_path / "skip'$(touch INJECTED)*", 3_000_000_000)
    args = [mode, stamp] if mode == "-n" else [mode, "-p"]
    result = timestamp(*args, "-x", str(excluded), source, excluded, cwd=tmp_path)
    assert not (tmp_path / "INJECTED").exists()
    assert result.returncode == (1 if mode == "-n" else 0), result.stderr
    if mode != "-n":
        assert result.stdout == f"{source}\n"


def test_exclusions_and_version_control_directories(tmp_path):
    stamp = touch(tmp_path / "stamp", 1_000_000_000)
    source = touch(tmp_path / "source" / "old")
    for name in ["ignored", ".svn/entries", "CVS/Entries"]:
        touch(source.parent / name, 2_000_000_000)
    result = timestamp("-n", stamp, "-x", "*/ignored", source.parent, cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_follow_directory_symlinks(tmp_path):
    stamp = touch(tmp_path / "stamp", 500_000_000)
    source = touch(tmp_path / "external" / "new", 600_000_000)
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "linked").symlink_to(source.parent, target_is_directory=True)
    assert timestamp("-n", stamp, tree, cwd=tmp_path).returncode == 0
    assert timestamp("-f", "-n", stamp, tree, cwd=tmp_path).returncode == 1


def test_filename_with_newline(tmp_path):
    source = touch(tmp_path / "line\nbreak")
    result = timestamp("-F", "-p", tmp_path, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{source}\n"


def test_failed_scan_does_not_skip_rebuild(tmp_path):
    stamp = touch(tmp_path / "stamp")
    result = timestamp("-n", stamp, tmp_path / "missing-source", cwd=tmp_path)
    assert result.returncode != 0
