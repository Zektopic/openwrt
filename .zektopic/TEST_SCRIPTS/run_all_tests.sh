#!/bin/bash
# run_all_tests.sh — Master orchestrator for comprehensive OpenWrt testing
# Discovers built images, runs QEMU tests, generates reports.
set -e

SCRIPTDIR="$(cd "$(dirname "$0")" && pwd)"
PROJECTDIR="$(cd "$SCRIPTDIR/../.." && pwd)"
REPORTDIR="$PROJECTDIR/.zektopic"
TEST_SCRIPT="$SCRIPTDIR/comprehensive_test.py"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
RESULTS_DIR="/tmp/ow_test_results_${TIMESTAMP}"
SUMMARY_FILE="$RESULTS_DIR/summary.json"
mkdir -p "$RESULTS_DIR"

# All build directories to search for images
BUILD_DIRS=(
    /home/manu/openwrt
    /home/manu/openwrt-arm
    /home/manu/openwrt-embedded
    /home/manu/openwrt-malta
    /home/manu/openwrt-x86-64-tests
)

# QEMU-testable targets with their board/subtarget/variant dirs
declare -A TARGET_MAP
TARGET_MAP["x86_64"]="x86/64"
TARGET_MAP["x86_generic"]="x86/generic"
TARGET_MAP["armv7"]="armsr/armv7"
TARGET_MAP["armv8"]="armsr/armv8"
TARGET_MAP["malta_be"]="malta/be"
TARGET_MAP["malta_le"]="malta/le"

# Build-only targets
BUILD_ONLY_TARGETS=("ath79/generic" "mediatek/filogic" "ramips/mt7621")

VARIANTS=("default" "minimal" "full" "dev" "hardened")

log() { echo "[$(date +%H:%M:%S)] $*"; }

# Phase A: Static image inventory
log "=== Phase A: Image Inventory ==="
INVENTORY="$RESULTS_DIR/image_inventory.txt"
: > "$INVENTORY"

for dir in "${BUILD_DIRS[@]}"; do
    if [ -d "$dir/bin/targets" ]; then
        find "$dir/bin/targets" -type f -name "*.img*" -o -name "*initramfs*" -o -name "*.bin" -o -name "*.manifest" 2>/dev/null >> "$INVENTORY"
    fi
done

log "Image inventory: $(wc -l < "$INVENTORY") files found"
log "Build directories searched: ${BUILD_DIRS[*]}"

# Phase B: QEMU tests
log "=== Phase B: QEMU Comprehensive Tests ==="
TEST_RESULTS="$RESULTS_DIR/test_results.json"
PORT=23000
FIRST=1

echo "{" > "$TEST_RESULTS"

for target in "${!TARGET_MAP[@]}"; do
    board_sub="${TARGET_MAP[$target]}"
    board="${board_sub%%/*}"
    subtarget="${board_sub##*/}"

    for variant in "${VARIANTS[@]}"; do
        log "Testing $target ($variant)..."
        # Find image
        IMG=""
        for dir in "${BUILD_DIRS[@]}"; do
            for d in "$dir/bin/targets/$board/${subtarget}_$variant" "$dir/bin/targets/$board/$subtarget"; do
                if [ -d "$d" ]; then
                    # Use target-appropriate pattern
                    case "$target" in
                        x86_64) pat="*ext4-combined-efi.img*" ;;
                        x86_generic) pat="*ext4-combined.img*" ;;
                        armv7|armv8|malta_be|malta_le) pat="*initramfs-kernel.bin" ;;
                    esac
                    found=$(ls "$d"/$pat 2>/dev/null | head -1)
                    [ -n "$found" ] && IMG="$found" && break 2
                fi
            done
        done

        if [ -z "$IMG" ]; then
            log "  SKIP - no image for $target/$variant"
            [ "$FIRST" -eq 0 ] && echo "," >> "$TEST_RESULTS"
            echo "\"${target}_${variant}\": {\"target\":\"$target\",\"variant\":\"$variant\",\"error\":\"No image found\"}" >> "$TEST_RESULTS"
            FIRST=0
            continue
        fi

        log "  Image: $(basename "$IMG")"
        JSON_OUT="$RESULTS_DIR/${target}_${variant}.json"

        if python3 "$TEST_SCRIPT" "$target" --variant "$variant" --port "$PORT" \
            --timeout 300 --json "$JSON_OUT" 2>&1; then
            log "  PASS"
        else
            log "  DONE (exit $?)"
        fi

        # Append to combined results
        [ "$FIRST" -eq 0 ] && echo "," >> "$TEST_RESULTS"
        cat "$JSON_OUT" >> "$TEST_RESULTS"
        FIRST=0

        PORT=$((PORT + 1))
        sleep 3
    done
