# Local ThruWire responsibility

This example keeps ThruWire-specific routing, guidance, and one recurring check in the user's
local Foreman configuration. Foreman's open-source runtime provides the generic declarative
responsibility implementation and contains no ThruWire-specific routing logic.

It requires `foreman-core >= 0.4.2`. That release is currently prepared but not yet published;
do not load this configuration with 0.4.1. Follow the complete [Foreman setup guide](../../../plugins/foreman/SETUP.md) for
PyPI installation, Foreman's TypeSafe credential, local configuration, verification, and hook trust.

## Separate prerequisite: the ThruWire plugin

Configure and authenticate the ThruWire plugin independently using its
[installation and OAuth guide](../../../plugins/thruwire/README.md). Codex owns that plugin connection;
Foreman does not sign in to ThruWire, store its OAuth credentials, or create its MCP connection.
Confirm that the plugin can read your real project and native resources before using this
responsibility. Foreman's TypeSafe key configures only its Jev router and assessments.

## Configure

1. Install the published compatible Foreman runtime and Foreman marketplace plugin.
2. Supply Foreman's TypeSafe key locally. The separately configured ThruWire plugin should already
   have project access through its own authentication.
3. Copy or merge [`foreman-config.toml`](foreman-config.toml) into `~/.foreman/config.toml`.
   Replace all six `/absolute/path/to/...` entries with your checkout paths, and replace
   `YOUR_PROJECT_NAME` and `YOUR_PROJECT_ID` with a real, readable ThruWire project.
4. Keep the paths and project identity local. Do not modify either plugin manifest or Foreman
   source to configure a project. No `AGENTS.md`, extra hook definitions, or custom extension
   package is needed.
5. Verify a direct hook probe from an allowed repository and a live MCP resource/project read.
6. **Review, trust, and enable the Foreman plugin's hooks in Codex**, then start a fresh session
   and submit a new prompt. Trust is not automatic after plugin installation.

The built-in completion, verification, worker-health, human-escalation, repository-instruction,
and documentation responsibilities are explicitly disabled for attached sessions. The enabled
responsibility is `thruwire.project-context`, and its only check is `project_context_consulted`.
It owns both routing and checks; disabling the built-ins does not disable this local check.

The paths restrict the existing plugin hooks to the selected Git repositories, including their
subdirectories and linked worktrees. Use `compiler-service`, the example's actual repository
spelling. Replace the sample repository set if you work in different projects.

## Expected behavior

- Development prompts in selected repositories receive the local ThruWire guidance.
- Foreman assesses only the enabled ThruWire criterion through normal lifecycle events.
- Completed current project reads satisfy the criterion; merely proposing a read does not.
- An accurately reported authentication, native-resource, or project-access blocker satisfies
  the reporting branch of the criterion, allowing independent repository work to continue.
- Unrelated prompts and excluded repositories receive no intervention.
- The workflow reads project context and leaves project blocks and artifacts unchanged.

These are semantic Jev assessments using available evidence, rather than a deterministic audit
of every MCP operation. Tool permissions and server-side permissions enforce read-only access
when an enforced restriction is needed. The responsibility's guidance alone does not revoke
the plugin's authoring tools.

To restore ordinary supervision later, re-enable the desired built-in responsibilities in the
local file. Keep their default checks and thresholds unless you deliberately configure them.
The installed PyPI package and marketplace plugin do not need replacement.
