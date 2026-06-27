#!/usr/bin/env bash
#
# check-js-syntax.sh -- fail fast on invalid JavaScript.
#
# Catches the class of corruption that has slipped through before: heredoc
# escaping artifacts (\` and \${ in template literals), truncated/duplicated
# blocks, etc. Runs `node --check` (parse only -- no execution) on each file.
#
# Usage:
#   scripts/check-js-syntax.sh                # check all tracked frontend JS
#   scripts/check-js-syntax.sh f1.js f2.js    # check only the given files
#
# Exit code: non-zero if any file fails to parse (or node is unavailable).

set -u

if ! command -v node >/dev/null 2>&1; then
  echo "check-js-syntax: 'node' not found on PATH; cannot validate JS." >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root" || exit 2

# Collect target files.
files=()
if [ "$#" -gt 0 ]; then
  for f in "$@"; do
    case "$f" in
      *.js) [ -f "$f" ] && files+=("$f") ;;
    esac
  done
else
  while IFS= read -r f; do
    files+=("$f")
  done < <(find frontend/assets/js frontend/components -name '*.js' 2>/dev/null)
fi

if [ "${#files[@]}" -eq 0 ]; then
  echo "check-js-syntax: no JS files to check."
  exit 0
fi

fail=0
for f in "${files[@]}"; do
  if ! out=$(node --check "$f" 2>&1); then
    fail=$((fail + 1))
    echo "FAIL  $f"
    echo "$out" | sed 's/^/      /' | head -4
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "check-js-syntax: $fail file(s) failed to parse." >&2
  exit 1
fi

echo "check-js-syntax: OK (${#files[@]} file(s) parsed cleanly)."
