## 2024-05-19 - Fast OPKG Status Parsing
**Learning:** Parsing tens of thousands of RFC 822-style blocks (like opkg package indices or SBOMs) in Python by repeatedly calling `splitlines()` and creating an intermediate dictionary for each block causes massive memory allocations and parsing overhead.
**Action:** Use index-based string searching (`str.find('Key: ', start, end)`) and direct string slicing to extract exactly the fields needed, bypassing dictionary construction and reducing execution time by over 60%.
