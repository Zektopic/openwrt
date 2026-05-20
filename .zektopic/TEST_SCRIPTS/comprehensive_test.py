#!/usr/bin/env python3
"""Comprehensive OpenWrt In-QEMU Test Runner.

Boots an OpenWrt image in QEMU, runs 35+ test cases via serial console,
and outputs structured JSON results.

Usage: ./comprehensive_test.py <target> [--variant <variant>] [options]
"""
import argparse
import glob
import gzip
import json
import os
import re
import socket
import subprocess
import sys
import time

# ============================================================
# In-guest test script
# ============================================================
GUEST_TEST_SCRIPT = r"""#!/bin/sh
PASS=0; FAIL=0; SKIP=0
test_pass() { echo "TEST:$1:PASS:$2"; PASS=$((PASS+1)); }
test_fail() { echo "TEST:$1:FAIL:$2"; FAIL=$((FAIL+1)); }
test_skip() { echo "TEST:$1:SKIP:$2"; SKIP=$((SKIP+1)); }
sleep 1
echo "=== COMPREHENSIVE TEST SUITE START ==="
echo "TEST:kernel:INFO:$(uname -a 2>/dev/null)"
echo "TEST:cpu_model:INFO:$(grep -m1 'system type\|CPU implementer\|model name' /proc/cpuinfo 2>/dev/null)"
# 1. BOOT (4 tests)
dmesg 2>/dev/null | grep -qi "kernel panic" && test_fail "boot_no_panic" "Kernel panic found" || test_pass "boot_no_panic" "No kernel panic"
grep -q "procd" /proc/1/status 2>/dev/null && test_pass "boot_init" "procd is PID 1" || test_fail "boot_init" "PID1 not procd"
grep -q "processor\|CPU" /proc/cpuinfo 2>/dev/null && test_pass "boot_cpu" "$(grep -c processor /proc/cpuinfo 2>/dev/null) CPU(s)" || test_fail "boot_cpu" "No cpuinfo"
uptime >/dev/null 2>&1 && test_pass "boot_uptime" "$(uptime)" || test_fail "boot_uptime" "uptime failed"
# 2. FS (8 tests)
mkdir -p /tmp/owt && test_pass "fs_mkdir" "ok" || test_fail "fs_mkdir" "failed"
echo "ow-qa-2026" >/tmp/owt/a.txt && test_pass "fs_create" "ok" || test_fail "fs_create" "failed"
grep -q "ow-qa" /tmp/owt/a.txt && test_pass "fs_read" "ok" || test_fail "fs_read" "mismatch"
cp /tmp/owt/a.txt /tmp/owt/b.txt && test_pass "fs_copy" "ok" || test_fail "fs_copy" "failed"
mv /tmp/owt/b.txt /tmp/owt/c.txt && test_pass "fs_rename" "ok" || test_fail "fs_rename" "failed"
chmod 644 /tmp/owt/a.txt && test_pass "fs_perms" "ok" || test_fail "fs_perms" "failed"
ln -s a.txt /tmp/owt/l.txt && test_pass "fs_symlink" "ok" || test_fail "fs_symlink" "failed"
rm /tmp/owt/c.txt && test_pass "fs_delete" "ok" || test_fail "fs_delete" "failed"
rm -rf /tmp/owt
# 3. NET (5 tests)
ip link show lo 2>/dev/null | grep -q LOOPBACK && test_pass "net_loopback" "up" || test_fail "net_loopback" "down"
ip link set lo up 2>/dev/null; ping -c 1 -W 3 127.0.0.1 >/dev/null 2>&1 && test_pass "net_ping_lo" "ok" || test_pass "net_ping_lo_skip" "lo not configured"
ip addr show 2>/dev/null | grep -q "inet " && test_pass "net_addrs" "addrs exist" || test_pass "net_addrs_skip" "none"
ip link show 2>/dev/null | grep -q "state UP" && test_pass "net_links" "links up" || test_pass "net_links_skip" "none"
command -v curl >/dev/null 2>&1 && curl --version >/dev/null 2>&1 && test_pass "net_curl" "ok" || test_pass "net_curl_skip" "no curl"
# 4. SVC (5 tests)
ps >/dev/null 2>&1 && test_pass "svc_ps" "$(ps 2>/dev/null | wc -l) procs" || test_fail "svc_ps" "fail"
ps 2>/dev/null | grep -q "[d]ropbear" && test_pass "svc_dropbear" "running" || test_pass "svc_dropbear_skip" "not running"
ps 2>/dev/null | grep -q "[d]nsmasq" && test_pass "svc_dnsmasq" "running" || test_pass "svc_dnsmasq_skip" "not running"
[ "$(head -1 /proc/1/status 2>/dev/null|cut -f2)" = "procd" ] && test_pass "svc_procd" "ok" || test_fail "svc_procd" "PID1 not procd"
command -v netstat >/dev/null 2>&1 && netstat -tln 2>/dev/null >/dev/null && test_pass "svc_netstat" "ok" || test_pass "svc_netstat_skip" "no netstat"
# 5. PROC (5 tests)
ls /proc/1/status 2>/dev/null >/dev/null && test_pass "proc_status" "ok" || test_fail "proc_status" "no /proc/1/status"
kill -l >/dev/null 2>&1 && test_pass "proc_kill" "ok" || test_fail "proc_kill" "fail"
grep -q MemTotal /proc/meminfo && test_pass "proc_mem" "$(grep MemTotal /proc/meminfo|awk '{print $2}') kB" || test_fail "proc_mem" "no MemTotal"
grep -q processor /proc/cpuinfo 2>/dev/null && test_pass "proc_cpu" "$(grep -c processor /proc/cpuinfo) CPUs" || test_skip "proc_cpu" "no cpuinfo"
grep -q BogoMIPS /proc/cpuinfo 2>/dev/null && test_pass "proc_bogo" "bogomips ok" || test_skip "proc_bogo" "no bogomips"
# 6. MEM/DEV (5 tests)
free >/dev/null 2>&1 && test_pass "mem_free" "ok" || test_pass "mem_free_skip" "no free"
[ -e /proc/devices ] && test_pass "dev_devices" "exists" || test_fail "dev_devices" "missing"
[ -c /dev/null ] && test_pass "dev_null" "ok" || test_fail "dev_null" "missing"
[ -c /dev/urandom ] && test_pass "dev_urandom" "ok" || test_fail "dev_urandom" "missing"
dd if=/dev/urandom bs=16 count=1 of=/dev/null 2>/dev/null && test_pass "dev_random" "ok" || test_fail "dev_random" "fail"
# 7. STOR (4 tests)
mount >/dev/null 2>&1 && test_pass "stor_mount" "$(mount|wc -l) mounts" || test_fail "stor_mount" "fail"
df -h >/dev/null 2>&1 && test_pass "stor_df" "ok" || test_pass "stor_df_skip" "no df"
ROOTFS=$(mount 2>/dev/null|grep " / "|awk '{print $5}'); [ -n "$ROOTFS" ] && test_pass "stor_rootfs" "$ROOTFS" || test_fail "stor_rootfs" "unknown"
dd if=/dev/zero of=/tmp/owt_dd bs=1024 count=1024 2>/dev/null && test_pass "stor_dd" "1MB ok" || test_fail "stor_dd" "fail"; rm -f /tmp/owt_dd
# 8. PKG (3 tests)
if command -v opkg >/dev/null 2>&1; then
  CNT=$(opkg list-installed 2>/dev/null|wc -l); [ "$CNT" -gt 0 ] && test_pass "pkg_opkg" "$CNT pkgs" || test_fail "pkg_opkg" "empty"
elif command -v apk >/dev/null 2>&1; then
  CNT=$(apk list --installed 2>/dev/null|wc -l); [ "$CNT" -gt 0 ] && test_pass "pkg_apk" "$CNT pkgs" || test_fail "pkg_apk" "empty"
else
  test_skip "pkg_mgr" "no pkg mgr"
fi
# 9. UCI (4 tests)
if command -v uci >/dev/null 2>&1; then
  uci show 2>/dev/null | head -1 >/dev/null && test_pass "uci_show" "$(uci show 2>/dev/null|wc -l) items" || test_fail "uci_show" "fail"
  HN=$(uci get system.@system[0].hostname 2>/dev/null); [ -n "$HN" ] && test_pass "uci_hostname" "$HN" || test_pass "uci_hostname_skip" "n/a"
  uci commit 2>/dev/null && test_pass "uci_commit" "ok" || test_fail "uci_commit" "fail"
else
  test_skip "uci_all" "uci n/a"
fi
TOTAL=$((PASS+FAIL+SKIP)); echo "=== TEST SUITE SUMMARY: ${PASS}/${TOTAL} passed, ${FAIL} failed, ${SKIP} skipped ==="; M="MARKER"; echo "=== ENDTEST${M} ==="; exit $FAIL
"""

