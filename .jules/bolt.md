## 2024-05-15 - Early Package Filtering in make-sbom.py
**Learning:** In the `get_apk_sbom` function parsing large JSON package lists, creating an empty dictionary (`element = {}`) and extracting multiple properties before checking the `installed` filter caused unnecessary overhead for packages that were ultimately skipped.
**Action:** Move exclusion filters as early as possible in loops parsing large collections. Extracting just the `name` and immediately applying the `installed` filter avoids creating the new dictionary object and evaluating subsequent conditions for skipped items.
