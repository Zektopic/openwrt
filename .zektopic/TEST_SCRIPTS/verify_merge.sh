#!/usr/bin/env bash
# Run local regression checks from any working directory.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."

if [[ -n $(git diff --name-only --diff-filter=U) ]]; then
    echo 'Unresolved merge conflicts remain.' >&2
    exit 1
fi
if git grep -n -E '^(<<<<<<< |>>>>>>> )' -- ':!.zektopic/TEST_SCRIPTS/verify_merge.sh'; then
    echo 'Merge conflict markers remain.' >&2
    exit 1
fi
git diff --check
git diff --cached --check
python3 -m pytest -q
for script in scripts/feeds scripts/download.pl scripts/timestamp.pl; do
    perl -I scripts -c "$script"
done
for script in .zektopic/TEST_SCRIPTS/*.sh; do
    bash -n "$script"
done
echo 'Local regression checks passed. Firmware builds and hardware boot tests are separate checks.'