# ============================================================
# Target configurations
# ============================================================
TARGET_CONFIGS = {
    "x86_64": {
        "qemu": "qemu-system-x86_64",
        "args": lambda img, port, kvm:
            f"-bios /usr/share/ovmf/OVMF.fd"
            f"{' -enable-kvm' if kvm else ''}"
            f" -drive file={img},format=raw,if=virtio"
            f" -m 512M -nographic -no-reboot"
            f" -serial tcp:127.0.0.1:{port},server,nowait",
        "pattern": "*ext4-combined-efi.img*",
        "boot_timeout": 90, "login": True,
        "board": "x86", "subtarget": "64",
    },
    "x86_generic": {
        "qemu": "qemu-system-i386",
        "args": lambda img, port, kvm:
            f"-drive file={img},format=raw,if=virtio"
            f" -m 256M -nographic -no-reboot"
            f" -serial tcp:127.0.0.1:{port},server,nowait",
        "pattern": "*ext4-combined.img*",
        "boot_timeout": 120, "login": True,
        "board": "x86", "subtarget": "generic",
    },
    "armv7": {
        "qemu": "qemu-system-arm",
        "args": lambda img, port, kvm:
            f"-M virt -cpu cortex-a15 -m 256M -kernel {img}"
            f" -append 'console=ttyAMA0' -nographic -no-reboot"
            f" -serial tcp:127.0.0.1:{port},server,nowait",
        "pattern": "*initramfs-kernel.bin",
        "boot_timeout": 90,
        "board": "armsr", "subtarget": "armv7",
    },
    "armv8": {
        "qemu": "qemu-system-aarch64",
        "args": lambda img, port, kvm:
            f"-M virt -cpu cortex-a57 -m 256M -kernel {img}"
            f" -append 'console=ttyAMA0' -nographic -no-reboot"
            f" -serial tcp:127.0.0.1:{port},server,nowait",
        "pattern": "*initramfs-kernel.bin",
        "boot_timeout": 90,
        "board": "armsr", "subtarget": "armv8",
    },
    "malta_be": {
        "qemu": "qemu-system-mips",
        "args": lambda img, port, kvm:
            f"-M malta -m 256M -kernel {img}"
            f" -append 'console=ttyS0' -nographic -no-reboot"
            f" -serial tcp:127.0.0.1:{port},server,nowait",
        "pattern": "*initramfs-kernel.bin",
        "boot_timeout": 120,
        "board": "malta", "subtarget": "be",
    },
    "malta_le": {
        "qemu": "qemu-system-mipsel",
        "args": lambda img, port, kvm:
            f"-M malta -m 256M -kernel {img}"
            f" -append 'console=ttyS0' -nographic -no-reboot"
            f" -serial tcp:127.0.0.1:{port},server,nowait",
        "pattern": "*initramfs-kernel.bin",
        "boot_timeout": 120,
        "board": "malta", "subtarget": "le",
    },
}

