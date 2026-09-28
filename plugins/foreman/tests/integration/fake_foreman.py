#!/usr/bin/env python3
"""Deterministic Foreman protocol double for live Codex integration checks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    if sys.argv[1:] != ["hook", "--client", "codex"]:
        print("fake foreman: unexpected arguments", file=sys.stderr)
        return 64

    event = json.load(sys.stdin)
    log_path = Path(os.environ["FOREMAN_FAKE_LOG"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")))
        handle.write("\n")

    name = event["hook_event_name"]
    mode = os.environ.get("FOREMAN_FAKE_MODE", "normal")
    response: dict[str, object] = {}

    if name == "SessionStart":
        response = {
            "hookSpecificOutput": {
                "hookEventName": name,
                "additionalContext": "Foreman integration test supervisor attached.",
            }
        }
    elif name == "UserPromptSubmit":
        response = {
            "hookSpecificOutput": {
                "hookEventName": name,
                "additionalContext": "Foreman integration test responsibility is active.",
            }
        }
    elif name == "PreToolUse" and mode == "deny":
        response = {
            "hookSpecificOutput": {
                "hookEventName": name,
                "permissionDecision": "deny",
                "permissionDecisionReason": "Denied by the Foreman integration test.",
            }
        }
    elif name == "PostToolUse":
        response = {
            "hookSpecificOutput": {
                "hookEventName": name,
                "additionalContext": "Foreman observed the completed integration-test tool call.",
            }
        }
    elif name == "Stop" and mode == "continue":
        state_dir = Path(os.environ["FOREMAN_FAKE_STATE"])
        state_dir.mkdir(parents=True, exist_ok=True)
        marker = state_dir / f"{event['session_id']}.continued"
        if not marker.exists() and not event.get("stop_hook_active", False):
            marker.write_text("continued\n", encoding="utf-8")
            response = {
                "decision": "block",
                "reason": "Foreman integration test requests one continuation before completion.",
            }

    sys.stdout.write(json.dumps(response, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