done

echo "}" >> "$TEST_RESULTS"
log "QEMU tests complete. Results: $TEST_RESULTS"

# Phase C: Static verification for build-only targets
log "=== Phase C: Static Image Verification ==="
VERIFY_REPORT="$RESULTS_DIR/static_verify.txt"
: > "$VERIFY_REPORT"

for target in "${BUILD_ONLY_TARGETS[@]}"; do
    board="${target%%/*}"
    subtarget="${target##*/}"
    log "Verifying $target..."

    for variant in "${VARIANTS[@]}"; do
        img_count=0
        total_size=0
        for dir in "${BUILD_DIRS[@]}"; do
            for d in "$dir/bin/targets/$board/${subtarget}_$variant" "$dir/bin/targets/$board/$subtarget"; do
                if [ -d "$d" ]; then
                    for f in "$d"/*; do
                        if [ -f "$f" ]; then
                            img_count=$((img_count + 1))
                            size=$(stat -c%s "$f" 2>/dev/null || echo 0)
                            total_size=$((total_size + size))
                        fi
                    done
                fi
            done
        done
        echo "$target/$variant: ${img_count} images, $(numfmt --to=iec $total_size)" >> "$VERIFY_REPORT"
    done
done

cat "$VERIFY_REPORT"

# Phase D: Generate summary
log "=== Phase D: Summary ==="
python3 -c "
import json, sys
try:
    with open('$TEST_RESULTS') as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    print('FAIL: Could not parse test results')
    sys.exit(1)

total_tests = 0
total_passed = 0
total_failed = 0
results_by_target = {}

for key, result in data.items():
    t = result.get('target', 'unknown')
    v = result.get('variant', 'unknown')
    if 'summary' in result:
        s = result['summary']
        total_tests += s.get('total', 0)
        total_passed += s.get('passed', 0)
        total_failed += s.get('failed', 0)
        status = 'PASS' if s.get('failed', 0) == 0 else 'FAIL'
    elif 'error' in result or 'boot_error' in result:
        status = 'ERROR'
    else:
        status = 'INCOMPLETE'

    if t not in results_by_target: results_by_target[t] = {}
    results_by_target[t][v] = status

# Print summary table
targets = sorted(results_by_target.keys())
print(f'{\"Target\":20s} {\"Default\":12s} {\"Minimal\":12s} {\"Full\":12s} {\"Dev\":12s} {\"Hardened\":12s}')
print('-' * 68)
for t in targets:
    dv = results_by_target[t]
    print(f'{t:20s} {dv.get(\"default\",\"-\"):12s} {dv.get(\"minimal\",\"-\"):12s} {dv.get(\"full\",\"-\"):12s} {dv.get(\"dev\",\"-\"):12s} {dv.get(\"hardened\",\"-\"):12s}')

print(f'\nTotal: {total_tests} tests, {total_passed} passed, {total_failed} failed')
print(f'Results: $RESULTS_DIR')
"

log "=== All tests complete. Results in $RESULTS_DIR ==="
