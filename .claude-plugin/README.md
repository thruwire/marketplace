# Deep Agents marketplace catalog

Deep Agents Code (`dcode`) discovers the Claude-format catalog in this directory.
It contains `foreman-deepagents`, which uses Deep Agents lifecycle events and
`foreman hook --client deepagents`. This package targets dcode; it is not a
Claude Code integration.

The Codex catalog remains at `.agents/plugins/marketplace.json`. Keeping the
catalogs separate prevents dcode from installing the Codex-specific Foreman
adapter. There is no supported Claude Code plugin in this repository yet.
