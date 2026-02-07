#!/bin/bash
echo "Installing claude-docs-sync..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Copy fetch script
cp "$SCRIPT_DIR/fetch-docs.py" ~/.claude/fetch-docs.py
cp "$SCRIPT_DIR/check-docs.sh" ~/.claude/check-docs.sh
chmod +x ~/.claude/check-docs.sh

# Initial download
echo
echo "Running initial docs download..."
python3 ~/.claude/fetch-docs.py

# Schedule daily check (cron)
echo
echo "Setting up daily cron job (9:00 AM)..."
CRON_CMD="0 9 * * * ~/.claude/check-docs.sh >/dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "check-docs.sh"; echo "$CRON_CMD") | crontab -

echo
echo "Done! Docs saved to ~/.claude/docs/claude-code/"
echo "Daily update check scheduled at 9:00 AM via cron."
echo
echo "Manual commands:"
echo "  python3 ~/.claude/fetch-docs.py           Full download"
echo "  python3 ~/.claude/fetch-docs.py --check   Check for updates"
echo "  python3 ~/.claude/fetch-docs.py --update  Download only changes"
