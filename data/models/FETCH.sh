#!/usr/bin/env bash
# Re-fetch the frozen model weights (too big for git; identity pinned by CHECKSUMS.txt).
# Run once at setup; verify: shasum -a 256 -c CHECKSUMS.txt
set -euo pipefail
cd "$(dirname "$0")"
curl -L -o qwen2.5-0.5b-instruct-q8_0.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q8_0.gguf"
shasum -a 256 -c CHECKSUMS.txt
