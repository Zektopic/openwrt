## 2024-05-24 - Unsafe Buffer Formatting with sprintf
**Vulnerability:** The `nvram` C utility used `sprintf` to write formatted strings directly into statically allocated character arrays (`char buf[]` or `char dev[PATH_MAX]`), without passing maximum bound limits.
**Learning:** Even if the input parameters format constraints implicitly seem short enough, relying on implicit bounds with `sprintf` is inherently unsafe and leads to buffer overflows if inputs mutate. OpenWrt utilities require bounds checking for robust security posture.
**Prevention:** Always replace `sprintf` with `snprintf`, passing the exact allocation size (`sizeof(buf)`) or dynamically calculated remainder (`end - ptr`) to prevent accidental or malicious buffer overflows.
