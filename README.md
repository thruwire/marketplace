# ThruWire Marketplace

The ThruWire marketplace is the publisher-owned catalog for ThruWire agent plugins. Plugin
implementations remain with their product repositories so their protocol adapters and compatible
runtime versions can be reviewed and released together.

## Codex

Add the marketplace and install Foreman:

```bash
codex plugin marketplace add thruwire/marketplace
codex plugin add foreman@thruwire
```

The catalog entry in [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) points
to `integrations/codex` in [`thruwire/foreman`](https://github.com/thruwire/foreman). Codex fetches
and caches that Git subdirectory; users do not need a local clone of Foreman.

Foreman itself remains a separate runtime dependency:

```bash
uv tool install 'foreman-core>=0.4.1'
```

`pipx install 'foreman-core>=0.4.1'` is also supported. Keep `TYPESAFE_API_KEY` in the user or
process environment; never place it in this repository, marketplace metadata, or hook definitions.

## Claude Code

The [`.claude-plugin/`](.claude-plugin/) directory reserves the future Claude Code marketplace
location. There is no Claude marketplace or Claude plugin in this repository yet.

## Development

Validate the catalog with:

```bash
make check
```

Add future products as additional entries rather than creating a marketplace per product. The
stable marketplace identifier is `thruwire`; `ThruWire Plugins` is its user-facing display name.
