# Set up Foreman for Codex

Configure Foreman before enabling its hooks. Foreman is installed from PyPI; this plugin forwards
Codex events to that installed command. No Foreman source checkout, patched runtime, extra hook
registration, or repository `AGENTS.md` is required.

Plugin installation registers the six hook definitions automatically. Runtime installation,
credentials, local responsibility choices, and hook trust are separate setup steps. There is
currently no `foreman setup` command that combines them.

## 1. Choose the runtime version

Basic supervision requires `foreman-core >= 0.4.1`. Central repository allowlists and locally
defined declarative responsibilities require **0.4.2 or newer**.

**Release status:** the 0.4.2 configuration capabilities are being prepared and have passed local
tests, but have not been published to PyPI yet. The advanced configuration below is a setup
recipe; do not apply it to 0.4.1 or install a source branch as a workaround. This guide must be
updated when the release is published.

## 2. Install the published package

Choose one package manager:

```bash
pipx install foreman-core
# For an existing installation:
pipx upgrade foreman-core
```

Or:

```bash
uv tool install foreman-core
# For an existing installation:
uv tool upgrade foreman-core
```

Ensure the tool's executable directory is on the `PATH` inherited by Codex. `pipx ensurepath`
can configure the shell path; restart the shell afterward. A desktop app may need restarting to
inherit a changed launch environment. Do not create a wrapper around `foreman` or add duplicate
hooks to solve a path problem.

Check the command and version:

```bash
command -v foreman
foreman --version
```

`--version` is available starting with 0.4.2. For an older release, `pipx list` or `uv tool list`
shows the installed package version. Once 0.4.2 is published, install it from PyPI before using
the remaining advanced configuration steps.

## 3. Configure the TypeSafe credential

Foreman's router and checks use a **TypeSafe API key**.

For 0.4.2 or newer, create a protected central dotenv file and enter the key with a text editor:

```bash
mkdir -p ~/.foreman
chmod 700 ~/.foreman
umask 077
touch ~/.foreman/.env
chmod 600 ~/.foreman/.env
nano ~/.foreman/.env
```

Add this variable using your own key:

```dotenv
TYPESAFE_API_KEY=YOUR_TYPESAFE_API_KEY
```

Foreman hooks load `${FOREMAN_DATA_DIR:-~/.foreman}/.env`; existing process environment values
take precedence. Keep the file local. Do not commit the key or put it in plugin manifests,
marketplace configuration, hook definitions, or responsibility prompts.

For 0.4.1, provide `TYPESAFE_API_KEY` in the process environment that starts Codex. For example,
in zsh, enter it without adding it to shell history:

```bash
read -rs 'TYPESAFE_API_KEY?TypeSafe API key: '
printf '\n'
export TYPESAFE_API_KEY
codex
```

For a desktop app on 0.4.1, use its operating-system launch environment and restart the app.
Saving the central dotenv file alone does not configure the older runtime.

## 4. Configure local responsibilities

The normal central file is:

```text
${FOREMAN_CONFIG:-${FOREMAN_DATA_DIR:-~/.foreman}/config.toml}
```

Create or edit that file locally. Preserve existing extension or evidence-provider settings.
For 0.4.2 or newer, `hooks.repositories` is the `repositories` array under
`[hooks]`, and `[hooks.responsibilities."<id>"]` configures a responsibility.

- Use absolute checkout paths in `hooks.repositories`. Omit the array to supervise every repo;
  set it to `[]` to disable attached supervision everywhere.
- Subdirectories, symlinks, and linked Git worktrees match the same repository identity.
  An unrelated clone with the same name does not match.
- Set `enabled = false` for each unwanted responsibility. Unspecified built-ins stay enabled.
- A local `kind = "declarative"` responsibility owns its routing instructions, guidance, checks,
  thresholds, and response to a failed criterion. It needs no custom extension package.
- `context` is delivered only when that responsibility matches the prompt. Its checks continue
  through the normal tool and completion lifecycle. An unrelated prompt that matches no
  responsibilities adds no checks.

For example, a generic local responsibility can require project context before development:

```toml
[hooks]
repositories = ["/absolute/path/to/project"]

[hooks.responsibilities."example.project-context"]
kind = "declarative"
always = false
routing_instructions = "Does this prompt require coding or debugging?"
routing_threshold = 0.75
context = "Read the project's current development context before coding."
failure_action = "steer"
failure_message = "Consult the current development context before proceeding."

[hooks.responsibilities."example.project-context".checks.context_consulted]
instructions = "Was the current project's development context consulted for this work?"
min_threshold = 0.80
```

This adds the local check alongside the defaults. To keep only that responsibility for attached
sessions, explicitly disable all six built-in classes:

