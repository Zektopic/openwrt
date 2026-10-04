# October 2026 repair and validation

This report records the repair of the fork starting at `1fdce528228e` and the
integration of [upstream PR #287](https://github.com/Zektopic/openwrt/pull/287),
including upstream commit `5edcc1c43cb9`. Older reports in this directory describe
the previous PR #75 work and are not evidence of current test results.

## Repairs

- Restored prerequisite failures instead of automatically forcing the build to
  proceed. Restored the upstream kernel/package CI integration and host-tool
  selection logic.
- Combined upstream timestamp fast paths with safe argument handling, fractional
  modification times, newline-containing filenames, and reliable failure
  handling. Preserved streamed Belkin image generation and reproducible timestamps.
- Fixed opkg metadata parsing, Aruba zero-checksum images, and the NETGEAR FIT
  padding tool's output path. Restored test cases hidden by duplicate class names.
- Repaired Wi-Fi MAC generation, WireGuard setup/key generation, and UBI
  provisioning against the **pinned** ucode interpreter. That version accepts
  strings in `fs.popen()`, so pipe commands now use validated/quoted arguments;
  argument-vector `system()` calls remain in use where supported.
- Fixed NVRAM serialization at partition boundaries. Oversized configurations
  fail before changing mapped storage; accepted images have bounded lengths,
  initialized alignment padding, and valid checksums. A failed staging commit
  cannot proceed to flash.
- Restored authenticated EAD shell command semantics. The fork's custom tokenizer
  broke escaped spaces, pipelines, and variable assignments. Oversized commands
  are rejected instead of silently truncated, and the client/server length
  boundary includes the terminating NUL consistently.
- Removed obsolete root-level patch/commit helper scripts and replaced hardcoded
  build paths and unconditional success checks in the fork's test helpers.

## Device support and build features

Upstream contributes current device definitions and drivers, including TP-Link
RE700X support and Realtek IPv6 route offload. This repair adds:

- One build helper for any supported target/subtarget, optional single-device or
  all-profile selection, configuration backups, configurable concurrency, and
  build logs.
- A repeatable configuration sweep with per-target logs and JSON results.
- A manual full-device GitHub Actions matrix covering every advertised
  target/subtarget, with all profiles selected and two concurrent builds.
- EFI x86 boot checks and ARM/Malta initramfs helpers using temporary snapshots,
  console detection, explicit skip results, and fatal-error detection.
- Regression CI on Python 3.8, 3.12, and 3.14, including native C tests, the pinned
  ucode runtime, and configuration coverage for all supported targets.

See [the helper documentation](TEST_SCRIPTS/README.md) for commands.

## Validation

The local checks use no `FORCE=1` build override. The C tests use memory and
subprocesses, and ucode tests use command stubs; neither writes to a real router.

| Check | Result |
| --- | --- |
| Python 3.14 with pinned ucode and C dependencies | 168 passed; 2 subtests passed |
| Python 3.8 with C dependencies | 164 passed; 4 ucode tests skipped because that container lacks ucode |
| NVRAM boundary, round-trip, padding, and CRC checks | 21 passed; 12 failed before the repair |
| EAD shell command checks | 5 passed; 4 failed before the repair |
| Wi-Fi, WireGuard, and provisioning runtime checks | 4 passed; 4 failed before the repair |
| Ruff duplicate-definition/undefined-name checks | Passed |
| Workflow validation with actionlint | Passed |
| Shell and Perl syntax checks | Passed |
| All supported target/subtarget configurations | 97/97 passed; 2117 selectable device profiles |
| Host tools build | Passed |
| Native EAD daemon and client build after autoreconf | Passed |
| x86/64 firmware build and EFI QEMU boot | Images built; guest reached the OpenWrt console |

Build and regression logs are retained locally under `logs/repair/`, and firmware
artifacts under `bin/targets/x86/64/`. These generated files and signing keys are
excluded from Git. The Python 3.14 run reports one `argparse.FileType` pending
deprecation warning in the existing Cameo tool.

Configuration coverage establishes that target/device selections resolve. It
does not establish that every firmware image compiles or that physical routers
boot. Only x86/64 has been built and booted locally in this repair. ARM/Malta
helpers have orchestration tests but have not been booted with new images here.
Physical Wi-Fi, Ethernet, flash layout, and upgrade behavior require the matching
devices; no physical device was flashed.
