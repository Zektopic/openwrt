# Build and test helpers

Run these scripts from any working directory. Install the build prerequisites
and update/install feeds as described in the repository README first. Missing
prerequisites stop the build; `FORCE=1` is not part of the normal workflow.

## Local checks

```sh
bash .zektopic/TEST_SCRIPTS/verify_merge.sh
python3 scripts/check-target-configs.py
python3 scripts/check-target-configs.py x86/64 mediatek/filogic
```

The configuration check requires an initial `make defconfig`. It writes one
configuration and diagnostic log per target, plus `results.json`, under
`logs/target-configs/`. It preserves the active `.config`. It checks the targets
advertised by `scripts/dump-target-info.pl`, which excludes broken and
source-only targets; device counts describe selectable profiles, not boot tests.

## Firmware builds

```sh
JOBS=2 bash .zektopic/TEST_SCRIPTS/build_x86_64.sh
ALL_PROFILES=1 JOBS=2 bash .zektopic/TEST_SCRIPTS/build_mediatek.sh
JOBS=2 bash .zektopic/TEST_SCRIPTS/build_target.sh ramips mt7621
DEVICE=generic JOBS=2 bash .zektopic/TEST_SCRIPTS/build_target.sh x86 64
```

The wrappers for x86/64, MediaTek Filogic, ath79/generic and ramips/mt7621 share
`build_target.sh`. `DEVICE` selects a profile identifier from OpenWrt's generated
configuration. `ALL_PROFILES=1` selects all available profiles. Use one of these
options at a time. The default concurrency is two jobs; adjust `JOBS` for your
machine's memory and CPU capacity.

Build helpers replace `.config` with the requested selection and save its
previous contents under `logs/build-helper/`. An optional final `clean` argument
runs `make clean` first. Build logs also go under `logs/build-helper/`; firmware
images go to the standard `bin/targets/<target>/<subtarget>/` directory. Builds
for different targets must use separate checkouts when run concurrently.

For a full build across the supported device profiles, manually run the
**Test Build All Devices** GitHub workflow with `targets=all`. Selected pairs
such as `x86/64 ath79/generic` are also accepted. The maintained upstream build
workflow supplies tools and toolchains and retains build artifacts.

## QEMU boot checks

```sh
bash .zektopic/TEST_SCRIPTS/smoke_test.sh bin/targets/x86/64/<ext4-combined-efi.img.gz>
TIMEOUT=180 bash .zektopic/TEST_SCRIPTS/qemu_test.sh x86_64
bash .zektopic/TEST_SCRIPTS/qemu_test.sh malta_be
bash .zektopic/TEST_SCRIPTS/qemu_test.sh armsr_armv8
```

Install the appropriate QEMU system emulator and, for x86 EFI images, OVMF.
The x86 helper detects common OVMF installations; `OVMF` can specify a monolithic
firmware file. `armvirt_32` and `armvirt_64` remain aliases for the current
`armsr_armv7` and `armsr_armv8` targets. ARM and Malta checks require an initramfs
kernel.

Boot checks use temporary disk snapshots, disable networking, and save console
logs under `logs/qemu/` (`LOG` overrides the path). They pass only after the
guest reaches the console and no fatal kernel error appears. The default
timeout is 120 seconds. Exit status 0 means pass, 1 means failure or incomplete
boot, 2 means invalid arguments, and 77 means a required emulator/firmware is
missing. A skip is not a successful boot. These checks do not validate a
physical router's Wi-Fi, Ethernet, flash layout or upgrade behavior.
