#!/usr/bin/env python3
"""Record Lungji widget state atomically.

Usage: python set_state.py <idle|working|review|done>

Also reads a Claude Code hook payload from stdin (if present) and, for
notification-style hooks, stores its message text into the `cmd` field so the
widget can show what is happening. Never crashes the caller: any failure is
swallowed so hooks stay transparent.
"""
import json
import os
import sys
import tempfile

VALID = {"idle", "working", "review", "done"}


def state_dir():
    d = os.path.expanduser("~/.adele_term")
    os.makedirs(d, exist_ok=True)
    return d


def read_hook_payload():
    """Best-effort parse of a hook JSON payload piped on stdin."""
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def pick_cmd(payload):
    """Extract a short human-readable command/message from a hook payload."""
    if not isinstance(payload, dict):
        return ""
    for key in ("message", "prompt", "tool_name"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().splitlines()[0][:120]
    tool = payload.get("tool_input")
    if isinstance(tool, dict):
        for key in ("command", "description", "file_path"):
            val = tool.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().splitlines()[0][:120]
    return ""


def atomic_write(path, data):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def main():
    state = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "idle"
    if state not in VALID:
        state = "idle"
    payload = read_hook_payload()
    cmd = pick_cmd(payload)
    try:
        atomic_write(os.path.join(state_dir(), "state.json"),
                     {"state": state, "cmd": cmd})
    except Exception:
        pass  # never break the hook chain
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
