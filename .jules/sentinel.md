## 2024-03-13 - [Fix SSL Certificate Verification in GitHub Archive Downloader]
**Vulnerability:** `scripts/dl_github_archive.py` created an unverified SSL context (`ssl._create_unverified_context()`) when making requests to the GitHub API, disabling SSL/TLS certificate verification. This left the script vulnerable to Man-in-the-Middle (MITM) attacks.
**Learning:** This vulnerability existed likely to bypass SSL errors on developer machines with outdated or missing CA certificates.
**Prevention:** Always use `ssl.create_default_context()` or let the system use its default verified context when making HTTPS requests. Do not disable SSL verification in production scripts, especially when downloading source code archives.
