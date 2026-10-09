---
name: foreman-deepagents
description: Set up, diagnose, or explain Foreman supervision in Deep Agents Code (dcode). Do not reproduce Foreman's supervisory decisions manually.
---

# Foreman in Deep Agents Code

This plugin forwards seven native lifecycle events to `foreman hook --client
deepagents`. Foreman core owns responsibility routing, evidence, decisions,
completion checks, and session state.

For setup and diagnosis, follow `../../README.md`:

1. Check `foreman --version` and `dcode --version`. Require `foreman-core >= 0.5.0`
   and `deepagents-code >= 0.1.83`, installed separately.
2. Configure supervisor credentials in Foreman's protected central `.env` file.
   Never print credentials. Native hook environments may remove API key variables.
3. Use `foreman extension status` to validate the central configuration. Repository
   scope and responsibilities belong in Foreman's user configuration.
4. Inspect `dcode plugin list --json` for `foreman-deepagents@thruwire`. Start a
   fresh session after installing or enabling the plugin. Avoid duplicate Foreman
   handlers installed by `foreman deepagents setup` in user or project hooks.
5. Check that the runtime can find `foreman` on PATH. Do not run setup to repair
   plugin discovery: it installs a second set of handlers.

Describe only the responsibilities and outcomes actually reported by Foreman.
Do not infer, simulate, or replace its allow, deny, steering, or completion decisions.
