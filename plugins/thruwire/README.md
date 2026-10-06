# ThruWire

Connect to the hosted ThruWire MCP server at `https://api.thruwire.ai/mcp`.
The package contains a portable plugin manifest, a Streamable HTTP MCP connection,
and ThruWire artwork. It runs no local server and includes no credentials,
project-specific configuration, Slack connection, hooks, or scheduled tasks.
The bundled `thruwire-projects` skill guides live resource discovery and reads.

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

An archive imported through ChatGPT's personal **Upload plugin archive** flow
currently exposes the portable `mcp.json` server as desktop-only, even for an
HTTPS endpoint. That upload alone is not a working dot connection.

For a hosted ChatGPT plugin, upload this package through the OpenAI Platform
plugin dashboard, open its **MCPs** tab, and configure and authenticate the
server within the plugin. Complete its setup and verify the installed plugin in
the dot's runtime. Users should install and connect **ThruWire**; no separate
custom MCP plugin or local server is required. Dashboard registration and
review availability are distinct from the Git marketplace package.

Give the dot the factory identity, the reporting destination, and what should
trigger a report. Connect Slack separately and add the dot to the target channel.
For read-only monitoring, instruct the dot to leave factory blocks and artifacts
unchanged and report only meaningful changes. Verify the project's initial read
and the event subscription or polling schedule before calling monitoring active.

The server also exposes authoring tools. This package does not enforce read-only
access; use host tool permissions or server-side account permissions when an
enforced restriction is required. Installing the plugin does not authorize
factory changes or outgoing messages.

## MCP resources

The connection targets the full hosted MCP endpoint, with no tools-only proxy or
allowlist. Resources must be discovered and read using the host's native
`resources/list`, `resources/templates/list`, and `resources/read` APIs. Follow
resource pagination and use returned URIs. An empty template list is valid.

`tools-server/main.py` registers 47 tools and 16 resources. The deployment
profile can hide tools. During verification, the authenticated hosted server
exposed 16 resources.
All 16 discovered resources were read successfully; no continuation cursor
was returned. The server advertised no resource templates. This verifies the server, not every installation: repeat discovery
and a read in the actual client or dot runtime. Hosts that expose only tools
need a documented resource bridge; manifest metadata cannot add host support.
The bundled skill reports that gap rather than fabricating required context.

## Package format

`plugin.json` declares the Agent Plugins manifest schema and OpenAI listing metadata.
`mcp.json` declares the portable MCP schema and the hosted Streamable HTTP endpoint.
There are no account-specific registered app IDs in the distribution, so each
installation connects using the user's own account.

References:

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Custom MCP connections](https://developers.openai.com/api/docs/guides/custom-mcp-server)
- [Dot app connections](https://learn.chatgpt.com/docs/dots/computers-and-apps)
