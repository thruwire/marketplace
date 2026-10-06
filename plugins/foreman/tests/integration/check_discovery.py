#!/usr/bin/env python3
"""Check actual plugin hook discovery without invoking models or installing hook copies."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = ROOT.parents[1] / ".agents" / "plugins" / "marketplace.json"
EVENTS = {"sessionStart", "userPromptSubmit", "preToolUse", "postToolUse", "stop", "sessionEnd"}


def main() -> None:
    binary = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not binary:
        raise SystemExit("Codex is required for the discovery check")
    process = subprocess.Popen(
        [binary, "app-server", "--stdio"], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )

    def rpc(identifier, method, params):
        process.stdin.write(json.dumps({"id": identifier, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        for line in process.stdout:
            response = json.loads(line)
            if response.get("id") == identifier:
                if "error" in response:
                    raise RuntimeError(json.dumps(response["error"]))
                return response["result"]
        raise RuntimeError("App server ended before responding")

    try:
        rpc(1, "initialize", {
            "clientInfo": {"name": "foreman_discovery_check", "version": "1.0"},
            "capabilities": {"experimentalApi": True},
        })
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        plugin = rpc(2, "plugin/read", {
            "marketplacePath": str(MARKETPLACE), "pluginName": "foreman",
        })["plugin"]
        hooks = plugin["hooks"]
        observed = {hook["eventName"] for hook in hooks}
        if len(hooks) != 6 or observed != EVENTS:
            raise AssertionError(f"Expected six Foreman hooks, got {hooks!r}")
        if not all(hook["key"].startswith("foreman@thruwire:hooks/hooks.json:") for hook in hooks):
            raise AssertionError("Hooks did not come from the existing plugin configuration")
        if plugin["summary"]["id"] != "foreman@thruwire":
            raise AssertionError("Plugin identity changed")
        print("Codex discovered all six existing foreman@thruwire plugin hooks")
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
