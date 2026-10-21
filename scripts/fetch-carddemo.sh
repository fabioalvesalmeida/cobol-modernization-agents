#!/usr/bin/env bash
# Fetch the AWS CardDemo sample (Apache-2.0) used by the examples. Not vendored in this repo.
set -euo pipefail
DEST="${1:-vendor/carddemo}"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  git clone --depth 1 https://github.com/aws-samples/aws-mainframe-modernization-carddemo "$DEST"
fi
echo "CardDemo at $DEST (commit $(git -C "$DEST" rev-parse --short HEAD))"
