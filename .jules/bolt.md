## 2024-05-24 - [Avoid `email.parser` for large package indexes]
**Learning:** `email.parser.Parser` performs full RFC 822/2822 compliance checks which adds massive overhead. When parsing tens of thousands of machine-generated opkg package index blocks with predictable `Key: Value` line formats, standard string splitting and `.startswith()` checks provide a ~14x speedup.
**Action:** When extracting a few specific headers from a trusted and uniform block format instead of parsing arbitrary emails, avoid `email.parser.Parser` and use fast native python string operations instead. Make sure to use `.strip()` when parsing values to correctly handle `\r\n` line endings.

## 2024-03-15 - [Python regex optimization in JSON info file script]
**Learning:** Pre-compiling regexes outside of loops in Python utility scripts (`scripts/`) is a safe micro-optimization that yields measurable speedups (~50% faster matching) and avoids repeatedly hitting Python's internal regex cache.
**Action:** When working on Python scripts that iterate over many files or lines and use `re.match` or `re.search` with a static pattern, pre-compile the pattern using `re.compile()` outside the loop.
