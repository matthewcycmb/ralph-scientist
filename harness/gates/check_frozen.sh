#!/usr/bin/env bash
# Gate: the local model and both frozen-data inputs still match their declared hashes.
set -euo pipefail

check_set() {
  local dir="$1"
  [[ -f "$dir/CHECKSUMS.txt" ]] || {
    echo "FAIL: $dir/CHECKSUMS.txt missing"
    return 1
  }
  (cd "$dir" && shasum -a 256 -c CHECKSUMS.txt)
}

check_set data/models
check_set data/cache/nlsy97
echo "PASS: frozen model and fallback dataset match their declared checksums"
