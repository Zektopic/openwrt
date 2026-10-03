#!/usr/bin/env bash
# Shared result handling: an early kernel banner is not a successful boot.
boot_result() {
    local log=$1 status=$2
    if [[ $status != 0 && $status != 124 ]]; then
        echo "[FAIL] Emulator exited with status $status. Log: $log" >&2
        return 1
    fi
    if grep -qiE 'Kernel panic|Oops:|BUG:|not syncing|segfault|out of memory' "$log"; then
        echo "[FAIL] Fatal boot error. Log: $log" >&2
        return 1
    fi
    if grep -qE 'Please press Enter to activate this console|Please press Enter to activate console|root@[^[:space:]]+:[^#]*#|OpenWrt login:' "$log"; then
        echo "[PASS] Guest reached the console. Log: $log"
        return 0
    fi
    echo "[FAIL] Guest did not reach the console. Log: $log" >&2
    return 1
}
