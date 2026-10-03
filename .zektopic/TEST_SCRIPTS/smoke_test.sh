#!/usr/bin/env bash
# Usage: smoke_test.sh [x86/64 ext4 EFI image, optionally gzip compressed]
# TIMEOUT, LOG and OVMF may be overridden. Disk writes go to a temporary snapshot.
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/boot_result.sh"
ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
TIMEOUT=${TIMEOUT:-120}
if [[ ! $TIMEOUT =~ ^[1-9][0-9]*$ ]]; then
    echo 'TIMEOUT must be a positive number of seconds.' >&2
    exit 2
fi
if ! command -v qemu-system-x86_64 >/dev/null; then
    echo '[SKIP] Install qemu-system-x86 to run the boot test.' >&2
    exit 77
fi
if [[ $# -gt 1 ]]; then
    echo "Usage: $0 [image]" >&2
    exit 2
fi
if [[ $# == 1 ]]; then
    IMAGE=$1
else
    shopt -s nullglob
    images=("$ROOT"/bin/targets/x86/64/*-ext4-combined-efi.img{,.gz})
    if [[ ${#images[@]} == 0 ]]; then
        echo 'No x86/64 ext4 EFI image found. Build one first.' >&2
        exit 1
    fi
    IMAGE=${images[0]}
fi
if [[ ! -s $IMAGE ]]; then
    echo "Image does not exist or is empty: $IMAGE" >&2
    exit 1
fi

TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if [[ $IMAGE == *.gz ]]; then
    gzip -dc -- "$IMAGE" > "$TMP/disk.img"
    IMAGE=$TMP/disk.img
fi

firmware=()
if [[ -n ${OVMF:-} ]]; then
    [[ -f $OVMF ]] || { echo "OVMF not found: $OVMF" >&2; exit 77; }
    firmware=(-bios "$OVMF")
else
    for path in /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd; do
        vars=${path/CODE/VARS}
        if [[ -f $path && -f $vars ]]; then
            cp -- "$vars" "$TMP/vars.fd"
            firmware=(-drive "if=pflash,format=raw,unit=0,readonly=on,file=$path"
                      -drive "if=pflash,format=raw,unit=1,file=$TMP/vars.fd")
            break
        fi
    done
    if [[ ${#firmware[@]} == 0 && -f /usr/share/ovmf/OVMF.fd ]]; then
        firmware=(-bios /usr/share/ovmf/OVMF.fd)
    fi
fi
if [[ ${#firmware[@]} == 0 ]]; then
    echo '[SKIP] Install ovmf, or set OVMF to a firmware image.' >&2
    exit 77
fi

accel=()
if [[ -r /dev/kvm && -w /dev/kvm ]]; then
    accel=(-enable-kvm -cpu host)
fi
LOG=${LOG:-$ROOT/logs/qemu/x86_64.log}
mkdir -p -- "$(dirname -- "$LOG")"
# QEMU separates -drive options with commas; double any literal path commas.
IMAGE=${IMAGE//,/,,}
status=0
timeout --kill-after=5 "$TIMEOUT" qemu-system-x86_64 \
    "${firmware[@]}" "${accel[@]}" \
    -drive "file=$IMAGE,format=raw,if=virtio" -snapshot -nic none \
    -m 512M -nographic -no-reboot > "$LOG" 2>&1 || status=$?
tail -40 "$LOG"
boot_result "$LOG" "$status"
