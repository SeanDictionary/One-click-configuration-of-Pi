#!/usr/bin/env python3
"""Convert a Claude Code session JSONL to a pi session JSONL.

Strategy: summary (programmatically extracted) + recent conversation (mapped tool calls,
thinking dropped, tool results truncated).
"""
import json, uuid, re, os, sys
from collections import defaultdict, OrderedDict
from datetime import datetime, timezone

NOISE_PATTERNS = [
    r"^API Error[:\s]",
    r"Please run /login",
    r"余额和订阅额度",
    r"所有供应商已熔断",
    r"function_call\.arguments",
    r"\[Request interrupted",
    r"Responses upstream",
    r"InternalError\.Algo",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS))

def is_noise(s):
    if not s:
        return True
    return bool(NOISE_RE.search(s))

# --- defaults: src/cwd required; provider/model/thinking auto-detected from pi settings ---
def _pi_setting(key, default=None):
    import json as _json, os as _os
    p = _os.path.expanduser("~/.pi/agent/settings.json")
    try:
        with open(p, encoding="utf-8") as fh:
            s = _json.load(fh)
        return s.get(key, default)
    except Exception:
        return default

_DEFAULT_PROVIDER = _pi_setting("defaultProvider") or ""
_DEFAULT_MODEL = _pi_setting("defaultModel") or ""
_DEFAULT_THINKING = _pi_setting("defaultThinkingLevel") or "medium"

import argparse
_ap = argparse.ArgumentParser(
    description="Migrate a Claude Code session JSONL to a pi session JSONL (summary + recent, mapped tools).",
    epilog="Example: python claude2pi.py ~/.claude/projects/d--myproj/abc.jsonl /d/Proj --cutoff 2026-08-01")
_ap.add_argument("src", help="Claude session .jsonl path (e.g. ~/.claude/projects/<enc-cwd>/<uuid>.jsonl)")
_ap.add_argument("cwd", help="target working directory for the pi session")
_ap.add_argument("--cutoff", default="",
                 help="ISO timestamp; turns at/after it are kept as full recent conversation, earlier turns become a summary. Empty (default) = keep all turns as recent.")
_ap.add_argument("--provider", default=_DEFAULT_PROVIDER, help="pi provider id (default: from pi settings)")
_ap.add_argument("--model", default=_DEFAULT_MODEL, help="pi model id (default: from pi settings)")
_ap.add_argument("--thinking", default=_DEFAULT_THINKING, help="thinking level (default: from pi settings)")
_args = _ap.parse_args()

SRC = _args.src
CWD = _args.cwd
CUTOFF = _args.cutoff
PROVIDER = _args.provider
MODEL_ID = _args.model
THINKING_LEVEL = _args.thinking

# truncation
TR_TOOLRESULT = 500      # cap each tool result text
TR_AITEXT_RECENT = 3000  # cap assistant text in recent block
TR_AITEXT_SUMM = 220     # cap assistant text in summary "key progress"

