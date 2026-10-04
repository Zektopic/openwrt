"""Check authenticated EAD command execution without starting the daemon."""

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ead_command(tmp_path_factory):
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("a C compiler is required")
    headers = subprocess.run([cc, "-E", "-include", "pcap.h", "-"],
                             input="", text=True, capture_output=True)
    if headers.returncode:
        pytest.skip("libpcap development headers are required")
    directory = tmp_path_factory.mktemp("ead")
    source = directory / "test.c"
    source.write_text('''
#define main ead_program_main
#include "ead.c"
#undef main
int main(int argc, char **argv) {
    ead_exec_command(argv[1]);
    return 127;
}
''')
    src = ROOT / "package/network/services/ead/src"
    executable = directory / "test"
    subprocess.run(
        [cc, "-I", str(src), "-I", str(src / "tinysrp"), "-ffunction-sections",
         "-fdata-sections", "-Wl,--gc-sections", "-Wno-implicit-function-declaration",
         str(source), "-o", str(executable)], check=True, capture_output=True,
    )
    return executable


@pytest.mark.parametrize("command,expected,status", [
    ("printf '%s' 'hello world'", "hello world", 0),
    (r"printf '%s' hello\ world", "hello world", 0),
    ("printf '%s' hello | tr a-z A-Z", "HELLO", 0),
    ("value=working; printf '%s' \"$value\"", "working", 0),
    ("exit 7", "", 7),
])
def test_shell_commands(ead_command, command, expected, status):
    result = subprocess.run([str(ead_command), command], text=True,
                            capture_output=True, timeout=5)
    assert (result.stdout, result.returncode) == (expected, status), result.stderr
