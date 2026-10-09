from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


LAUNCHER = Path(__file__).resolve().parent.parent / "plugins/foreman-deepagents/scripts/foreman-hook"


class DeepAgentsLauncherTests(unittest.TestCase):
    def test_preserves_native_protocol_and_selects_deepagents_from_another_cwd(self) -> None:
        with tempfile.TemporaryDirectory(prefix="deep agents plugin ") as directory:
            root = Path(directory)
            bin_dir = root / "bin with spaces"
            bin_dir.mkdir()
            fake = bin_dir / "foreman"
            fake.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE_ARGS"\n'
                'cat > "$CAPTURE_INPUT"\n'
                'printf "%s\\n" \'{"decision":"block","reason":"unfinished"}\'\n'
                'printf "%s\\n" "supervisor diagnostic" >&2\nexit 2\n'
            )
            fake.chmod(0o755)
            payload = b'{"hook_event_name":"Stop","cwd":"odd directory","stop_hook_active":true}\n'
            result = subprocess.run(
                [LAUNCHER], input=payload, capture_output=True, cwd=root,
                env={**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin",
                     "CAPTURE_ARGS": str(root / "args"), "CAPTURE_INPUT": str(root / "input")},
                check=False,
            )
            self.assertEqual((root / "args").read_text(), "hook\n--client\ndeepagents\n")
            self.assertEqual((root / "input").read_bytes(), payload)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'{"decision":"block","reason":"unfinished"}\n')
            self.assertEqual(result.stderr, b"supervisor diagnostic\n")

    def test_missing_runtime_leaves_protocol_stdout_empty(self) -> None:
        result = subprocess.run([LAUNCHER], input=b"{}", capture_output=True,
                                env={"PATH": ""}, check=False)
        self.assertEqual(result.returncode, 127)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"foreman-core >= 0.5.0", result.stderr)


if __name__ == "__main__":
    unittest.main()
