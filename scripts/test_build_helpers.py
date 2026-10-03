"""Check helper failure reporting without requiring a cross compiler or QEMU."""

import gzip
import os
from pathlib import Path
import shutil
import subprocess

import pytest


HELPERS = Path(__file__).resolve().parents[1] / ".zektopic" / "TEST_SCRIPTS"


@pytest.fixture
def helper_repo(tmp_path):
    root = tmp_path / "checkout"
    shutil.copytree(HELPERS, root / ".zektopic" / "TEST_SCRIPTS")
    tools = tmp_path / "bin"
    tools.mkdir()
    env = dict(os.environ, PATH=f"{tools}:{os.environ['PATH']}")
    return root, tools, env


@pytest.mark.parametrize("message,status,expected", [
    ("Please press Enter to activate this console.", 0, 0),
    ("Please press Enter to activate this console.", 124, 0),
    ("OpenWrt kernel init started", 124, 1),
    ("Please press Enter to activate this console.\nKernel panic - not syncing", 124, 1),
    ("Please press Enter to activate this console.", 1, 1),
])
def test_boot_result_and_image_protection(helper_repo, tmp_path, message, status, expected):
    root, tools, env = helper_repo
    emulator = tools / "qemu-system-x86_64"
    emulator.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$@" > "$ARGS_FILE"\n'
        'printf "%s\\n" "$BOOT_OUTPUT"\nexit "$EMULATOR_STATUS"\n'
    )
    emulator.chmod(0o755)
    firmware = tmp_path / "firmware.fd"
    firmware.write_bytes(b"firmware")
    image = tmp_path / "disk image.img.gz"
    image.write_bytes(gzip.compress(b"disk contents"))
    original = image.read_bytes()
    args = tmp_path / "qemu-args"
    env.update(OVMF=str(firmware), BOOT_OUTPUT=message, EMULATOR_STATUS=str(status), ARGS_FILE=str(args))
    result = subprocess.run(
        ["bash", str(root / ".zektopic/TEST_SCRIPTS/smoke_test.sh"), str(image)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    assert image.read_bytes() == original
    arguments = args.read_text().splitlines()
    assert "-snapshot" in arguments
    drive = next(arg for arg in arguments if arg.startswith("file="))
    temporary_image = Path(drive.split(",")[0][5:])
    assert not temporary_image.exists(), "Decompressed image must be cleaned up"
    assert (root / "logs/qemu/x86_64.log").is_file()


def test_missing_firmware_is_a_skip(helper_repo, tmp_path):
    root, tools, env = helper_repo
    emulator = tools / "qemu-system-x86_64"
    emulator.write_text("#!/bin/sh\nexit 99\n")
    emulator.chmod(0o755)
    image = tmp_path / "image.img"
    image.write_bytes(b"test")
    env["OVMF"] = str(tmp_path / "missing.fd")
    result = subprocess.run(
        ["bash", str(root / ".zektopic/TEST_SCRIPTS/smoke_test.sh"), str(image)],
        env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 77


@pytest.mark.parametrize("status", [0, 2])
def test_build_wrapper_uses_checkout_and_propagates_failure(helper_repo, tmp_path, status):
    root, tools, env = helper_repo
    target = root / "target/linux/x86"
    target.mkdir(parents=True)
    (target / "Makefile").touch()
    (root / ".config").write_text("previous configuration\n")
    make = tools / "make"
    make.write_text(
        '#!/bin/sh\n[ "$1" != defconfig ] || exit 0\n'
        'printf "build arguments: %s\\n" "$*"\n'
        'mkdir -p bin/targets/x86/64\nexit "$BUILD_STATUS"\n'
    )
    make.chmod(0o755)
    env.update(JOBS="2", ALL_PROFILES="1", BUILD_STATUS=str(status))
    result = subprocess.run(
        ["bash", str(root / ".zektopic/TEST_SCRIPTS/build_x86_64.sh")],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == status, result.stdout + result.stderr
    assert "CONFIG_TARGET_ALL_PROFILES=y" in (root / ".config").read_text()
    assert (root / "logs/build-helper/x86-64.previous.config").read_text() == "previous configuration\n"
    assert "-j2 V=s" in (root / "logs/build-helper/x86-64.log").read_text()
    if status:
        assert "Build completed" not in result.stdout
