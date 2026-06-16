## 2025-06-14 - Fix Potential Command Injection in unetd
**Vulnerability:** Shell command injection in `unet.uc` where `bin_path` and `out_file` variables were directly interpolated into `system([ "sh", "-c", "..." ])` without escaping.
**Learning:** Even if input variables are validated via regex earlier in the code, injecting them unquoted or using single quotes without escaping them directly into `sh -c` introduces a vulnerability pattern if those validations are ever bypassed, refactored, or missed.
**Prevention:** Always escape shell variables using `replace(var, /'/g, "'\\''")` and enclose them in single quotes when interpolating into `sh -c`, or better yet, avoid `sh -c` entirely by using array-based execution when I/O redirection is not required.
