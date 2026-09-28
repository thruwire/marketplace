---
name: foreman
description: Diagnose and explain the Foreman supervisor integration for Codex, including installation, status, configuration, and attached responsibilities. Do not use this skill to reproduce Foreman's supervisory decisions manually.
---

# Foreman operations

Foreman is an agent supervisor and software factory foreman powered by TypeSafe’s Jev model. This plugin forwards Codex lifecycle events to `foreman hook --client codex`; Foreman independently owns responsibility routing, evidence collection, supervisory decisions, completion checks, and attached-session state.

For setup or diagnosis:

1. Locate this plugin's root from this `SKILL.md` and run `scripts/doctor` there.
2. If Foreman is missing, recommend one supported installation command:
   - `pipx install foreman-core`
   - `uv tool install foreman-core`
3. Require `foreman-core >= 0.4.1` and a nonempty `TYPESAFE_API_KEY` in the Codex process environment. Never print the key.
4. Use `foreman extension status` to inspect extension state and validate the normal Foreman configuration. Foreman configuration remains under `${FOREMAN_CONFIG:-${FOREMAN_DATA_DIR:-~/.foreman}/config.toml}`.
5. Use `/hooks` in Codex to check whether the installed plugin hooks have been reviewed and trusted.

When explaining current supervision, describe the lifecycle boundary and any responsibility names Foreman returned. Do not infer, replace, or simulate Foreman's allow, deny, steering, evidence, or completion decisions.
