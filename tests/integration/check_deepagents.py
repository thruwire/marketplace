"""Exercise marketplace installation and plugin hooks in installed dcode, without API calls.

Run with a Python environment containing deepagents-code >= 0.1.83:
    python tests/integration/check_deepagents.py
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ID = "foreman-deepagents@thruwire"


def main() -> None:
    original_env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="foreman dcode integration ") as temporary:
        root = Path(temporary)
        marketplace = root / "marketplace with spaces"
        shutil.copytree(ROOT, marketplace, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        profile = root / "profile"
        os.environ["DEEPAGENTS_HOME"] = str(profile)
        cli = Path(sys.executable).parent / "dcode"

        def command(*args: str) -> str:
            result = subprocess.run([cli, "plugin", *args], capture_output=True, text=True)
            assert result.returncode == 0, (args, result.stdout, result.stderr)
            return result.stdout

        command("marketplace", "add", str(marketplace))
        # Re-registering is the refresh route supported by 0.1.83.
        command("marketplace", "add", str(marketplace))
        command("install", PLUGIN_ID)

        from deepagents_code.plugins import discover_plugins, list_available_plugins
        from deepagents_code.plugins.adapters.hooks import plugin_hook_event_names

        found = discover_plugins()
        assert not found.warnings, found.warnings
        assert [p.plugin_id for p in found.plugins] == [PLUGIN_ID]
        plugin = found.plugins[0]
        assert plugin.version == "0.1.0"
        assert plugin.inventory.skills, "Plugin skill was not discovered"
        events = set(plugin_hook_event_names(plugin))
        assert events == {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse",
                          "PostToolUseFailure", "Stop", "SessionEnd"}, events
        assert not (profile / "hooks.json").exists(), "Installation wrote user hooks"
        assert len(list_available_plugins()) == 1, "dcode discovered a Codex package"

        # Run installed hooks through dcode's native loader and subprocess runner.
        # The fake supervisor records the real native payload and supplies control responses.
        bin_dir = root / "bin with spaces"
        bin_dir.mkdir()
        capture = root / "calls.jsonl"
        fake = bin_dir / "foreman"
        fake.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "payload = json.load(sys.stdin)\n"
            "assert sys.argv[1:] == ['hook', '--client', 'deepagents'], sys.argv\n"
            "with open(os.environ['FOREMAN_TEST_CAPTURE'], 'a') as stream:\n"
            "    stream.write(json.dumps(payload) + '\\n')\n"
            "event = payload['hook_event_name']\n"
            "if event == 'PreToolUse':\n"
            "    print(json.dumps({'hookSpecificOutput': {'hookEventName': event, "
            "'permissionDecision': 'deny', 'permissionDecisionReason': 'test denial'}}))\n"
            "elif event == 'Stop':\n"
            "    print(json.dumps({'decision': 'block', 'reason': 'test continuation'}))\n"
            "else:\n"
            "    print('{}')\n"
        )
        fake.chmod(0o755)
        os.environ["PATH"] = f"{bin_dir}:{os.environ.get('PATH', '')}"
        os.environ["FOREMAN_TEST_CAPTURE"] = str(capture)
        asyncio.run(exercise_hooks(root, capture))

        command("disable", PLUGIN_ID)
        assert not discover_plugins().plugins, "Disabled plugin still loaded"
        command("enable", PLUGIN_ID)
        assert len(discover_plugins().plugins) == 1
        command("uninstall", PLUGIN_ID)
        assert not discover_plugins().plugins, "Uninstalled plugin still loaded"
        print("PASS: dcode marketplace add/re-add, install, skill and seven-hook discovery, "
              "native payload forwarding, tool denial, Stop continuation, disable/enable/uninstall; "
              "paths with spaces; no API calls or user-profile changes.")
    os.environ.clear()
    os.environ.update(original_env)


async def exercise_hooks(root: Path, capture: Path) -> None:
    from deepagents_code.approval_mode import ApprovalMode
    from deepagents_code.hooks.manager import HookSessionIdentity, HooksManager
    from deepagents_code.hooks.models.domain import (
        HookContext, HookEvent, HookInvocation, PostToolUseEvent, PostToolUseFailureEvent,
        PreToolUseEvent, SessionEndCause, SessionStartCause, StopEvent, ToolCallData,
    )
    from deepagents_code.hooks.trust import WorkspaceTrust

    prompt_id = uuid4()
    identity = HookSessionIdentity("plugin-smoke", ApprovalMode.MANUAL, prompt_id)
    notices = []
    manager = HooksManager.create(cwd=root, identity=lambda: identity,
                                  notice=lambda *args: notices.append(args),
                                  trust=WorkspaceTrust.none())
    assert manager.enabled, "Plugin hooks did not load"
    context = HookContext(thread_id=identity.thread_id, cwd=root, prompt_id=prompt_id,
                          approval_mode=ApprovalMode.MANUAL)

    async def invoke(event):
        return await manager._runtime.invoke(HookInvocation(context=context, event=event))

    await manager.on_session_start(SessionStartCause.STARTUP)
    prompt = await manager.on_user_prompt("Verify plugin hooks")
    assert prompt.ok
    call = ToolCallData(id="call-1", name="execute", args={"command": "cat example.txt"})
    denied = await invoke(PreToolUseEvent(event=HookEvent.PRE_TOOL_USE, call=call))
    assert denied.permission.behavior == "deny", denied
    await invoke(PostToolUseEvent(event=HookEvent.POST_TOOL_USE, call=call, result="example"))
    await invoke(PostToolUseFailureEvent(event=HookEvent.POST_TOOL_USE_FAILURE, call=call,
                                        error="sample failure"))
    stop = await invoke(StopEvent(event=HookEvent.STOP, continuation_count=0,
                                 last_assistant_message="unfinished"))
    assert stop.continue_loop, stop
    await manager.on_session_end(SessionEndCause.OTHER)
    recorded = [json.loads(line) for line in capture.read_text().splitlines()]
    assert [p["hook_event_name"] for p in recorded] == [
        "SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse",
        "PostToolUseFailure", "Stop", "SessionEnd",
    ], recorded
    assert all(p["session_id"] == identity.thread_id for p in recorded)
    assert recorded[2]["tool_name"] == "Bash", recorded[2]
    assert recorded[4]["error"] == "sample failure", recorded[4]
    assert not notices, notices


if __name__ == "__main__":
    main()
