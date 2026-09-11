#!/bin/bash
git commit --amend --author="google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>" -m "scripts: 🛡️ Sentinel: [CRITICAL] Fix command injection in dump-target-info.pl

🚨 Severity: CRITICAL
💡 Vulnerability: Command injection was possible in scripts/dump-target-info.pl via the subtarget argument. The script directly interpolated user-controlled input into shell commands executed via the 2-argument open function (e.g., open M, \"make -C '\$target_dir' ... SUBTARGET='\$subtarget' |\").
🎯 Impact: If an attacker can control the subtarget argument passed to the script, they could inject malicious shell metacharacters (e.g., foo'; id; #) and execute arbitrary commands with the privileges of the script.
🔧 Fix: Introduced a shell_quote subroutine to safely escape single quotes and wrap strings in single quotes. Applied this function to all instances where \$target_dir and \$subtarget are interpolated into shell commands.
✅ Verification: Verified by attempting the exploit locally (./scripts/dump-target-info.pl devices \"foo/bar'; id > /tmp/id; #\") and confirming that /tmp/id is no longer created, and by successfully running make help and perl -c scripts/dump-target-info.pl to ensure no functionality is broken.

Signed-off-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>"
