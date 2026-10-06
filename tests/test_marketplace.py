from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CLAUDE_PLACEHOLDER = ROOT / ".claude-plugin" / "README.md"
FOREMAN_PLUGIN = ROOT / "plugins" / "foreman"


class MarketplaceTests(unittest.TestCase):
    def test_foreman_points_to_marketplace_local_package(self) -> None:
        payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "thruwire")
        self.assertEqual(payload["interface"]["displayName"], "ThruWire Plugins")
        plugin = next(entry for entry in payload["plugins"] if entry["name"] == "foreman")
        self.assertEqual(plugin["name"], "foreman")
        self.assertEqual(
            plugin["source"],
            {
                "source": "local",
                "path": "./plugins/foreman",
            },
        )
        self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")
        self.assertEqual(plugin["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(plugin["category"], "Developer Tools")

    def test_catalog_packages_are_unique_and_resolvable(self) -> None:
        payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        names = [entry["name"] for entry in payload["plugins"]]
        self.assertEqual(len(names), len(set(names)))
        for entry in payload["plugins"]:
            with self.subTest(plugin=entry["name"]):
                self.assertEqual(entry["source"]["source"], "local")
                source = entry["source"]["path"]
                self.assertTrue(source.startswith("./"))
                package = (ROOT / source).resolve()
                self.assertIn(ROOT, package.parents)
                portable_path = package / "plugin.json"
                manifest_path = (portable_path if portable_path.is_file()
                                 else package / ".codex-plugin" / "plugin.json")
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(manifest["name"], entry["name"])
                interface = (manifest["extensions"]["com.openai"]["interface"]
                             if portable_path.is_file() else manifest["interface"])
                for field in ("composerIcon", "logo"):
                    asset = (package / interface[field]).resolve()
                    self.assertIn(package, asset.parents)
                    self.assertTrue(asset.is_file())

    def test_thruwire_mcp_is_remote_and_does_not_bundle_credentials(self) -> None:
        entry = next(
            plugin for plugin in json.loads(MARKETPLACE.read_text(encoding="utf-8"))["plugins"]
            if plugin["name"] == "thruwire"
        )
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        package = ROOT / entry["source"]["path"]
        config = json.loads((package / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(config["$schema"], "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json")
        self.assertEqual(set(config["mcpServers"]), {"thruwire"})
        server = config["mcpServers"]["thruwire"]
        self.assertEqual(set(server), {"type", "url"})
        self.assertEqual(server["type"], "streamable-http")
        endpoint = urlsplit(server["url"])
        self.assertEqual((endpoint.scheme, endpoint.netloc, endpoint.path),
                         ("https", "api.thruwire.ai", "/mcp"))
        self.assertFalse(endpoint.query)
        self.assertFalse(endpoint.fragment)
        manifest = json.loads((package / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("apps", manifest["extensions"]["com.openai"])
        self.assertNotIn("hooks", manifest["extensions"]["com.openai"])

    def test_foreman_package_contains_resolvable_marketplace_artwork(self) -> None:
        manifest = json.loads((FOREMAN_PLUGIN / ".codex-plugin" / "plugin.json").read_text(
            encoding="utf-8"))
        interface = manifest["interface"]

        self.assertEqual(manifest["name"], "foreman")
        self.assertEqual(interface["displayName"], "Foreman")
        for field in ("composerIcon", "logo"):
            asset = interface[field]
            self.assertTrue(asset.startswith("./assets/"))
            self.assertTrue((FOREMAN_PLUGIN / asset).is_file())

    def test_claude_is_only_a_placeholder(self) -> None:
        self.assertTrue(CLAUDE_PLACEHOLDER.is_file())
        self.assertFalse((ROOT / ".claude-plugin" / "marketplace.json").exists())


if __name__ == "__main__":
    unittest.main()
