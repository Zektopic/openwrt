"""Exercise the actual NVRAM serializer using memory, never a flash device."""

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def nvram_harness(tmp_path_factory):
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("a C compiler is required")
    directory = tmp_path_factory.mktemp("nvram")
    source = directory / "test.c"
    source.write_text(r'''
#include <assert.h>
#include "nvram.c"

int main(int argc, char **argv)
{
    size_t capacity = strtoul(argv[1], NULL, 10);
    size_t offset = strtoul(argv[2], NULL, 10);
    size_t length = strtoul(argv[3], NULL, 10);
    int overflow = atoi(argv[4]);
    nvram_handle_t h = { .fd = -1, .length = capacity + offset, .offset = offset };
    char *value = malloc(length + 1);
    char *before = malloc(h.length + 16);
    h.mmap = malloc(h.length + 16);
    memset(h.mmap, 0xa5, h.length + 16);
    memcpy(before, h.mmap, h.length + 16);
    memset(value, 'x', length);
    value[length] = 0;
    nvram_part_size = h.length;
    assert(nvram_set(&h, "key", value) == 0);
    int result = nvram_commit(&h);
    if (overflow) {
        assert(result == -ENOSPC);
        assert(memcmp(before, h.mmap, h.length + 16) == 0);
        assert(strcmp(nvram_get(&h, "key"), value) == 0);
    } else {
        nvram_header_t *header = nvram_header(&h);
        assert(result == 0);
        assert(header->len <= capacity);
        assert(header->len % 4 == 0);
        assert(strcmp(nvram_get(&h, "key"), value) == 0);
        assert(memcmp(before, h.mmap, offset) == 0);
        assert(memcmp(before + h.length, h.mmap + h.length, 16) == 0);
        assert(hndcrc8((uint8_t *)header + NVRAM_CRC_START_POSITION,
                      header->len - NVRAM_CRC_START_POSITION, 0xff) ==
               (header->crc_ver_init & 0xff));
        for (size_t i = sizeof(*header) + length + 5; i < header->len; i++)
            assert(((char *)header)[i] == 0);
    }
    _nvram_free(&h);
    free(h.mmap);
    free(before);
    free(value);
    return 0;
}
''')
    src = ROOT / "package/utils/nvram/src"
    executable = directory / "test"
    subprocess.run([cc, "-I", str(src), str(source), str(src / "crc.c"),
                    "-o", str(executable)], check=True, capture_output=True)
    return executable


@pytest.mark.parametrize("capacity,offset", [(32, 0), (64, 4), (32768, 16)])
@pytest.mark.parametrize("spare", [0, 1, 2, 3, 4, -1, -2])
def test_commit_bounds_and_roundtrip(nvram_harness, capacity, offset, spare):
    # Header + "key=" + value + two NUL bytes consumes 26 + len(value).
    result = subprocess.run(
        [str(nvram_harness), str(capacity), str(offset), str(capacity - 26 - spare),
         str(int(spare < 0))], text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
