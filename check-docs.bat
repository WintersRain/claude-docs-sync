@echo off
claude -p "Run python %USERPROFILE%/.claude/fetch-docs.py --check to check if the Claude Code docs have updated. If there are updates, run python %USERPROFILE%/.claude/fetch-docs.py --update to pull them down. If everything is up to date, just say so and exit."
