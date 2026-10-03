"""Verify the relocated FIT string table and explicit output path."""

from pathlib import Path
import struct
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "target/linux/ipq40xx/image/netgear-fit-padding.py"


@pytest.mark.parametrize("size", [1024, 65536, 65537])
def test_padding_preserves_payload_and_honors_destination(tmp_path, size):
    data = bytearray(size)
    strings = bytes(range(256))
    data[512:768] = strings
    struct.pack_into(">I", data, 0, 0xd00dfeed)
    struct.pack_into(">I", data, 4, size)
    struct.pack_into(">I", data, 12, 512)
    source = tmp_path / "kernel.fit"
    output = tmp_path / "firmware.bin"
    source.write_bytes(data)
    subprocess.run([sys.executable, str(SCRIPT), str(source), str(output)], check=True, capture_output=True)
    assert source.read_bytes() == data
    assert not source.with_suffix(".fit.new").exists()
    padded = output.read_bytes()
    offset = (size // 65536 + 2) * 65536
    assert len(padded) == offset + 65536 - 64
    assert struct.unpack_from(">I", padded, 12)[0] == offset
    assert struct.unpack_from(">I", padded, 4)[0] == offset + 32768
    assert padded[offset:offset + 256] == strings
    assert padded[512:768] == bytes(256)
    assert padded[16:512] == data[16:512]
    assert padded[768:size] == data[768:]
