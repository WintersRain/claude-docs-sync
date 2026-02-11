# Parallel Subagents (Agent Swarms) — Troubleshooting Guide

## What Are Parallel Subagents?
Claude Code can spawn multiple specialized subagents simultaneously using the **Task tool**. Each subagent gets its own context window, runs independently, and returns results to the main session. This is how skills like `/essentials:analyze` dispatch 8+ reviewers at once.

## How It Works
- The main Claude session sends multiple `Task` tool calls in a **single message**
- Each Task specifies a `subagent_type` (e.g., a custom agent from a plugin or built-in like `general-purpose`, `Explore`)
- Claude Code runs them concurrently — you see colored spinners for each active agent
- Results return to the main session as each agent finishes

## The #1 Mistake: Sending Tasks One at a Time
If Claude sends Task calls across multiple messages (one per message), they run **sequentially**, not in parallel. This wastes tokens and time.

**Wrong** (sequential — each waits for the previous):
```
Message 1: Task → Agent A
Message 2: Task → Agent B
Message 3: Task → Agent C
```

**Right** (parallel — all run at once):
```
Message 1: Task → Agent A + Task → Agent B + Task → Agent C
```

**Fix:** If Claude keeps sending one agent at a time, tell it:
> "Send ALL Task calls in a single message. Do not send one at a time."

## Troubleshooting Checklist

### Agents aren't running in parallel
- [ ] Confirm Claude is sending all Task tool calls in **one message**, not spread across multiple
- [ ] Keep prompts short — long prompts slow down message assembly and can cause partial sends
- [ ] Check if you're hitting a model-specific tool call limit per message

### Subagent type not recognized
- [ ] Run `/agents` to see all available subagent types (built-in + plugin + user-defined)
- [ ] Plugin agents require the plugin to be installed first (`/plugin list` to check)
- [ ] Custom agents must be `.md` files in `~/.claude/agents/` (user-level) or `.claude/agents/` (project-level)
- [ ] Agents are loaded at session start — restart Claude Code after adding new agent files, or use `/agents` to reload

### Plugin marketplace setup (for plugin-provided agents)
1. Install GitHub CLI: `winget install GitHub.cli` (Windows) or `brew install gh` (macOS)
2. Authenticate: `gh auth login` → choose GitHub.com → HTTPS → paste your PAT
3. If using enterprise GitHub (EMU): go to github.com/settings/tokens → find your PAT → **Configure SSO** → Authorize for your org
4. Add marketplace: `/plugin marketplace add <repo-url>`
5. Install plugin: `/plugin install <plugin-name>`
6. Restart Claude Code to load new agents

### Agent Teams vs. Subagents
These are two different systems:

| | Subagents (Task tool) | Agent Teams |
|---|---|---|
| **How** | Task tool calls within one session | Separate Claude Code instances |
| **Context** | Own context, results return to main | Fully independent sessions |
| **Communication** | Report back to main agent only | Can message each other directly |
| **Token cost** | Lower (results summarized back) | Higher (each is a full session) |
| **Setup** | Works by default | Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| **Best for** | Focused parallel tasks (review, analyze) | Complex collaborative work (multi-file features, debates) |

**Enable Agent Teams:**
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```
Or add to settings.json:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Local documentation cache
Keep Claude Code docs available locally so Claude always knows about subagents and agent teams:
```bash
git clone https://github.com/WintersRain/claude-docs-sync.git
python fetch-docs.py
```
Downloads ~56 pages to `~/.claude/docs/claude-code/`. Run `python fetch-docs.py --update` periodically to pull changes.

## Quick Reference: Dispatching Parallel Subagents

When you want Claude to run multiple agents in parallel, be explicit:

> "Launch 8 analyzer agents in parallel. Send ALL Task calls in a single message. Use short prompts. Use haiku model for speed."

Key parameters per Task call:
- `subagent_type` — which agent to use
- `model` — `haiku` (fast/cheap), `sonnet` (balanced), `opus` (strongest), or omit to inherit
- `run_in_background` — set `true` to continue working while agents run
- `prompt` — keep it concise when dispatching many agents

## Creating Custom Subagents for Parallel Use

Create a `.md` file in `~/.claude/agents/`:

```markdown
---
name: my-reviewer
description: Reviews code for security issues
tools: Read, Grep, Glob, Bash
model: haiku
---

You are a security reviewer. Analyze the provided code and report:
- Key Findings (3-5 bullets)
- Risks (if any)
- Recommendation (1-2 sentences)
```

Then dispatch it alongside other agents:
```
Use my-reviewer, code-reviewer, and debugger agents in parallel to analyze src/auth.js
```
