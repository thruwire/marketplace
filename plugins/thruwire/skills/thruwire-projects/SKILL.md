---
name: thruwire-projects
description: Inspect or work with ThruWire projects through the hosted MCP connection, including the live resources required to understand artifact queries and project operations.
---

# ThruWire projects

The plugin connects to the full MCP server at `https://api.thruwire.ai/mcp`.
Live MCP resources are part of this interface; discovering tools alone is
insufficient. Use the authenticated connection for the intended account.

## Discover and read live resources

List MCP resources for the ThruWire server, following pagination. Also list
resource templates; an empty template list is valid. Read the discovered
`resource://thruwire-overview` resource for context. Before using a tool that
names a prerequisite resource, read that live resource from the same server.
In particular, read `resource://thruwire-artifact-query` before artifact queries,
and `resource://thruwire-execute-python-guide` before graph-planning scripts.
Resolve resource URIs from discovery rather than guessing alternate names.

Use native `resources/list`, `resources/templates/list`, and `resources/read`
through the host's resource APIs. Do not treat a successful tool listing or a
manifest's endpoint URL as proof that the host can read resources. If the host
only exposes tools, use a documented authenticated resource-reading capability
if one exists. Otherwise report the missing resource capability, and do not
invent resource content or perform an operation whose prerequisite is missing.
Bundled instructions do not substitute for live account-specific resources.

## Verify the requested project and preserve scope

Resolve the project name against accessible projects, then use its ID explicitly
for reads and authorized work. Do not create a replacement project because a
lookup failed. For monitoring, verify an initial project read and resource read
on the dot's actual runtime before describing monitoring as active. A local
Codex connection does not establish the dot's cloud connection.

Follow the user's authorization for authoring and reporting. A request to watch
or inspect a project is read-only: leave its blocks and artifacts unchanged.
Connect the reporting destination separately, use one monitoring responsibility,
and report meaningful changes while staying quiet when nothing has changed.
