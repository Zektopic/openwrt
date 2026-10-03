#!/usr/bin/env bash
# Usage: qemu_test.sh <x86_64|malta_be|malta_le|armsr_armv7|armsr_armv8> [image_dir]
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/boot_result.sh"
ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=${1:-x86_64}
IMGDIR=${2:-$ROOT/bin/targets}
TIMEOUT=${TIMEOUT:-120}
if [[ $# -gt 2 || ! $TIMEOUT =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: $0 <target> [image_dir]; TIMEOUT must be positive seconds" >&2
    exit 2
fi
shopt -s nullglob
case "$TARGET" in
    x86_64)
        images=("$IMGDIR"/x86/64/*-ext4-combined-efi.img{,.gz})
        [[ ${#images[@]} -gt 0 ]] || { echo "No EFI image in $IMGDIR/x86/64" >&2; exit 1; }
        exec bash "$SCRIPT_DIR/smoke_test.sh" "${images[0]}"
        ;;
    malta_be) target=malta; subtarget=be; emulator=qemu-system-mips ;;
    malta_le) target=malta; subtarget=le; emulator=qemu-system-mipsel ;;
    armsr_armv7|armvirt_32) target=armsr; subtarget=armv7; emulator=qemu-system-arm ;;
    armsr_armv8|armvirt_64) target=armsr; subtarget=armv8; emulator=qemu-system-aarch64 ;;
    *) echo "Unsupported QEMU target: $TARGET" >&2; exit 2 ;;
esac
if ! command -v "$emulator" >/dev/null; then
    echo "[SKIP] Install $emulator to run this boot test." >&2
    exit 77
fi
images=("$IMGDIR/$target/$subtarget/"*-initramfs-kernel.bin)
if [[ ${#images[@]} == 0 ]]; then
    echo "No initramfs kernel found in $IMGDIR/$target/$subtarget" >&2
    exit 1
fi
IMAGE=$(realpath -- "${images[0]}")
LOG=${LOG:-$ROOT/logs/qemu/$TARGET.log}
mkdir -p -- "$(dirname -- "$LOG")"
LOG=$(realpath -- "$LOG")
cd -- "$ROOT"
status=0
timeout --kill-after=5 "$TIMEOUT" bash scripts/qemustart "$target" "$subtarget" \
    --kernel "$IMAGE" -snapshot -nic none -no-reboot > "$LOG" 2>&1 || status=$?
tail -40 "$LOG"
boot_result "$LOG" "$status"
