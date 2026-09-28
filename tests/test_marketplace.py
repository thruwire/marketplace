from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CLAUDE_PLACEHOLDER = ROOT / ".claude-plugin" / "README.md"


class MarketplaceTests(unittest.TestCase):
    def test_foreman_points_to_product_owned_codex_package(self) -> None:
        payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "thruwire")
        self.assertEqual(payload["interface"]["displayName"], "ThruWire Plugins")
        self.assertEqual(len(payload["plugins"]), 1)

        plugin = payload["plugins"][0]
        self.assertEqual(plugin["name"], "foreman")
        self.assertEqual(
            plugin["source"],
            {
                "source": "git-subdir",
                "url": "https://github.com/thruwire/foreman.git",
                "path": "./integrations/codex",
                "ref": "main",
            },
        )
        self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")
        self.assertEqual(plugin["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(plugin["category"], "Developer Tools")

    def test_claude_is_only_a_placeholder(self) -> None:
        self.assertTrue(CLAUDE_PLACEHOLDER.is_file())
        self.assertFalse((ROOT / ".claude-plugin" / "marketplace.json").exists())


if __name__ == "__main__":
    unittest.main()
