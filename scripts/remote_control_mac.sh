#!/bin/bash
# Start a Claude Code Remote Control session on macOS, reachable from iPad/iPhone
# (Claude app → Code). Ensures TradingView runs with CDP first, and keeps the Mac
# awake for as long as the session is open.
# Usage: ./scripts/remote_control_mac.sh [port]

PORT="${1:-9222}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

if ! command -v claude > /dev/null 2>&1; then
  echo "Error: 'claude' CLI not found. Install it: npm install -g @anthropic-ai/claude-code"
  exit 1
fi

# Launch TradingView with CDP only if it is not already reachable
if curl -s "http://localhost:$PORT/json/version" > /dev/null 2>&1; then
  echo "CDP already up at http://localhost:$PORT"
else
  "$SCRIPT_DIR/launch_tv_debug_mac.sh" "$PORT" || echo "Warning: TradingView/CDP not ready; chart tools will fail until it is."
fi

cd "$REPO_DIR" || exit 1
echo "Starting Remote Control in $REPO_DIR (Mac kept awake until you quit with Ctrl+C)..."
# caffeinate -dimsu: no display/idle/disk/system sleep while claude runs
exec caffeinate -dimsu claude remote-control