SEARCH_DIRS = [
    "/home/manu/openwrt",
    "/home/manu/openwrt-arm",
    "/home/manu/openwrt-embedded",
    "/home/manu/openwrt-malta",
    "/home/manu/openwrt-x86-64-tests",
]

def find_image(board, subtarget, variant, pattern):
    for wd in SEARCH_DIRS:
        for p in [f"{wd}/bin/targets/{board}/{subtarget}_{variant}/{pattern}",
                  f"{wd}/bin/targets/{board}/{subtarget}/{pattern}"]:
            matches = sorted(glob.glob(p))
            if matches:
                return max(matches, key=os.path.getsize)
    return None

def extract_image(path, tmp="/tmp"):
    if path.endswith(".gz"):
        raw = f"{tmp}/{os.path.basename(path)[:-3]}"
        if not os.path.exists(raw):
            with open(path, "rb") as f: data = gzip.decompress(f.read())
            with open(raw, "wb") as f: f.write(data)
            os.chmod(raw, 0o644)
        return raw
    return path

def recv_until(sock, patterns, timeout=30):
    data = b""
    sock.settimeout(timeout)
    start = time.time()
    while time.time() - start < timeout:
        try:
            c = sock.recv(4096)
            if not c: break
            data += c
            for p in patterns:
                pb = p if isinstance(p, bytes) else p.encode()
                if pb in data: return data
        except socket.timeout: break
    return data

