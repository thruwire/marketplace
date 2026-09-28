from __future__ import annotations

import json
import os
import re
import stat
import struct
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "scripts" / "foreman-hook"
DOCTOR = ROOT / "scripts" / "doctor"
HOOKS = ROOT / "hooks" / "hooks.json"
MANIFEST = ROOT / "plugin.json"
COMPATIBILITY_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
COMPOSER_ICON = ROOT / "assets" / "icon.png"
LOGO = ROOT / "assets" / "logo.svg"
SELECTIVE_PYTEST = ROOT / "examples" / "selective-pytest"
EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "SessionEnd",
}


def executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class FakeForeman:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.bin_dir = directory / "bin with spaces"
        self.bin_dir.mkdir(parents=True)
        self.stdin = directory / "captured stdin"
        self.args = directory / "captured args"
        self.stdout = directory / "fake stdout"
        self.stderr = directory / "fake stderr"
        self.stdout.write_bytes(b'{"ok":true}\n')
        self.stderr.write_bytes(b"")
        executable(
            self.bin_dir / "foreman",
            """#!/bin/sh
if [ "${1:-}" = "--version" ]; then
    printf '%s\\n' "foreman-core ${FAKE_FOREMAN_VERSION:-0.4.1}"
    exit 0
fi
if [ "${1:-}" = "extension" ] && [ "${2:-}" = "status" ]; then
    if [ "${FAKE_CONFIG_VALID:-1}" = "1" ]; then
        exit 0
    fi
    printf '%s\\n' 'mock configuration error' >&2
    exit 2
fi
printf '%s\\n' "$@" > "$FAKE_ARGS"
cat > "$FAKE_STDIN"
cat "$FAKE_STDOUT"
cat "$FAKE_STDERR" >&2
exit "${FAKE_EXIT_CODE:-0}"
""",
        )

    def environment(self, **updates: str) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{self.bin_dir}:{environment.get('PATH', '')}",
                "FAKE_STDIN": str(self.stdin),
                "FAKE_ARGS": str(self.args),
                "FAKE_STDOUT": str(self.stdout),
                "FAKE_STDERR": str(self.stderr),
            }
        )
        environment.update(updates)
        return environment


class LauncherTests(unittest.TestCase):
    def test_forwards_streams_arguments_and_exit_status(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foreman plugin test ") as temporary:
            temporary_path = Path(temporary)
            fake = FakeForeman(temporary_path)
            protocol_input = b'{"path":"directory with spaces/odd-[name]","n":1}\n'
            protocol_output = b'{"decision":"block","reason":"review output"}\n'
            diagnostic = b"jev diagnostic on stderr\n"
            fake.stdout.write_bytes(protocol_output)
            fake.stderr.write_bytes(diagnostic)
            caller = temporary_path / "caller cwd with spaces"
            caller.mkdir()

            result = subprocess.run(
                [LAUNCHER],
                input=protocol_input,
                capture_output=True,
                cwd=caller,
                env=fake.environment(FAKE_EXIT_CODE="23"),
                check=False,
            )

            self.assertEqual(result.returncode, 23)
            self.assertEqual(fake.stdin.read_bytes(), protocol_input)
            self.assertEqual(result.stdout, protocol_output)
            self.assertEqual(result.stderr, diagnostic)
            self.assertEqual(fake.args.read_text(encoding="utf-8"), "hook\n--client\ncodex\n")

    def test_missing_foreman_is_actionable_and_protocol_safe(self) -> None:
        result = subprocess.run(
            [LAUNCHER],
            input=b"{}",
            capture_output=True,
            env={"PATH": ""},
            check=False,
        )
        self.assertEqual(result.returncode, 127)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"foreman was not found on PATH", result.stderr)
        self.assertIn(b"pipx install foreman-core", result.stderr)


