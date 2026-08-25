#!/data/data/com.termux/files/usr/bin/bash
# setup.sh — One-time environment setup for TermiHub in Termux.
#
# Run this once after cloning/copying the project:
#   bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

echo "=== TermiHub setup ==="
echo ""

# ── 1. Termux packages ────────────────────────────────────────────────────────
echo "[1/4] Updating package list and installing system packages..."
pkg update -y
pkg install -y python iproute2 termux-api
# termux-api provides the termux-* CLI tools.
# iproute2 provides the `ip` command for /ip handler.

# ── 2. Python virtual environment ─────────────────────────────────────────────
echo ""
echo "[2/4] Creating Python virtual environment at $VENV..."
python -m venv "$VENV"

# ── 3. Python dependencies ────────────────────────────────────────────────────
echo ""
echo "[3/4] Installing Python dependencies..."
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# ── 4. Env file ───────────────────────────────────────────────────────────────
echo ""
echo "[4/4] Checking for environment file..."
ENV_FILE="$HOME/.termihub.env"
if [[ -f "$ENV_FILE" ]]; then
  echo "  Found existing $ENV_FILE — skipping copy."
else
  cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
  echo "  Created $ENV_FILE from template."
  echo ""
  echo "  *** ACTION REQUIRED ***"
  echo "  Edit $ENV_FILE and fill in:"
  echo "    TERMIHUB_BOT_TOKEN   — from @BotFather"
  echo "    TERMIHUB_ALLOWED_IDS — your Telegram user ID (from @userinfobot)"
  echo "  Then run:  bash start.sh"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit ~/.termihub.env with your bot token and user ID"
echo "  2. Install the Termux:API companion app from F-Droid"
echo "     (required for /battery, /wifi, /temperature)"
echo "  3. Run:  bash start.sh"
