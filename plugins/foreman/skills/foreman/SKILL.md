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
3. Require `foreman-core >= 0.4.1` and a nonempty TypeSafe API key in the runtime's supported credential location. Version 0.4.1 needs `TYPESAFE_API_KEY` in the Codex process environment; 0.4.2 and newer also support a protected central dotenv file documented in the setup guide. Never print the key.
4. Use `foreman extension status` to inspect extension state and validate the normal Foreman configuration. Foreman configuration remains under `${FOREMAN_CONFIG:-${FOREMAN_DATA_DIR:-~/.foreman}/config.toml}`.
5. Follow the ordered setup in `../../SETUP.md`: configure runtime, credentials, and local responsibilities, verify them, then review/trust the hooks in desktop Settings → Hooks or CLI `/hooks`, and start a fresh session. Plugin installation does not automatically trust hooks. If hooks were enabled during an active turn and report `arrived before work_submitted`, temporarily disable them and restart with a fresh session after configuration.
6. Generic local declarative responsibilities documented in `../../SETUP.md` require the published `foreman-core >= 0.4.2` package from PyPI. Do not install a source branch or modify Foreman code to configure them. In 0.4.2 and newer, a protected central `.env` is supported for hook credentials; the current doctor still checks the process environment. Clearly distinguish a diagnostic limitation from a working installed setup.

When explaining current supervision, describe the lifecycle boundary and any responsibility names Foreman returned. Do not infer, replace, or simulate Foreman's allow, deny, steering, evidence, or completion decisions.
