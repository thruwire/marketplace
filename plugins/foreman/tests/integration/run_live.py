#!/usr/bin/env python3
"""Exercise the Foreman hook contract in real Codex turns.

This uses a project-scoped mirror of the plugin hook registration so it can
separate hook-runtime compatibility from plugin-bundled hook discovery.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "integration" / "hooks.json"
FAKE_FOREMAN = ROOT / "tests" / "integration" / "fake_foreman.py"


def run_scenario(codex: str, root: Path, mode: str, prompt: str) -> list[dict]:
    log = root / f"{mode}.jsonl"
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{root / 'bin'}:{environment.get('PATH', '')}",
            "FOREMAN_PLUGIN_ROOT": str(ROOT),
            "FOREMAN_FAKE_LOG": str(log),
            "FOREMAN_FAKE_STATE": str(root / "state"),
            "FOREMAN_FAKE_MODE": mode,
        }
    )
    command = [
        codex,
        "exec",
        "--ephemeral",
        "--json",
        "--enable",
        "hooks",
        "--dangerously-bypass-hook-trust",
        "-C",
        str(root / "repo"),
        "-s",
        "workspace-write",
        prompt,
    ]
    result = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"Codex {mode} scenario exited {result.returncode}")
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def names(events: list[dict]) -> list[str]:
    return [event["hook_event_name"] for event in events]


def main() -> int:
    codex = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not codex:
        print("live integration: codex was not found on PATH", file=sys.stderr)
        return 127

    with tempfile.TemporaryDirectory(prefix="foreman-codex-live-") as temporary:
        root = Path(temporary)
        (root / "bin").mkdir()
        (root / "repo" / ".codex").mkdir(parents=True)
        (root / "state").mkdir()
        (root / "bin" / "foreman").symlink_to(FAKE_FOREMAN)
        shutil.copy2(FIXTURE, root / "repo" / ".codex" / "hooks.json")
        subprocess.run(["git", "init", "-q", str(root / "repo")], check=True)

        continued = run_scenario(
            codex,
            root,
            "continue",
            "Use the shell exactly once to run printf 'foreman-live-allowed\\n'. "
            "Do not modify files. Report the output and finish.",
        )
        continued_names = names(continued)
        required = [
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "Stop",
            "Stop",
            "SessionEnd",
        ]
        if continued_names != required:
            raise AssertionError(f"unexpected continuation flow: {continued_names}")
        stop_states = [
            event.get("stop_hook_active")
            for event in continued
            if event["hook_event_name"] == "Stop"
        ]
        if stop_states != [False, True]:
            raise AssertionError("Stop continuation flag did not transition false -> true")

        denied = run_scenario(
            codex,
            root,
            "deny",
            "Use the shell exactly once to run printf 'foreman-live-denied\\n'. "
            "If denied, do not retry. Do not modify files.",
        )
        denied_names = names(denied)
        if "PreToolUse" not in denied_names or "PostToolUse" in denied_names:
            raise AssertionError(f"tool denial did not stop execution: {denied_names}")
        if denied_names[-1] != "SessionEnd":
            raise AssertionError(f"SessionEnd missing from denied flow: {denied_names}")

    print("live Codex hook integration passed: allow, post-tool, continuation, deny, cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
