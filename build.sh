#!/usr/bin/env bash
# Re-render the PDF from slides.html.
# Requires: macOS Chrome at /Applications/Google Chrome.app/.
# Output:  output/food-delivery-domain.pdf

set -euo pipefail
cd "$(dirname "$0")"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRC="file://$PWD/slides/slides.html?print=1"
OUT="$PWD/output/food-delivery-domain.pdf"

mkdir -p output
"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf-no-header \
  --print-to-pdf="$OUT" \
  --virtual-time-budget=4000 \
  "$SRC"

echo "→ $OUT ($(du -h "$OUT" | cut -f1))"
