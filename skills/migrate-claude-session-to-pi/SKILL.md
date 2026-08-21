---
name: migrate-claude-session-to-pi
description: Convert a Claude Code session (.claude/projects/.../*.jsonl) into a resumable pi session JSONL, so it can be opened with `pi --resume`. Builds a programmatic summary of early history plus a faithful recent conversation with Claude tool calls mapped to pi tools. Use when migrating Claude Code conversations to pi, or when you need to understand the pi session JSONL / Claude Code JSONL formats.
license: MIT
compatibility: Requires Python 3.8+ and pi (reads ~/.pi/agent/settings.json for default provider/model). Windows/macOS/Linux.
---

# Migrate Claude Code Session → pi

This skill converts a Claude Code conversation into a pi session that can be resumed with `pi --resume`. It bundles a Python converter (`claude2pi.py`) that does everything: parses Claude's streaming JSONL, builds a compact summary + recent conversation, maps Claude tool calls to pi tools, and writes a valid pi session file to the correct location.

## Quick start

```bash
# Auto-detects provider/model/thinking from your pi settings.json
python claude2pi.py "<claude-session.jsonl>" "<target-cwd>" --cutoff "<ISO>"
```

- `<claude-session.jsonl>` — path under `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`.
- `<target-cwd>` — the working directory the pi session should bind to (usually the original project dir).
- `--cutoff` — ISO timestamp. Turns at/after it are kept as a full recent conversation; earlier turns are condensed into one structured **summary** user message (AGENT.md, user-prompt timeline, files-touched list, key progress, last status). Omit or pass `""` to keep **all** turns as recent (no summary).

Output is written to `~/.pi/agent/sessions/--<encoded-cwd>--/<ISO>_<uuid>.jsonl`.

### Example

```bash
python claude2pi.py \
  ~/.claude/projects/d--myproj/abc-123.jsonl \
  "D:\Github\MyProj" \
  --cutoff "2026-08-21T03:38:21"
```

## Options

| Option | Default | Purpose |
|---|---|---|
| `src` (positional, required) | — | Claude session JSONL path |
| `cwd` (positional, required) | — | target working directory |
| `--cutoff` | `""` (keep all) | ISO timestamp splitting summary vs recent |
| `--provider` | from pi settings | pi provider id for the session model |
| `--model` | from pi settings | pi model id |
| `--thinking` | from pi settings | thinking level |

## Open the migrated session

```bash
cd /path/to/target-cwd
pi --resume          # then pick the migrated session from the list
```

Historical tool calls are context only — pi does not re-execute them; file contents they reference may be stale.

## How it works (design notes)

- **Claude format**: each assistant JSONL line carries exactly ONE streaming delta block; lines sharing the same `message.id` form one turn. The converter concatenates `text` deltas to reconstruct full replies; each `tool_use` block is already complete. `thinking` blocks are dropped to save space. User lines hold either real typed prompts (string/text) or `tool_result` blocks paired by `tool_use_id`.
- **pi format**: `session` header → `model_change` → `thinking_level_change` → `message` entries. `parentId` forms a strict linear chain (every reference must exist). Assistant messages carry `toolCall` blocks; each must be followed by a matching `toolResult` message (1:1 by id, or provider replay breaks). `stopReason` is `toolUse` when the turn has tool calls, else `end_turn`.
- **Tool name mapping**: `Read→read`, `Edit→edit`, `Write→write`, `Bash/PowerShell/Grep/Glob→bash`. `mcp__*`, `Skill`, `Agent`, etc. are kept as-is (historical; not re-executed).
- **Size control**: thinking dropped; each tool result truncated (~500 chars); recent assistant text capped (~3000 chars). A 12 MB / 10k-line session typically becomes ~175 KB.
- **Noise filtering**: Claude injects `API Error`, `Please run /login`, `余额不足`, `所有供应商已熔断`, `function_call.arguments` as content — excluded from the summary's prompt timeline and "last status" so the summary is not misleading.

## Verification

After running, validate the output (the converter prints the path and counts to stderr):

- 0 bad-JSON lines
- 0 `parentId` references pointing to missing ids
- `toolCall` count == `toolResult` count, 0 orphans
- `stopReason` values are a subset of `{end_turn, toolUse}`

## Pitfalls

- **OOM-looking `MemoryError`** during development came from forgetting to advance the index in the user-message branch of the turn-grouping loop — it re-appended the same turn forever. If you edit the grouping logic, ensure every branch advances the iterator.
- Claude file order is chronological but `parentUuid` forms a tree; for migration to pi's *linear* format, chronological order with a fresh linear `parentId` chain is correct and sufficient.
- Streaming `text`/`thinking` blocks are **deltas** (e.g. 4-char fragments), not snapshots — concatenate them in order.
- `toolResult.toolName` must match the toolCall's name; the converter builds an id→name map from the assistant `tool_use` blocks rather than hardcoding `bash`.
- pi's `usage.cost` object has keys `input, output, cacheRead, cacheWrite, total` (no `reasoning`); top-level `usage` has `reasoning` and `totalTokens`.

## Files

- `claude2pi.py` — the converter. Run `python claude2pi.py --help` for usage.
