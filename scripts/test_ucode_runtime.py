"""Run networking helpers against the ucode version selected by the build.

Set UCODE to the interpreter and UCODE_LIB to its module directory when testing
outside OpenWrt. Native command stubs keep these tests away from real devices.
"""

import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
UCODE = os.environ.get("UCODE") or shutil.which("ucode")
pytestmark = pytest.mark.skipif(not UCODE, reason="ucode interpreter is required")


def executable(path, body):
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)


def run_ucode(tmp_path, program, **environment):
    args = [UCODE]
    if os.environ.get("UCODE_LIB"):
        args += ["-L", os.environ["UCODE_LIB"]]
    args += ["-L", str(tmp_path / "*.uc"), "-e", program]
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}", **environment)
    result = subprocess.run(args, cwd=tmp_path, env=env, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_wifi_mac_address_generation(tmp_path):
    common = tmp_path / "wifi" / "common.uc"
    common.parent.mkdir()
    common.write_text("export function append_value() {}\nexport function log() {}\n")
    executable(tmp_path / "ucode", 'printf "02:11:22:33:44:55\\n"\n')
    source = ROOT / "package/network/config/wifi-scripts/files-ucode/usr/share/ucode/wifi/iface.uc"
    output = run_ucode(tmp_path, f"""
        import * as iface from {json.dumps(str(source))};
        let data = {{ ifname: 'wlan0' }};
        iface.prepare(data, 'phy0', 1, '02:00:00:00:00:00');
        print(data.macaddr);
    """)
    assert output == "02:11:22:33:44:55"


def test_wireguard_key_generation_and_setup(tmp_path):
    # The executable location is the only substituted implementation constant.
    source = ROOT / "package/network/utils/wireguard-tools/files/wireguard.uc"
    code = source.read_text().replace("'/usr/bin/wg'", json.dumps(str(tmp_path / "wg")))
    module = tmp_path / "wireguard.uc"
    module.write_text(code)
    executable(tmp_path / "wg", '''case "$1" in
genkey) printf 'generated-key\\n' ;;
syncconf) cat > "$WG_CONFIG" ;;
show) printf 'peer\\t198.51.100.1:51820\\n' ;;
esac
''')
    executable(tmp_path / "ip", "exit 0\n")
    config = tmp_path / "wg.conf"
    output = run_ucode(tmp_path, f"""
        global.netifd = {{ add_proto: (p) => {{ global.protocol = p; }} }};
        include({json.dumps(str(module))});
        let cursor = {{
            get: () => 'generate', set: () => true, commit: () => true,
            foreach: () => null
        }};
        let config = protocol.config({{ uci: cursor, section: 'wg0', data: {{}} }});
        let result = {{}};
        protocol.setup({{
            iface: 'wg0', config,
            setup_failed: () => {{ result.failed = true; }},
            add_host_dependency: (addr) => {{ result.endpoint = addr; }},
            update_link: (up) => {{ result.up = up; }}
        }});
        result.key = config.private_key;
        print(result);
    """, WG_CONFIG=str(config))
    assert json.loads(output) == {"key": "generated-key", "endpoint": "198.51.100.1", "up": True}
    assert "PrivateKey=generated-key" in config.read_text()


@pytest.mark.parametrize("device", ["/dev/ubi0_1", "device'; touch INJECTED; echo '"])
def test_provision_streams_data_without_shell_injection(tmp_path, device):
    source = ROOT / "package/utils/provision/files/usr/share/ucode/provision.uc"
    module = tmp_path / "provision.uc"
    # Export the backend for a direct test; avoid accessing real UBI hardware.
    module.write_text(source.read_text() + "\nexport { ubi_proto };\n")
    executable(tmp_path / "ubiupdatevol", 'printf "%s\\n" "$@" > "$UBI_ARGS"\ncat > "$UBI_DATA"\n')
    args = tmp_path / "ubi-args"
    data = tmp_path / "ubi-data"
    output = run_ucode(tmp_path, f"""
        import {{ ubi_proto }} from {json.dumps(str(module))};
        let backend = proto({{ dev: {json.dumps(device)} }}, ubi_proto);
        let committed = backend.commit('test-data');
        let reader = proto({{ dev: getenv('UBI_DATA') }}, ubi_proto);
        print({{ committed, data: reader.read() }});
    """, UBI_ARGS=str(args), UBI_DATA=str(data))
    assert json.loads(output) == {"committed": True, "data": "test-data"}
    assert args.read_text().splitlines() == [device, "-s", "18", "-"]
    # Preserve the existing on-flash character field (ucode's 'c' converts 0 to '0').
    assert data.read_bytes() == struct.pack(">IIc", 0xf09f8697, 9, b"0") + b"test-data"
    assert not (tmp_path / "INJECTED").exists()