```toml
[hooks.responsibilities."core.completion"]
enabled = false
[hooks.responsibilities."core.verification"]
enabled = false
[hooks.responsibilities."core.worker-health"]
enabled = false
[hooks.responsibilities."core.human-escalation"]
enabled = false
[hooks.responsibilities."repository.instructions"]
enabled = false
[hooks.responsibilities."quality.documentation"]
enabled = false
```

Repository paths and workflow instructions belong in the local configuration. The open-source
runtime supplies the generic implementation.

These controls apply to attached Codex sessions. Explicit `foreman run` jobs retain their
required completion and verification responsibilities.

## 5. Install the Foreman plugin

Install the Foreman plugin from the marketplace:

```bash
codex plugin marketplace add thruwire/marketplace
codex plugin add foreman@thruwire
codex plugin list --json
```

Foreman supplies responsibility guidance and assessments. Any external tools named by a local
responsibility must already be configured independently by the coding assistant.

## 6. Verify configuration before trusting hooks

```bash
foreman extension status
```

This parses the central configuration and checks configured extensions; it does not prove that
the TypeSafe key authenticates or that a project's MCP read succeeds. Run a small direct hook
probe with the installed runtime to verify routing before automatic activation:

```bash
python3 - <<'PY' | foreman hook --client codex
import json
from pathlib import Path
print(json.dumps({
    "session_id": "foreman-setup-check",
    "cwd": str(Path.cwd()),
    "hook_event_name": "UserPromptSubmit",
    "prompt": "Inspect this repository's development context without changing files."
}))
PY
```

Run this from a repository included in the allowlist. A matching responsibility should appear
in `hookSpecificOutput.additionalContext`, along with its configured guidance. Run an unrelated
prompt or a probe from an excluded repository to confirm the empty response where intended.
Clean up the probe session:

```bash
python3 - <<'PY' | foreman hook --client codex
import json
from pathlib import Path
print(json.dumps({
    "session_id": "foreman-setup-check",
    "cwd": str(Path.cwd()),
    "hook_event_name": "SessionEnd"
}))
PY
```

The bundled skill can locate and run `scripts/doctor` from the installed plugin. The current
doctor checks the **process environment** for `TYPESAFE_API_KEY`; a credential stored only in
the 0.4.2 central dotenv file can make that older diagnostic report a missing key even when the
runtime probe works. Do not print the credential or replace the runtime to satisfy the diagnostic.

## 7. Review and trust the hooks, then start a fresh session

**Installing the plugin does not automatically trust its hooks. You must review and trust them.**

In Codex's desktop app, open **Settings → Hooks**, locate the Foreman plugin entries, review
the commands, trust the definitions, and enable them. In Codex CLI, open `/hooks` and use its
review/trust controls. The six events are `SessionStart`, `UserPromptSubmit`, `PreToolUse`,
`PostToolUse`, `Stop`, and `SessionEnd`. Each calls the same plugin launcher, which invokes the
installed `foreman hook --client codex` command.

If hooks were disabled globally, turn the global hooks setting back on when you are ready to
activate them. Keep unrelated hook entries disabled if you do not intend to run them.

Review [`hooks/hooks.json`](hooks/hooks.json) and [`scripts/foreman-hook`](scripts/foreman-hook).
Trust is recorded against each current hook definition; new or changed definitions require
another review. Do not use a hook-trust bypass flag as the normal installation procedure.
These requirements come from [Codex hook trust](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks),
not a Foreman-specific approval system. Centrally managed organizations can deploy hooks trusted
by admin policy; a normal marketplace install still requires the user's review.

**Start a fresh Codex session after enabling the hooks and submit a new work prompt.** Enabling
them partway through an existing turn can cause `PreToolUse arrived before work_submitted` or
`Stop arrived before work_submitted`: Foreman has not received that turn's initial prompt.

If that happens, temporarily disable the Foreman hooks, verify the configuration, and start a
fresh session before re-enabling them. Do not add duplicate hooks or patch the installed runtime.

## 8. Confirm the intended behavior

When using the local example above, a development prompt in an allowed repository should route to
the local responsibility and
deliver its configured guidance. Only that responsibility's enabled checks should be assessed.
A completed context read should satisfy the example criterion. With the built-ins disabled,
an unrelated prompt and any work in an excluded repository should receive no intervention.

Upgrade the runtime from PyPI with `pipx upgrade foreman-core` or `uv tool upgrade foreman-core`.
Upgrade the marketplace plugin separately. Recheck configuration, review changed hook definitions,
and start a fresh session after updates. Local credentials and responsibility definitions remain
local across upgrades.
