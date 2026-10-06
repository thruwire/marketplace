# ThruWire

Connect to the hosted ThruWire MCP server at `https://api.thruwire.ai/mcp`.
The package contains a portable plugin manifest, a Streamable HTTP MCP connection,
and ThruWire artwork. It runs no local server and includes no credentials,
project-specific configuration, Slack connection, hooks, or scheduled tasks.

## Install from the ThruWire marketplace

```bash
codex plugin marketplace add thruwire/marketplace
codex plugin add thruwire@thruwire
```

Complete the host's authentication flow with your own ThruWire account. Access
depends on that account's project permissions. Never add access tokens or account
credentials to this package or the marketplace.

## Use with a cloud dot

A Codex-local MCP configuration or a Git marketplace installation does not by
itself establish a ChatGPT cloud connection. Install and authenticate this package
in the ChatGPT account used by the dot, then verify that the dot can read the
intended factory. Local and Git marketplace availability varies by surface.

For a personal cloud installation, ZIP the contents of this directory with
`plugin.json` and `mcp.json` at the archive root, open ChatGPT Plugins, and choose
**Add → Upload plugin archive**. In the tested ChatGPT web flow, this imports a
listing that offers **Open in desktop app**; it does not establish dot tool access.
To register the hosted MCP connection for a cloud dot separately, use
**Add → Create custom MCP server** with the same URL and OAuth authentication.
Verify actual tool availability after installation; package creation alone does
not establish a working cloud connection.

Give the dot the factory identity, the reporting destination, and what should
trigger a report. Connect Slack separately and add the dot to the target channel.
For read-only monitoring, instruct the dot to leave factory blocks and artifacts
unchanged and report only meaningful changes. Verify the project's initial read
and the event subscription or polling schedule before calling monitoring active.

The server also exposes authoring tools. This package does not enforce read-only
access; use host tool permissions or server-side account permissions when an
enforced restriction is required. Installing the plugin does not authorize
factory changes or outgoing messages.

## Package format

`plugin.json` declares the Agent Plugins manifest schema and OpenAI listing metadata.
`mcp.json` declares the portable MCP schema and the hosted Streamable HTTP endpoint.
There are no account-specific registered app IDs in the distribution, so each
installation connects using the user's own account.

References:

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Custom MCP connections](https://developers.openai.com/api/docs/guides/custom-mcp-server)
- [Dot app connections](https://learn.chatgpt.com/docs/dots/computers-and-apps)
