# ThruWire Marketplace

The ThruWire marketplace is the publisher-owned catalog and source repository for ThruWire agent
plugins. Keeping installable packages in the marketplace checkout lets Codex read their manifests
and assets before installation, so the Plugins Directory can render complete listings.

## Codex

Add the marketplace and install a plugin:

```bash
codex plugin marketplace add thruwire/marketplace
codex plugin add foreman@thruwire
codex plugin add thruwire@thruwire
```

The catalog entry in [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) points
to the package at [`plugins/foreman`](plugins/foreman). Keeping the complete package—including
`assets/icon.png` and `assets/logo.svg`—inside the marketplace checkout lets the Plugins Directory
render Foreman's name, description, and icon before installation. Users do not need a local clone
of either repository.

The [ThruWire plugin](plugins/thruwire) connects to the hosted factory MCP server.
It uses the installing user's ThruWire authentication and has no local server
dependency. The marketplace package is validated for local use. ChatGPT cloud
dots require a supported account-level MCP plugin connection; importing this
package alone does not provide one. See the package README for the verified
local behavior and cloud integration requirements.

Foreman itself remains a separate runtime dependency:

```bash
uv tool install 'foreman-core>=0.4.1'
```

`pipx install 'foreman-core>=0.4.1'` is also supported. Keep `TYPESAFE_API_KEY` in the user or
process environment; never place it in this repository, marketplace metadata, or hook definitions.

Use the [Foreman setup guide](plugins/foreman/SETUP.md) for every configuration step, including
the required hook review and trust. Configure first, trust the hooks last, and start a fresh
session. ThruWire installation and OAuth are documented separately in the
[ThruWire plugin guide](plugins/thruwire/README.md).

The optional [Foreman–ThruWire integration guide](docs/integrations/foreman-thruwire/README.md)
is outside both plugin packages. It keeps project-specific checks in local configuration and
requires Foreman 0.4.2 or newer from PyPI.

## Deep Agents Code

Install Foreman core and Deep Agents Code separately, then install the dcode plugin:

```bash
uv tool install 'foreman-core>=0.5.0'
uv tool install --python 3.12 'deepagents-code>=0.1.83'
dcode plugin marketplace add thruwire/marketplace
dcode plugin install foreman-deepagents@thruwire
```

Follow the [Deep Agents plugin guide](plugins/foreman-deepagents/README.md) to
configure protected central credentials, repository scope, and responsibilities
before enabling hooks and starting a fresh session. Choose this plugin or
`foreman deepagents setup` to avoid duplicate assessments.

dcode reads the separate Claude-format catalog at
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). The existing
Codex catalog and Foreman Codex package remain unchanged.

## Claude Code

The `.claude-plugin/` catalog format is also understood by dcode. The Deep Agents
package targets dcode; there is no supported Claude Code plugin here yet.

## Development

Validate the catalog with:

```bash
make check
```

With `deepagents-code >= 0.1.83` installed in the Python environment, also run
`python tests/integration/check_deepagents.py`. It installs into a disposable
profile and verifies native plugin discovery and control responses without API calls.

Add future products as additional entries rather than creating a marketplace per product. The
stable marketplace identifier is `thruwire`; `ThruWire Plugins` is its user-facing display name.
