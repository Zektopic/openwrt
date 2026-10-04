# Zektopic OpenWrt Fork

This is the Zektopic fork of [OpenWrt](https://github.com/openwrt/openwrt) — the leading open-source Linux distribution for embedded devices and routers.

See [the October 2026 repair report](REPAIR_REPORT.md) for current changes and
verified results, and [the build helpers](TEST_SCRIPTS/README.md) for usage.
The PR #75 build, security, and optimization reports below are historical;
they do not establish test coverage for the current revision.

## Purpose

This fork maintains the core OpenWrt build system while adding custom security hardening and performance optimizations.

## Key Changes vs Upstream

### Security Fixes (Sentinel Series)
- **wireguard.uc** — Argument-vector execution and validated, quoted pipe commands compatible with the pinned ucode interpreter
- **ead/button-hotplug** — Buffer overflow fixes (strcpy → strscpy/strncpy)
- **provision.uc** — Command injection prevention
- **trelay** — TOCTOU and buffer overflow hardening
- **nvram.c** — Alignment and overflow safety
- **tinysrp** — Multiple security fixes
- **ead-client** — Bounds check hardening

### Script Optimizations (Bolt Series)
Memory usage reductions across Python build scripts via:
- Chunked/streamed I/O (belkin-header.py, cameo-imghdr.py, netgear-encrypted-factory.py)
- Set operations for intersection checks (b43-fwsquash.py)
- Dictionary grouping (dl_cleanup.py)
- String slicing (make-index-json.py)
- CSV parsing (sercomm-payload.py)

## Directory Structure

```
.zektopic/
  README.md                         # This file
  REPAIR_REPORT.md                  # Current repair and validation results
  BUILD_REPORT.md                   # Historical PR #75 report
  CONFLICT_RESOLUTION.md            # How PR #75 conflicts were resolved
  SECURITY_CHANGES.md               # Security fix details
  OPTIMIZATION_CHANGES.md           # Script optimization details
  UPSTREAM_CHANGES.md               # Upstream changes merged
  MANIFEST.md                       # Full change inventory
  TEST_SCRIPTS/                     # Build/test automation
    build_x86_64.sh
    build_ath79.sh
    build_mediatek.sh
    build_ramips.sh
    verify_merge.sh
    smoke_test.sh
```