class DoctorTests(unittest.TestCase):
    def test_missing_foreman(self) -> None:
        result = subprocess.run(
            [DOCTOR],
            capture_output=True,
            env={"PATH": "/usr/bin:/bin"},
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"foreman is not on PATH", result.stderr)

    def test_missing_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake = FakeForeman(Path(temporary))
            environment = fake.environment()
            environment.pop("TYPESAFE_API_KEY", None)
            result = subprocess.run(
                [DOCTOR],
                capture_output=True,
                env=environment,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"TYPESAFE_API_KEY is not set", result.stderr)

    def test_valid_mocked_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake = FakeForeman(Path(temporary))
            result = subprocess.run(
                [DOCTOR],
                capture_output=True,
                env=fake.environment(TYPESAFE_API_KEY="not-printed-secret"),
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertIn(b"Foreman is ready for Codex", result.stdout)
        self.assertNotIn(b"not-printed-secret", result.stdout + result.stderr)


class MetadataTests(unittest.TestCase):
    def test_hook_manifest_registers_all_supported_events_synchronously(self) -> None:
        payload = json.loads(HOOKS.read_text(encoding="utf-8"))
        self.assertEqual(set(payload["hooks"]), EVENTS)
        for event, groups in payload["hooks"].items():
            self.assertEqual(len(groups), 1, event)
            handlers = groups[0]["hooks"]
            self.assertEqual(len(handlers), 1, event)
            handler = handlers[0]
            self.assertEqual(handler["type"], "command")
            self.assertNotIn("async", handler)
            self.assertEqual(handler["command"], '"${PLUGIN_ROOT}/scripts/foreman-hook"')

    def test_portable_manifest_has_current_structure(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(payload["name"], "foreman")
        self.assertRegex(payload["version"], r"^\d+\.\d+\.\d+")
        self.assertEqual(payload["author"]["name"], "ThruWire")
        openai = payload["extensions"]["com.openai"]
        self.assertEqual(openai["hooks"], "./hooks/hooks.json")
        self.assertTrue((ROOT / openai["hooks"]).is_file())
        interface = openai["interface"]
        for key in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "capabilities",
            "defaultPrompt",
            "brandColor",
            "composerIcon",
            "logo",
        ):
            self.assertTrue(interface[key], key)
        self.assertEqual(interface["brandColor"], "#FF6500")
        self.assertEqual(interface["composerIcon"], "./assets/icon.png")
        self.assertEqual(interface["logo"], "./assets/logo.svg")
        self.assertTrue((ROOT / interface["composerIcon"]).is_file())
        self.assertTrue((ROOT / interface["logo"]).is_file())
        allowed = {
            "$schema",
            "name",
            "version",
            "description",
            "author",
            "homepage",
            "repository",
            "license",
            "keywords",
            "extensions",
        }
        self.assertFalse(set(payload) - allowed)
        self.assertLessEqual(len(payload["name"]), 64)
        self.assertIsNotNone(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", payload["name"]))

    def test_compatibility_manifest_matches_portable_identity(self) -> None:
        portable = json.loads(MANIFEST.read_text(encoding="utf-8"))
        compatibility = json.loads(COMPATIBILITY_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(compatibility["name"], portable["name"])
        self.assertEqual(compatibility["version"], portable["version"])
        self.assertEqual(compatibility["description"], portable["description"])
        self.assertEqual(compatibility["author"]["name"], "ThruWire")
        self.assertEqual(compatibility["skills"], "./skills/")
        self.assertEqual(
            compatibility["interface"],
            portable["extensions"]["com.openai"]["interface"],
        )
        self.assertNotIn("hooks", compatibility)

    def test_branding_assets_are_valid_square_images(self) -> None:
        png = COMPOSER_ICON.read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        self.assertEqual((width, height), (1254, 1254))

        svg = ET.parse(LOGO).getroot()
        self.assertEqual(svg.tag.rsplit("}", 1)[-1], "svg")
        view_box = [float(value) for value in svg.attrib["viewBox"].split()]
        self.assertEqual(len(view_box), 4)
        self.assertEqual(view_box[2], view_box[3])
        self.assertGreaterEqual(view_box[2], 48)

        for asset in (COMPOSER_ICON, LOGO):
            self.assertLessEqual(asset.stat().st_size, 5 * 1024 * 1024)

    def test_all_fixture_events_are_present_and_valid_json_objects(self) -> None:
        fixtures = ROOT / "tests" / "fixtures"
        observed = set()
        for path in fixtures.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(payload, dict)
            observed.add(payload["hook_event_name"])
        self.assertEqual(observed, EVENTS)

    def test_selective_pytest_example_uses_routed_command_evidence(self) -> None:
        package = (SELECTIVE_PYTEST / "pyproject.toml").read_text(encoding="utf-8")
        implementation = (
            SELECTIVE_PYTEST / "src" / "foreman_selective_pytest" / "__init__.py"
        ).read_text(encoding="utf-8")
        config = (SELECTIVE_PYTEST / "foreman-config.toml").read_text(encoding="utf-8")
        demo = (SELECTIVE_PYTEST / "run_demo.py").read_text(encoding="utf-8")

        self.assertIn('[project.entry-points."foreman.extensions"]', package)
        self.assertIn('selective-pytest = "foreman_selective_pytest:extension"', package)
        self.assertIn('always=False', implementation)
        self.assertEqual(implementation.count('evidence=("command.pytest",)'), 2)
        self.assertIn('[extensions."selective-pytest"]', config)
        self.assertIn('command = ["pytest", "-q"]', config)
        self.assertIn('expect_responsibility=False', demo)
        self.assertIn('expect_responsibility=True', demo)


if __name__ == "__main__":
    unittest.main()
