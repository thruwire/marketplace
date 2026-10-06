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

## Verified local behavior

The installed local plugin connects directly to the hosted endpoint using OAuth.
The runtime identifies the server as belonging to `thruwire@thruwire`, exposes
36 tools and 16 native resources, and successfully reads all 16 resources.
The local host resolves the official artwork on an opaque white background
with padding and the subtitle "Connect to ThruwWire projects".

Remove an older standalone `[mcp_servers.thruwire]` entry when switching to
this plugin. A standalone entry with the same server name takes precedence;
even setting that entry to `enabled = false` prevents the plugin connection
from starting. Keep the plugin enabled and use the host's authentication flow.
No separate standalone MCP connection is required.

## Use with a cloud dot

The local marketplace package and ChatGPT cloud integration are separate.
Imported plugins with `mcp.json` or `.mcp.json` are desktop-only, including
remote HTTPS endpoints. Importing this package does not establish a cloud dot
connection. See [desktop-only plugins](https://learn.chatgpt.com/docs/enterprise/plugin-management#desktop-only-plugins).

A dot can use supported plugins installed, enabled, and connected on its owner's
ChatGPT account, with that account's permissions. Local Codex OAuth alone does
not authorize the cloud connection. A private cloud plugin can target the same
hosted ThruWire endpoint without deploying another server or submitting to the
public directory. See [custom MCP plugin setup](https://developers.openai.com/api/docs/guides/custom-mcp-server#how-to-use).

Cloud registration, account OAuth, native resource access, and the dot's project
read must be verified separately. That integration and monitoring remain pending;
the local package's successful validation does not establish cloud availability.

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
was returned. The server advertised no resource templates. The local plugin also
successfully read every resource through the host's native resource API. Repeat
discovery and a read in each intended client or dot runtime. Hosts that expose only tools
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