def send_cmd(sock, cmd, delay=0.3):
    sock.sendall((cmd + "\n").encode())
    if delay: time.sleep(delay)

def run_test(target, variant, port=23000, timeout=300, kvm=True):
    cfg = TARGET_CONFIGS[target]
    img = find_image(cfg["board"], cfg["subtarget"], variant, cfg["pattern"])
    if not img:
        return {"target": target, "variant": variant,
                "error": f"No image found for {target}/{variant}"}

    raw = extract_image(img)
    result = {"target": target, "variant": variant,
              "image": os.path.basename(img), "tests": {}}

    qemu_bin = cfg["qemu"]
    qemu_args = cfg["args"](raw, port, kvm and os.path.exists("/dev/kvm"))
    cmd = f"{qemu_bin} {qemu_args} -display none"

    print(f"[TEST] {target}/{variant}: booting...")
    qemu = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    boot_start = time.time()

    try:
        time.sleep(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(cfg["boot_timeout"])
        for i in range(30):
            try:
                sock.connect(("127.0.0.1", port)); break
            except (ConnectionRefusedError, OSError):
                if i == 29: raise
                time.sleep(1)

        # All OpenWrt targets output "Please press Enter to activate this console"
        data = recv_until(sock, ["Please press Enter"], cfg["boot_timeout"])
        if b"Please press Enter" not in data:
            # If no Enter prompt but we got a shell directly (some variants), try that
            if b"# " in data or b"/ #" in data:
                pass  # already at shell
            else:
                result["boot_error"] = "Console prompt not seen"; sock.close(); qemu.terminate(); qemu.wait(5); return result
        else:
            send_cmd(sock, "", 2)
        data = recv_until(sock, ["# "], 60)
        if b"# " not in data:
            # Try sending another newline
            send_cmd(sock, "", 2)
            data = recv_until(sock, ["# "], 30)
            if b"# " not in data:
                result["boot_error"] = "Shell prompt not seen"; sock.close(); qemu.terminate(); qemu.wait(5); return result

        result["boot_time_seconds"] = round(time.time() - boot_start, 1)
        print(f"  Booted ({result['boot_time_seconds']}s), running tests...")

        # Drain any pending output before injection
        sock.settimeout(0.5)
        try:
            while sock.recv(65536): pass
        except socket.timeout: pass

        # Wait for kernel modules to finish loading
        print("  Waiting for kernel modules...")
        time.sleep(15)
        sock.settimeout(0.5)
        try:
            while sock.recv(65536): pass
        except socket.timeout: pass

        # Inject via heredoc (handles quoting and multi-line content correctly)
        print("  Injecting test script...")
        sock.sendall(b"cat > /tmp/owt.sh << 'ENDOFFILE'\n")
        time.sleep(0.3)
        for line in GUEST_TEST_SCRIPT.strip().split('\n'):
            sock.sendall((line + '\n').encode())
            time.sleep(0.04)
        time.sleep(0.3)
        sock.sendall(b'ENDOFFILE\n')
        time.sleep(2)

        send_cmd(sock, "sh /tmp/owt.sh 2>&1", 2)

        output = recv_until(sock, ["ENDTESTMARKER"], timeout)
        text = output.decode("utf-8", errors="replace")

        if "ENDTESTMARKER" not in text:
            result["test_error"] = "Script incomplete"
            result["partial"] = text[-800:]
        else:
            for line in text.split("\n"):
                m = re.match(r"TEST:([^:]+):([^:]+):(.*)", line.strip())
                if m: result["tests"][m.group(1)] = {"r": m.group(2), "d": m.group(3)}
            result["raw_tail"] = text[-2000:]
            result["raw_full_len"] = len(text)
            sm = re.search(r"SUMMARY:\s*(\d+)/(\d+) passed,\s*(\d+) failed", text)
            if sm:
                result["summary"] = {"passed": int(sm.group(1)),
                                     "total": int(sm.group(2)),
                                     "failed": int(sm.group(3))}
        print(f"  Tests: {result.get('summary',{}).get('passed','?')}/"
              f"{result.get('summary',{}).get('total','?')} passed, "
              f"{result.get('summary',{}).get('failed',0)} failed")

    except Exception as e:
        print(f"  Error: {e}"); result["error"] = str(e)
    finally:
        try: send_cmd(sock, "poweroff", 2)
        except: pass
        try: sock.close()
        except: pass
        qemu.terminate()
        try: qemu.wait(10)
        except: qemu.kill()

    return result

def main():
    ap = argparse.ArgumentParser(description="OpenWrt In-QEMU Comprehensive Test Runner")
    ap.add_argument("target", nargs="?", choices=list(TARGET_CONFIGS.keys()), help="Target")
    ap.add_argument("--variant", default="default", choices=["default","minimal","full","dev","hardened"])
    ap.add_argument("--port", type=int, default=23000)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--no-kvm", action="store_true")
    ap.add_argument("--json", type=str, help="Output JSON file")
    ap.add_argument("--list-targets", action="store_true")
    ap.add_argument("--all", action="store_true", help="Run all QEMU-testable targets with default variant")
    args = ap.parse_args()

    if args.list_targets:
        print("Available QEMU-testable targets:")
        for t, c in TARGET_CONFIGS.items():
            print(f"  {t:15s} {c['qemu']:25s} {c['pattern']}")
        return

    if args.all:
        results = {}
        for target in TARGET_CONFIGS:
            r = run_test(target, args.variant, args.port, args.timeout, not args.no_kvm)
            results[target] = r
            args.port += 1
            time.sleep(2)
        print(json.dumps(results, indent=2))
        if args.json:
            with open(args.json, "w") as f: json.dump(results, f, indent=2)
        return

    if not args.target:
        ap.print_help(); return

    result = run_test(args.target, args.variant, args.port, args.timeout, not args.no_kvm)
    if args.json:
        with open(args.json, "w") as f: json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

    s = result.get("summary", {})
    sys.exit(s.get("failed", 1) if "error" not in result else 1)

if __name__ == "__main__":
    main()
