# claude-docs-sync

Keep a local cache of the [Claude Code documentation](https://code.claude.com/docs) so Claude always has access to up-to-date reference material.

## What it does

- Downloads all ~54 pages of Claude Code docs as raw markdown to `~/.claude/docs/claude-code/`
- Checks for updates using HTTP `Last-Modified` headers (lightweight HEAD requests)
- Optionally schedules a daily check via `claude -p` so Claude itself handles the update

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (for the scheduled auto-update)
- Python 3.6+

## Quick Start

### Windows

```
setup.bat
```

### macOS / Linux

```bash
chmod +x setup.sh
./setup.sh
```

The setup script:
1. Copies `fetch-docs.py` to `~/.claude/`
2. Downloads all documentation pages
3. Schedules a daily update check at 9:00 AM

## Manual Usage

```
python ~/.claude/fetch-docs.py           # Download all docs (full refresh)
python ~/.claude/fetch-docs.py --check   # Check what's changed (HEAD requests only)
python ~/.claude/fetch-docs.py --update  # Download only changed pages
```

## How the daily check works

The scheduled task runs:

```
claude -p "check if docs updated, pull down changes"
```

This starts a headless Claude Code session that runs the check script and exits. On Windows it uses Task Scheduler; on macOS/Linux it uses cron.

## Where docs are stored

```
~/.claude/
  fetch-docs.py          # The sync script
  docs/
    claude-code/
      _index.md           # Page manifest
      llms.txt            # Raw upstream index
      hooks.md            # Individual doc pages...
      skills.md
      sub-agents.md
      settings.md
      ...
```

## Uninstall

### Windows
```powershell
Unregister-ScheduledTask -TaskName 'ClaudeDocsUpdate' -Confirm:$false
del %USERPROFILE%\.claude\fetch-docs.py
del %USERPROFILE%\.claude\check-docs.bat
rmdir /s %USERPROFILE%\.claude\docs\claude-code
```

### macOS / Linux
```bash
crontab -l | grep -v "check-docs.sh" | crontab -
rm ~/.claude/fetch-docs.py ~/.claude/check-docs.sh
rm -rf ~/.claude/docs/claude-code
```

## License

MIT
