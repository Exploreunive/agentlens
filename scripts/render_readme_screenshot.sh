#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HTML_PATH="${1:-$ROOT_DIR/artifacts/latest_trace.html}"
OUT_PATH="${2:-$ROOT_DIR/docs/assets/langgraph-trace-real.png}"
WINDOW_SIZE="${WINDOW_SIZE:-1600,1200}"

CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome not found at: $CHROME_BIN" >&2
  exit 1
fi

if [[ ! -f "$HTML_PATH" ]]; then
  echo "HTML trace not found: $HTML_PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT_PATH")"

"$CHROME_BIN" \
  --headless \
  --disable-gpu \
  --window-size="$WINDOW_SIZE" \
  --screenshot="$OUT_PATH" \
  "file://$HTML_PATH"

echo "Wrote $OUT_PATH"
