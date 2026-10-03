#!/usr/bin/env bash
# Usage: build_target.sh <target> <subtarget> [clean]+# JOBS controls concurrency; DEVICE selects one profile; ALL_PROFILES=1 selects all.
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 || ! $1 =~ ^[a-zA-Z0-9_-]+$ || ! $2 =~ ^[a-zA-Z0-9_-]+$ || ${3:-clean} != clean ]]; then
    echo "Usage: $0 <target> <subtarget> [clean]" >&2
    exit 2
fi
TARGET=$1
SUBTARGET=$2
JOBS=${JOBS:-2}
if [[ ! $JOBS =~ ^[1-9][0-9]*$ || ( -n ${DEVICE:-} && ! $DEVICE =~ ^[a-zA-Z0-9_-]+$ ) ]]; then
    echo 'JOBS must be a positive integer and DEVICE must be a profile identifier.' >&2
    exit 2
fi
if [[ -n ${DEVICE:-} && ${ALL_PROFILES:-0} == 1 ]]; then
    echo 'Select either DEVICE or ALL_PROFILES=1.' >&2
    exit 2
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
mkdir -p logs/build-helper
LOG="logs/build-helper/$TARGET-$SUBTARGET.log"
trap 'echo "Build failed; see $LOG" >&2' ERR

if [[ ! -f target/linux/$TARGET/Makefile ]]; then
    echo "Unknown target: $TARGET" >&2
    exit 2
fi
[[ ! -f .config ]] || cp .config "logs/build-helper/$TARGET-$SUBTARGET.previous.config"
if [[ ${3:-} == clean ]]; then
    make clean > "$LOG" 2>&1
fi

printf 'CONFIG_TARGET_%s=y\nCONFIG_TARGET_%s_%s=y\n' "$TARGET" "$TARGET" "$SUBTARGET" > .config
if [[ -n ${DEVICE:-} ]]; then
    printf 'CONFIG_TARGET_%s_%s_DEVICE_%s=y\n' "$TARGET" "$SUBTARGET" "$DEVICE" >> .config
elif [[ ${ALL_PROFILES:-0} == 1 ]]; then
    cat >> .config <<'EOF'
CONFIG_TARGET_MULTI_PROFILE=y
CONFIG_TARGET_ALL_PROFILES=y
CONFIG_TARGET_PER_DEVICE_ROOTFS=y
EOF
fi
make defconfig >> "$LOG" 2>&1
if ! grep -qx "CONFIG_TARGET_${TARGET}_${SUBTARGET}=y" .config; then
    echo "Target/subtarget is unavailable: $TARGET/$SUBTARGET" >&2
    exit 1
fi
if [[ -n ${DEVICE:-} ]] && ! grep -qx "CONFIG_TARGET_${TARGET}_${SUBTARGET}_DEVICE_${DEVICE}=y" .config; then
    echo "Device profile is unavailable: $DEVICE" >&2
    exit 1
fi

echo "Building $TARGET/$SUBTARGET with $JOBS jobs; log: $LOG"
make -j"$JOBS" V=s >> "$LOG" 2>&1
echo "Build completed. Images: bin/targets/$TARGET/$SUBTARGET/"
find "bin/targets/$TARGET/$SUBTARGET" -maxdepth 1 -type f -print