# ---- read source ----
raw = []
with open(SRC, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        raw.append(o)

# keep only user/assistant, in file order (chronological)
msgs = [o for o in raw if o.get("type") in ("user", "assistant")]

# ---- group into turns ----
# assistant lines with same message.id belong to one turn (streaming deltas).
# user lines are individual (one per line; content may be string / [text] / [tool_result]).
turns = []
i = 0
n = len(msgs)
while i < n:
    o = msgs[i]
    if o["type"] == "assistant":
        mid = o.get("message", {}).get("id") or o.get("uuid")
        ts0 = o.get("timestamp")
        ts1 = o.get("timestamp")
        lines_grp = []
        while i < n and msgs[i]["type"] == "assistant" and (msgs[i].get("message", {}).get("id") == mid or (not msgs[i].get("message", {}).get("id"))):
            lines_grp.append(msgs[i])
            ts1 = msgs[i].get("timestamp", ts1)
            i += 1
        # merge content blocks
        text_parts = []
        thinking_parts = []  # dropped, but collect to know
        tool_uses = []  # list of (block)
        for L in lines_grp:
            c = L.get("message", {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    t = b.get("type")
                    if t == "text":
                        text_parts.append(b.get("text", ""))
                    elif t == "thinking":
                        thinking_parts.append(b.get("thinking", ""))
                    elif t == "tool_use":
                        # dedup by id (a tool_use may appear once when complete)
                        tu = {"id": b.get("id"), "name": b.get("name"), "input": b.get("input", {})}
                        tool_uses.append(tu)
            elif isinstance(c, str):
                text_parts.append(c)
        turns.append({
            "kind": "assistant",
            "ts": ts0,
            "ts_end": ts1,
            "text": "".join(text_parts),
            "tool_uses": tool_uses,
            "model": (lines_grp[0].get("message", {}).get("model") if lines_grp else None),
        })
    else:
        # user
        c = o.get("message", {}).get("content")
        text = ""
        tool_results = []  # list of {id, content(str), is_error}
        is_real_user = False
        if isinstance(c, str):
            text = c
            is_real_user = True
        elif isinstance(c, list):
            for b in c:
                if not isinstance(b, dict):
                    continue
                t = b.get("type")
                if t == "text":
                    text += b.get("text", "")
                    is_real_user = True
                elif t == "tool_result":
                    rc = b.get("content")
                    if isinstance(rc, list):
                        rtxt = "".join(x.get("text", "") for x in rc if isinstance(x, dict) and x.get("type") == "text")
                    elif isinstance(rc, str):
                        rtxt = rc
                    else:
                        rtxt = json.dumps(rc, ensure_ascii=False) if rc is not None else ""
                    tool_results.append({
                        "id": b.get("tool_use_id"),
                        "content": rtxt,
                        "is_error": bool(b.get("is_error", False)),
                    })
        turns.append({
            "kind": "user",
            "ts": o.get("timestamp"),
            "text": text,
            "tool_results": tool_results,
            "is_real_user": is_real_user,
        })
        i += 1

print(f"total turns: {len(turns)}", file=sys.stderr)

# ---- split summary vs recent ----
if not CUTOFF:
    # keep everything as recent conversation; no summary
    recent_idx = 0
else:
    recent_idx = None
    for idx, t in enumerate(turns):
        if t["ts"] and t["ts"] >= CUTOFF:
            recent_idx = idx
            break
    if recent_idx is None:
        recent_idx = len(turns)
summary_turns = turns[:recent_idx]
recent_turns = turns[recent_idx:]
print(f"summary turns: {len(summary_turns)}  recent turns: {len(recent_turns)}", file=sys.stderr)

# ---- build summary text ----
# 1. AGENT.md (first real user message)
agent_md = ""
for t in summary_turns:
    if t["kind"] == "user" and t["is_real_user"]:
        agent_md = t["text"]
        break

# 2. timeline of real user prompts (all turns, full session)
user_prompts = []
for t in turns:
    if t["kind"] == "user" and t["is_real_user"]:
        s = t["text"].strip()
        if not s or is_noise(s):
            continue
        # skip skill-launch boilerplate
        if s.startswith("Base directory for this skill"):
            s = "[skill: " + s.split("\n")[0].replace("Base directory for this skill: ", "") + "]"
        ts = (t["ts"] or "")[:19]
        user_prompts.append((ts, s[:160]))

# 3. files touched (from tool_uses across whole session)
files = defaultdict(set)
TOOL_FILE = {"Read": "file_path", "Edit": "file_path", "Write": "file_path"}
for t in turns:
    if t["kind"] != "assistant":
        continue
    for tu in t["tool_uses"]:
        nm = tu["name"]
        key = TOOL_FILE.get(nm)
        if key and isinstance(tu["input"], dict):
            p = tu["input"].get(key)
            if p:
                files[nm].add(p)

# group files by directory
def group_files(paths):
    bydir = defaultdict(list)
    for p in sorted(paths):
        d = os.path.dirname(p).replace("\\", "/")
        bydir[d].append(os.path.basename(p))
    return bydir

all_files = set().union(*files.values()) if files else set()

# 4. key progress: substantive assistant text replies in summary region, capped
key_progress = []
for t in summary_turns:
    if t["kind"] != "assistant":
        continue
    txt = t["text"].strip()
    if len(txt) < 40 or is_noise(txt):
        continue
    ts = (t["ts"] or "")[:19]
    key_progress.append((ts, txt[:TR_AITEXT_SUMM]))

# 5. last substantive assistant text (current status) — prefer a non-noise reply
# near the end of the summary region (the real progress report)
last_status = ""
for t in reversed(summary_turns):
    if t["kind"] == "assistant":
        txt = t["text"].strip()
        if len(txt) >= 40 and not is_noise(txt):
            last_status = txt
            break
if not last_status:
    for t in reversed(turns):
        if t["kind"] == "assistant" and len(t["text"].strip()) >= 40 and not is_noise(t["text"]):
            last_status = t["text"].strip()
            break

# ---- assemble summary message ----
parts = []
parts.append("# 会话迁移说明（来自 Claude Code）\n")
parts.append(f"本会话原始来源：Claude Code 会话 `ed193800-284a-4c78-8cdd-d0712fc502d0`，"
             f"使用模型 gpt-5.5-2026-04-23，工作目录 `{CWD}`。"
             f"以下为历史摘要 + 近期完整对话，由脚本自动迁移。"
             f"早期历史中的 thinking 块已省略，工具结果已截断。\n")

parts.append("\n## AGENT.md（项目操作约定）\n")
parts.append(agent_md.strip() + "\n")

parts.append("\n## 用户需求时间线\n")
for ts, s in user_prompts:
    parts.append(f"- `{ts}` {s}\n")

parts.append(f"\n## 涉及文件（共 {len(all_files)} 个，按工具）\n")
for nm in ("Read", "Edit", "Write"):
    if nm in files:
        bydir = group_files(files[nm])
        parts.append(f"\n### {nm}（{len(files[nm])}）\n")
        for d in sorted(bydir):
            parts.append(f"- `{d}/`: {', '.join(bydir[d])}\n")

parts.append("\n## 关键进展摘要（按时间）\n")
for ts, s in key_progress:
    parts.append(f"- `{ts}` {s}\n")

parts.append("\n## 最近状态（最近一条实质性助手回复）\n")
parts.append((last_status or "(无)") + "\n")

parts.append("\n---\n以下为近期完整对话（工具调用已映射为 pi 工具，结果已截断）。\n")

summary_text = "".join(parts)
print(f"summary text chars: {len(summary_text)}", file=sys.stderr)

# ---- tool name mapping ----
TOOL_MAP = {
    "Read": "read",
    "Edit": "edit",
    "Write": "write",
    "Bash": "bash",
    "PowerShell": "bash",
    "Grep": "bash",
    "Glob": "bash",
}

def map_tool_name(nm):
    return TOOL_MAP.get(nm, nm)  # keep mcp__/Skill/etc as-is

def trunc(s, n):
    if len(s) <= n:
        return s
    return s[:n] + f"\n…[已截断,原 {len(s)} 字符]"

# ---- build pi entries ----
def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond//1000:03d}Z"

def gen_id():
    return uuid.uuid4().hex[:8]

def gen_uuid():
    return str(uuid.uuid4())

session_id = gen_uuid()
start_iso = now_iso()
entries = []

# header
entries.append({"type": "session", "version": 3, "id": session_id, "timestamp": start_iso, "cwd": CWD})
mc_id = gen_id()
entries.append({"type": "model_change", "id": mc_id, "parentId": None, "timestamp": start_iso, "provider": PROVIDER, "modelId": MODEL_ID})
tl_id = gen_id()
entries.append({"type": "thinking_level_change", "id": tl_id, "parentId": mc_id, "timestamp": start_iso, "thinkingLevel": THINKING_LEVEL})

prev = tl_id
seq_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

def emit_user_text(text, ts_iso, ts_ms):
    global prev
    eid = gen_id()
    e = {"type": "message", "id": eid, "parentId": prev, "timestamp": ts_iso,
         "message": {"role": "user", "content": [{"type": "text", "text": text}], "timestamp": ts_ms}}
    entries.append(e)
    prev = eid

def emit_assistant(text, tool_calls, ts_iso, ts_ms, model):
    global prev
    eid = gen_id()
    blocks = []
    if text:
        blocks.append({"type": "text", "text": text})
    for tc in tool_calls:
        blocks.append({"type": "toolCall", "id": tc["id"], "name": tc["name"], "arguments": tc["arguments"]})
    if not blocks:
        blocks = [{"type": "text", "text": ""}]
    has_tools = bool(tool_calls)
    msg = {"role": "assistant", "content": blocks, "api": "openai-completions",
           "provider": "claude", "model": model or "gpt-5.5-2026-04-23",
           "usage": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
                     "reasoning": 0, "totalTokens": 0,
                     "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0}},
           "stopReason": "toolUse" if has_tools else "end_turn",
           "rawStopReason": "tool_calls" if has_tools else "stop",
           "responseId": "chatcmpl-migrated-" + eid,
           "timestamp": ts_ms}
    e = {"type": "message", "id": eid, "parentId": prev, "timestamp": ts_iso, "message": msg}
    entries.append(e)
    prev = eid
    return eid

def emit_tool_result(tool_call_id, tool_name, text, is_error, ts_iso, ts_ms):
    global prev
    eid = gen_id()
    msg = {"role": "toolResult", "toolCallId": tool_call_id, "toolName": tool_name,
           "content": [{"type": "text", "text": text}], "isError": is_error, "timestamp": ts_ms}
    e = {"type": "message", "id": eid, "parentId": prev, "timestamp": ts_iso, "message": msg}
    entries.append(e)
    prev = eid

def to_iso(ts):
    if not ts:
        return start_iso
    return ts

def to_ms(ts):
    nonlocal_var = ts
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except Exception:
        return seq_ms

# emit summary as a single user message
# emit summary as a single user message (skip if no summary region)
if summary_turns:
    emit_user_text(summary_text, start_iso, seq_ms)

# emit recent turns
# build id->mapped tool name map across recent (for toolResult toolName)
recent_id2name = {}
for t in recent_turns:
    if t["kind"] == "assistant":
        for tu in t["tool_uses"]:
            recent_id2name[tu["id"]] = map_tool_name(tu["name"])

for t in recent_turns:
    ts_iso = to_iso(t.get("ts") or t.get("ts_end") or start_iso)
    ts_ms = to_ms(t.get("ts") or t.get("ts_end") or start_iso)
    if t["kind"] == "user":
        if t["is_real_user"] and t["text"].strip():
            emit_user_text(t["text"].strip(), ts_iso, ts_ms)
        # tool results: emit as toolResult messages paired to preceding tool calls
        for tr in t["tool_results"]:
            tid = tr["id"] or gen_id()
            tname = recent_id2name.get(tid, "bash")
            emit_tool_result(tid, tname, trunc(tr["content"], TR_TOOLRESULT), tr["is_error"], ts_iso, ts_ms)
    else:  # assistant
        text = trunc(t["text"].strip(), TR_AITEXT_RECENT) if t["text"] else ""
        tcs = []
        for tu in t["tool_uses"]:
            nm = map_tool_name(tu["name"])
            args = tu["input"] if isinstance(tu["input"], dict) else {"_raw": tu["input"]}
            tcs.append({"id": tu["id"] or gen_id(), "name": nm, "arguments": args})
        emit_assistant(text, tcs, ts_iso, ts_ms, t.get("model"))

# write
out_dir = os.path.expanduser("~/.pi/agent/sessions/--D--Github-SeanBlog-Frame--")
os.makedirs(out_dir, exist_ok=True)
fname_ts = start_iso.replace(":", "-").replace(".", "-")
out_path = os.path.join(out_dir, f"{fname_ts}_{session_id}.jsonl")
# filename timestamp format matches pi: 2026-08-21T09-02-20-015Z_uuid
# reconstruct proper format
fname_ts2 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-") + f"{datetime.now(timezone.utc).microsecond//1000:03d}Z"
out_path = os.path.join(out_dir, f"{fname_ts2}_{session_id}.jsonl")

with open(out_path, "w", encoding="utf-8") as fh:
    for e in entries:
        fh.write(json.dumps(e, ensure_ascii=False) + "\n")

total = os.path.getsize(out_path)
print(f"\nOUTPUT: {out_path}", file=sys.stderr)
print(f"entries: {len(entries)}  size: {total} bytes ({total/1024:.1f} KB)", file=sys.stderr)
# breakdown
kinds = defaultdict(int)
for e in entries:
    if e["type"] == "message":
        kinds[e["message"]["role"]] += 1
    else:
        kinds[e["type"]] += 1
print("breakdown:", dict(kinds), file=sys.stderr)
