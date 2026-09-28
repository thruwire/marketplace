#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAUNCHER = ROOT / "scripts" / "foreman-hook"
RESPONSIBILITY_ID = "selective-pytest.python-tests"


def invoke(event: dict[str, object], environment: dict[str, str]) -> dict[str, object]:
    result = subprocess.run(
        [str(LAUNCHER)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=environment,
        cwd=ROOT,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"{event['hook_event_name']} failed with exit {result.returncode}: "
            f"{result.stderr.strip()}"
        )
    return json.loads(result.stdout)


def session_state(data_dir: Path) -> dict[str, object]:
    paths = list((data_dir / "sessions").glob("*.json"))
    if len(paths) != 1:
        raise RuntimeError(f"expected one attached session, found {len(paths)}")
    record = json.loads(paths[0].read_text(encoding="utf-8"))
    state = record.get("state")
    if not isinstance(state, dict):
        raise RuntimeError("attached session has no Foreman state")
    return state


def run_case(
    *,
    name: str,
    prompt: str,
    expect_responsibility: bool,
    target: Path,
    data_dir: Path,
    environment: dict[str, str],
) -> None:
    session_id = f"selective-pytest-{name}-{uuid.uuid4().hex}"
    base: dict[str, object] = {
        "session_id": session_id,
        "transcript_path": None,
        "cwd": str(target),
        "model": "selective-pytest-demo",
        "permission_mode": "default",
    }
    invoke({**base, "hook_event_name": "SessionStart", "source": "startup"}, environment)
    try:
        invoke(
            {
                **base,
                "hook_event_name": "UserPromptSubmit",
                "turn_id": f"{name}-turn",
                "prompt": prompt,
            },
            environment,
        )
        routed = session_state(data_dir)
        active = routed.get("active_responsibility_ids", [])
        activated = RESPONSIBILITY_ID in active
        if activated != expect_responsibility:
            raise RuntimeError(
                f"{name}: expected responsibility active={expect_responsibility}, got "
                f"{activated}; routing scores={routed.get('routing_scores', {})}"
            )

        invoke(
            {
                **base,
                "hook_event_name": "Stop",
                "turn_id": f"{name}-turn",
                "stop_hook_active": False,
                "last_assistant_message": "The requested work and verification are complete.",
            },
            environment,
        )
        stopped = session_state(data_dir)
        evidence = [
            item
            for item in stopped.get("command_evidence", [])
            if item.get("provider_id") == "command.pytest"
        ]
        if expect_responsibility:
            if len(evidence) != 1:
                raise RuntimeError(f"{name}: expected one pytest result, got {len(evidence)}")
            result = evidence[0]
            if result.get("status") != "completed" or result.get("exit_code") != 0:
                raise RuntimeError(f"{name}: pytest did not pass: {result}")
            print(
                f"{name}: routed=yes, command.pytest runs=1, "
                f"status={result['status']}, exit={result['exit_code']}"
            )
        else:
            if evidence:
                raise RuntimeError(f"{name}: pytest ran despite responsibility not being active")
            print(f"{name}: routed=no, command.pytest runs=0")
    finally:
        invoke(
            {**base, "hook_event_name": "SessionEnd", "reason": "demo-complete"},
            environment,
        )


def main() -> int:
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise SystemExit("TYPESAFE_API_KEY must already be present in the environment")
    if shutil.which("foreman") is None:
        raise SystemExit("foreman is not on PATH")
    if shutil.which("pytest") is None:
        raise SystemExit("pytest is not on PATH")

    with tempfile.TemporaryDirectory(prefix="foreman-selective-pytest-") as temporary:
        temporary_path = Path(temporary)
        data_dir = temporary_path / "foreman-data"
        target = temporary_path / "sample-project"
        data_dir.mkdir()
        shutil.copy2(HERE / "foreman-config.toml", data_dir / "config.toml")
        shutil.copytree(HERE / "sample_project", target)

        environment = os.environ.copy()
        environment["FOREMAN_DATA_DIR"] = str(data_dir)
        run_case(
            name="docs-only",
            prompt=(
                "Edit only the README heading. Do not change or validate Python code, Python "
                "tests, dependencies, or packaging."
            ),
            expect_responsibility=False,
            target=target,
            data_dir=data_dir,
            environment=environment,
        )
        run_case(
            name="python-change",
            prompt=(
                "Change the Python calculator behavior and validate it with the Python test "
                "suite. Passing pytest evidence is required before completion."
            ),
            expect_responsibility=True,
            target=target,
            data_dir=data_dir,
            environment=environment,
        )

        remaining = list((data_dir / "sessions").glob("*.json"))
        if remaining:
            raise RuntimeError(f"SessionEnd left {len(remaining)} session files")
    print("selective pytest demo passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
