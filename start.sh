#!/data/data/com.termux/files/usr/bin/bash
# start.sh — Load environment variables and launch TermiHub.
#
# Usage:
#   bash start.sh
#
# On first run, copy .env.example to ~/.termihub.env and fill in your values.

set -euo pipefail

ENV_FILE="$HOME/.termihub.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found."
  echo ""
  echo "Create it from the template:"
  echo "  cp $(dirname "$0")/.env.example $ENV_FILE"
  echo "  nano $ENV_FILE"
  exit 1
fi

# Source the env file — every line that is VAR=value is exported.
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [[ ! -d "$VENV" ]]; then
  echo "Virtual environment not found. Run setup.sh first."
  exit 1
fi

echo "Starting $TERMIHUB_BOT_NAME..."
exec "$VENV/bin/python" "$SCRIPT_DIR/bot.py"
