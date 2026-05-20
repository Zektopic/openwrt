#!/bin/bash
# build_slot.sh — Build all config variants for one target in one worktree
# Usage: ./build_slot.sh <workdir> <board> <subtarget> <arch_label>
set -e
WORKDIR="$1"
BOARD="$2"
SUBTARGET="$3"
LABEL="$4"
THREADS=${THREADS:-$(nproc)}
LOGDIR="$WORKDIR/build_logs"

mkdir -p "$LOGDIR"
cd "$WORKDIR"

build_variant() {
    local variant="$1"
    local logfile="$LOGDIR/build_${BOARD}_${SUBTARGET}_${variant}.log"
    echo "=== [$LABEL] Building $BOARD/$SUBTARGET ($variant) ===" | tee "$logfile"

    # Configure target
    echo "CONFIG_TARGET_${BOARD}=y" > .config
    echo "CONFIG_TARGET_${BOARD}_${SUBTARGET}=y" >> .config

    # Always add test packages
    echo "CONFIG_PACKAGE_iperf3=y" >> .config
    echo "CONFIG_PACKAGE_curl=y" >> .config
    echo "CONFIG_PACKAGE_tcpdump=y" >> .config

    make defconfig >> "$logfile" 2>&1; local dc=$?
    if [ "$dc" -ne 0 ] && [ "$dc" -ne 2 ]; then
        echo "[FAIL] make defconfig failed for $BOARD/$SUBTARGET (exit $dc)" | tee -a "$logfile"
        return 1
    fi
    [ "$dc" -eq 2 ] && echo "[WARN] make defconfig had scan warnings (exit 2), continuing" | tee -a "$logfile"

    # Apply variant-specific config
    case "$variant" in
        minimal)
            for pkg in dnsmasq firewall4 wpad-basic-mbedtls odhcpd-ipv6only odhcp6c; do
                sed -i "s/^CONFIG_PACKAGE_${pkg}=y/# CONFIG_PACKAGE_${pkg} is not set/" .config 2>/dev/null || true
            done
            ;;
        full)
            cat >> .config << 'PKGEOF'
CONFIG_PACKAGE_kmod-bridge=y
CONFIG_PACKAGE_kmod-tun=y
CONFIG_PACKAGE_kmod-bonding=y
CONFIG_PACKAGE_kmod-wireguard=y
CONFIG_PACKAGE_mtr=y
PKGEOF
            ;;
        dev)
            cat >> .config << 'PKGEOF'
CONFIG_PACKAGE_strace=y
CONFIG_PACKAGE_gdb=y
CONFIG_PACKAGE_perf=y
CONFIG_PACKAGE_nano=y
CONFIG_PACKAGE_tmux=y
PKGEOF
            ;;
        hardened)
            cat >> .config << 'PKGEOF'
CONFIG_KERNEL_CC_STACKPROTECTOR_STRONG=y
CONFIG_KERNEL_FORTIFY_SOURCE=y
CONFIG_PACKAGE_arptables=y
CONFIG_PACKAGE_ebtables=y
PKGEOF
            ;;
    esac

    make olddefconfig >> "$logfile" 2>&1 || {
        echo "[WARN] olddefconfig exit code $?, continuing" | tee -a "$logfile"
    }

    # Build
    echo "=== Starting build: $LABEL $variant ===" >> "$logfile"
    if make -j$THREADS V=s HOST_EXTRA_CXXFLAGS="-D_GNU_SOURCE" >> "$logfile" 2>&1; then
        echo "[PASS] $LABEL ($variant)" | tee -a "$logfile"
        # Archive images with variant label
        local imgdir="bin/targets/${BOARD}/${SUBTARGET}"
        if [ -d "$imgdir" ]; then
            local vdir="bin/targets/${BOARD}/${SUBTARGET}_${variant}"
            mkdir -p "$vdir"
            cp -r "$imgdir"/* "$vdir"/ 2>/dev/null || true
            echo "[INFO] Images archived to $vdir" | tee -a "$logfile"
        fi
        return 0
    else
        local ec=$?
        echo "[FAIL] $LABEL ($variant) — exit code $ec" | tee -a "$logfile"
        grep -i "error\|fail\|segfault\|panic" "$logfile" | tail -10 >> "$logfile"
        return $ec
    fi
}

# Build default first (full toolchain build)
build_variant "default"

# Build remaining variants (incremental, toolchain preserved)
for var in minimal full dev hardened; do
    build_variant "$var" || echo "[WARN] $var build failed, continuing"
done

echo "=== [$LABEL] ALL VARIANTS COMPLETE ==="
